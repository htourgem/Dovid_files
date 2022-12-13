import streamlit as st
import pandas as pd
import numpy as np
from tqdm import tqdm
import cufflinks
import plotly as py
import sys,re

pd.set_option("display.max_columns",1000) # don’t put … instead of multi columns
pd.set_option('expand_frame_repr',False) # for not wrapping columns if you have many
pd.set_option("display.max_rows",10)
pd.set_option('display.max_colwidth',1000)
tqdm.pandas()


def fix_table(file_path):
    df=fix_table_type_2(file_path)
    df=fix_table_type_1(df)
    return df.to_dict(orient='list')

def fix_table_type_2(file_path):
    '''

    :param df: table from virtuoso
    :return: we want this table to be with columns of freq, amp and radians
    '''
    import re, io
    with open(file_path) as f:
        content = f.read()
        content = re.sub('\([^ \n]*','', content)
        content = re.sub('^\s*$','', content)
    df=pd.read_csv(io.StringIO(content), sep='\s+')
    df=df.drop(columns=df.filter(regex='xval').columns)
    df=df.rename(columns=dict(mag='amp', dB20='amp_db', phase='radians'))
    return df

def fix_table_type_1(df):
    '''

    :param df: table from virtuoso
    :return: we want this table to be with columns of freq, amp and radians
    '''
    import re
    import numpy as np
    col=df.columns.tolist()
    col[0]='freq'
    df.columns=col
    df=df.set_index('freq')
    df=df.loc[:,~df.columns.str.endswith(' X')]#.rename(columns=lambda x: x[:-2] if x[-2:]==" Y" else x)
    df.index/=1e9
    df.loc[0]=df.iloc[0]
    df=df.sort_index()
    df = df.rename(columns=lambda x: re.sub('.*_mag_.*','amp',x)).\
        rename(columns=lambda x: re.sub('.*_phase_.*','radians',x)).\
        rename(columns=lambda x: re.sub('.*_db_.*','amp_db',x))
    if not set('amp,amp_db,radians'.split(',')) <= set(df.columns.to_list()):
        print('error in fixing table')
    df.radians=df.radians.apply(np.radians)
    return df

def P2R(A, angle):  # from amp and radians to complex number
    return A * np.exp(1j*angle)  # or A * (np.cos(angle) + np.sin(angle)*1j)

def R2P(x):  # from comples to amp and radians
    return np.abs(x), np.angle(x)

def transfer_function_to_fft(fft_abs, fft_angle, even_number_of_output_bins=True):
    '''
        if you have transfer function - meaning amp and angle (radians) per frequency .
        and you want to recover the original fft, you can use this function.
        this function is mirroring the amp and angle, then converting amp and angle to complex shape.
        the mirrored angle might be slightly different than the original angle, but it will result in no error,
        probably because the amp of this frequency is close to 0.
        even_number_of_output_bins True for having nyquist value, and False if you don’t want. also good to use when you want to set fixed number of samples at the fft, so you can do convolution with your data
    '''
    fft_angle=fft_angle%(2*np.pi)
    expand_angle=2*np.pi-fft_angle[1:-1 if even_number_of_output_bins else None][::-1]
    expand_abs=fft_abs[1:-1 if even_number_of_output_bins else None][::-1]
    fft_abs=np.hstack([fft_abs,expand_abs])
    fft_angle=np.hstack([fft_angle,expand_angle])
    full_complex_fft=P2R(fft_abs, fft_angle)
    return fft_abs, fft_angle, full_complex_fft

def interpolate(df, index): # index is a list of indexes that are not at df.index and you want to interpolate. return new and old indexes
    index=pd.DataFrame(index=index).drop(index=df.index, errors='ignore')
    new=pd.concat([df,index],axis=0,sort=True).sort_index()  # note that this can work only on monotonic up/down signal
    # now we have index, and some values with Nan…
    new=new.interpolate(method='pchip')  # another example method='polynomial', order=3
    # methods can be 'linear', 'time', 'index', 'values', 'nearest', 'zero', 'slinear', 'quadratic', 'cubic', 'barycentric', 'polynomial', 'krogh', 'piecewise_polynomial', 'pchip', 'akima', 'spline', 'from_derivatives'
    return new #.loc[index]

def convert_transfer_function_to_interpolated_full_fft(tf_freq, tf_amp, tf_angle, sampling_freq, samples_at_data):
    '''
        you have input data and system, and you want to get the system output, so you do convolution between the input and system.
        for the system you have transfer function , that have amp and angle per frequency, but might not be at even spaces and not the frequencies that you want.
        for example, you have tf from 0Hz to 10GHz, and you data has samples every 1ns, so max frequency that you need is 0.5GHz.
        if you want to multiply your signal with the tf, you need both to be at the same sampling rate, and number of samples,
        for example, if you do convolution, you need 2 vectors at the same size and same time space between samples.
        so you enter the sampling frequency and number of samples, and this function will interpolate the tf to the relevant fft values
        but the frequencies at the tf should be more than the sampled frequency otherwise you cannot interpolate the interesting frequencies.
    :param tf_freq: the frequencies of the tf. doesnt have to be at even space. doing interpolation to evaluate the desired value
    :param tf_amp: vector of all amps from 0Hz to some high frequency, more than the data nyquist
    :param tf_angle: vector of radians
    :param sampling_freq: we wnat to transfer the tf to the data frequency, so your sample frequency
    :param samples_at_data: number of samples at your data
    :return: you can do np.fft.ifft(full_complex_fft*np.fft.fft(input_samples)).real to get the system output from your input_samples
    '''
    interesting_inx=np.linspace(0, sampling_freq/2, samples_at_data//2+1)
    system=pd.DataFrame(index=tf_freq)
    system['amp']=tf_amp
    system['angle']=tf_angle
    if system.std().max()<1e-7:
        print('error - input data is constant')
    if system.isna().sum().sum():
        print('error - got nan in amp/angle')
    system=interpolate(system, interesting_inx)
    if system.isna().sum().sum():
        print('error - could not do interpolation')
    if system.loc[interesting_inx].std().max()<1e-7:
        print('error - interpolated data is constant')
    full_complex_fft = transfer_function_to_fft(system.loc[interesting_inx].amp.values,
                                                system.loc[interesting_inx].angle.values,
                                                even_number_of_output_bins=(samples_at_data%2)==0)[-1]
    return dict(full_complex_fft=full_complex_fft, all_system=system, system_at_interesting_frequencies=system.loc[interesting_inx])

tf_files=dict()
for place in 'stage_1,stage_2,stage_3,prebuf'.split(','):
    tf_files[place]=dict()
    for type_to_type in 'd2d,d2c,c2d,c2c,p2d,p2c'.split(','):
        tf_files[place][type_to_type]=st.sidebar.file_uploader(f'{type_to_type} at {place}', type=['csv'])
log=tf_files['stage_1']['d2d']
system=fix_table(log)
# display(system)
# system.drop(columns='complex_shape').figure()
out=convert_transfer_function_to_interpolated_full_fft(tf_freq=system.index.values,
                                                       tf_amp=system.amp.values,
                                                       tf_angle=system.radians.values,
                                                       sampling_freq=1/56, samples_at_data=10000)
fig=out['all_system'].figure()

system_fft_complex=out['full_complex_fft']
# data['signal_after_system'] = np.fft.ifft(data.system_fft.values*np.fft.fft(data.input.values)).real
fig=out['all_system'].figure()
st.write(fig)
