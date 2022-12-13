from glob import glob
import pandas as pd
from tqdm import tqdm
import numpy as np
import streamlit as st
pd.set_option("display.max_columns",1000) # don’t put … instead of multi columns
pd.set_option('expand_frame_repr',False) # for not wrapping columns if you have many
pd.set_option("display.max_rows",10)
pd.set_option('display.max_colwidth',100)
tqdm.pandas()

import cufflinks
import plotly as py
import plotly.express as px

def hash_file(file):
    import hashlib
    hasher = hashlib.md5()
    with open(file, 'rb') as afile:
        buf = afile.read()
        hasher.update(buf)
    return hasher.hexdigest()

def fix_table(file_path):
    df=fix_table_type_2(file_path)
    df=fix_table_type_1(df)
    df.original_freq/=1e9
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
    sep=',' if ',' in content else '\s+'
    df=pd.read_csv(io.StringIO(content), sep=sep)
    df=df.drop(columns=df.filter(regex='xval').columns)
    df=df.rename(columns=dict(mag='original_amp', dB20='original_amp_db', phase='original_radians', freq='original_freq'))
    return df


def fix_table_type_1(df):
    '''

    :param df: table from virtuoso
    :return: we want this table to be with columns of freq, amp and radians
    '''
    import re
    import numpy as np
    col=df.columns.tolist()
    col[0]='original_freq'
    df.columns=col
    df=df.set_index('original_freq')
    df=df.loc[:,~df.columns.str.endswith(' X')]#.rename(columns=lambda x: x[:-2] if x[-2:]==" Y" else x)
    df.loc[0]=df.iloc[0]
    df=df.sort_index()
    df = df.rename(columns=lambda x: re.sub('.*_mag_.*','original_amp',x)).\
        rename(columns=lambda x: re.sub('.*_phase_.*','original_radians',x)).\
        rename(columns=lambda x: re.sub('.*_db_.*','original_amp_db',x))
    if not set('original_amp,original_amp_db,original_radians'.split(',')) <= set(df.columns.to_list()):
        print('error in fixing table')
    df.original_radians=df.original_radians.apply(np.radians)
    df=df.reset_index()
    return df


def _P2R(A, angle):  # from amp and radians to complex number
    import numpy as np
    return A * np.exp(1j*angle)  # or A * (np.cos(angle) + np.sin(angle)*1j)


def _R2P(x):  # from complex to amp and radians
    import numpy as np
    return dict(amp=np.abs(x), radians=np.angle(x)%(2*np.pi))


def transfer_function_to_fft(fft_abs, fft_angle, even_number_of_output_bins=True):
    '''
        if you have transfer function - meaning amp and angle (radians) per frequency .
        and you want to recover the original fft, you can use this function.
        this function is mirroring the amp and angle, then converting amp and angle to complex shape.
        the mirrored angle might be slightly different than the original angle, but it will result in no error,
        probably because the amp of this frequency is close to 0.
        even_number_of_output_bins True for having nyquist value, and False if you don’t want. also good to use when you want to set fixed number of samples at the fft, so you can do convolution with your data
    '''
    import numpy as np
    import pandas as pd
    fft_angle=fft_angle%(2*np.pi)
    expand_angle=2*np.pi-fft_angle[1:-1 if even_number_of_output_bins else None][::-1]
    expand_abs=fft_abs[1:-1 if even_number_of_output_bins else None][::-1]
    fft_abs=np.hstack([expand_abs, fft_abs])
    fft_angle=np.hstack([expand_angle, fft_angle])
    full_complex_fft=_P2R(fft_abs, fft_angle)
    return fft_abs, fft_angle, full_complex_fft


def _interpolate(df, index): # index is a list of indexes that are not at df.index and you want to interpolate. return new and old indexes
    index=pd.DataFrame(index=index).drop(index=df.index, errors='ignore')
    new=pd.concat([df,index],axis=0,sort=True).sort_index()  # note that this can work only on monotonic up/down signal
    # now we have index, and some values with Nan…
    new=new.interpolate(method='pchip')  # another example method='polynomial', order=3
    # methods can be 'linear', 'time', 'index', 'values', 'nearest', 'zero', 'slinear', 'quadratic', 'cubic', 'barycentric', 'polynomial', 'krogh', 'piecewise_polynomial', 'pchip', 'akima', 'spline', 'from_derivatives'
    # checking if we have enough data to do the interpolation
    new['origin'] = 'original'
    new.loc[index.index, 'origin'] = 'interpolated'
    new['value_change'] = (new.origin != new.origin.shift(1).fillna(method='bfill')).cumsum()
    value_change = 0 if new.value_change.max()<2 else new.query('origin=="interpolated"').value_change.max()/new.query('value_change.min()<value_change<value_change.max()').shape[0]
    if value_change<0.3:  # from 0 to 1, where 1 is 1:1
        print('warning - interpolation is basing on too few samples. maybe the indexes are not inside the given data')
    return new.drop(columns=['origin','value_change']) #.loc[index]


def convert_transfer_function_to_interpolated_full_fft(tf_freq, tf_amp, tf_angle, interesting_frequencies):
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
    import numpy as np
    import pandas as pd
    interesting_inx=interesting_frequencies
    system=pd.DataFrame(index=tf_freq)
    system['amp']=tf_amp
    system['angle']=tf_angle
    if system.std().max()<1e-7:
        print('error - input data is constant')
    if system.isna().sum().sum():
        print('error - got nan in amp/angle')
    system=_interpolate(system, interesting_frequencies)
    if system.isna().sum().sum():
        print('error - could not do interpolation')
    if system.loc[interesting_inx].std().max()<1e-7:
        print('error - interpolated data is constant')
    full_complex_fft = transfer_function_to_fft(system.loc[interesting_frequencies].amp.values,
                                                system.loc[interesting_frequencies].angle.values,
                                                even_number_of_output_bins=(len(interesting_frequencies)%2)==0)[-1]
    return dict(full_complex_fft=full_complex_fft, all_system=system, system_at_interesting_frequencies=system.loc[interesting_frequencies])


def place_matrix_into_types(mat):
    # to validate it run:
    # place_matrix_into_types(df.query('place=="st3" and corner=="affs_hot_lc_hv"').pipe(all_types_into_big_matrix))['c2c']-df.query('place=="st3" and corner=="affs_hot_lc_hv" and type=="c2c"').complex_fft.iloc[0]
    number_of_samples = mat.shape[0]//3
    res=dict()
    res['d2d'], _, _, res['c2d'], res['c2c'], _, res['p2d'], res['p2c'], _ = split_matrix(np.asarray(mat), number_of_samples, number_of_samples)
    res={k:np.diag(v) for k,v in res.items()}
    return res


# def plot_tf(complex_fft, max_freq):
#     if len(complex_fft.shape)>1:
#         complex_fft = np.diag(complex_fft)
#     df=pd.DataFrame()
#     df['amp'], df['radians'] =_R2P(complex_fft)
#     df=df.iloc[df.shape[0]//2+1:]
#     df.index=np.linspace(0, max_freq, df.shape[0], endpoint=True)
#     fig=df.figure(subplots=True)
#     st.write(fig)
    
    
def plot_all_tf_from_matrix(complex_matrix, freq_list):
    import plotly.express as px
    all_places = place_matrix_into_types(complex_matrix)
    df=pd.DataFrame()
    for key, val in all_places.items():
        tmp=pd.DataFrame(_R2P(val))
        tmp['db']=20*np.log10(tmp.amp)
        tmp=tmp.iloc[-len(interesting_frequencies):]
        tmp['freq_GHz']=freq_list#np.linspace(0, max_freq, tmp.shape[0], endpoint=True)
#         tmp=tmp.melt(id_vars='freq', value_vars=['amp','radians'], var_name='amp_phase_type', value_name='amp_phase_content')
        tmp['place']=key
        df=df.append(tmp)
#     fig = px.line(df, x="freq", y="amp_phase_content", facet_row="amp_phase_type", color="place", height=1000)
#     fig = px.line(df.query('amp_phase_type=="amp"'), x="freq", y="amp_phase_content", color="place", height=400)
    fig = px.line(df, x="freq_GHz", y="db", color="place").update_traces(mode='lines+markers')
    st.write(fig)
    st.write(df)
    return df


def all_types_into_big_matrix(df):
    r=df.set_index('type').relevant_complex_fft_diag
    if r.empty:
        st.error('error - df is empty at all_types_into_big_matrix. df:')
        st.write(df)
    return np.mat(np.block([[r.d2d, np.zeros(r.d2d.shape), np.zeros(r.d2d.shape)],[r.c2d, r.c2c, np.zeros(r.d2d.shape)],[r.p2d, r.p2c, np.eye(r.d2d.shape[0])]]))


def split_matrix(array, nrows, ncols):
    """
        Split a matrix into sub-matrices.
        for example nrows=3, ncols=3 from 9X9 will give you 9 matrices of 3X3        
    """

    r, h = array.shape
    return (array.reshape(h//nrows, nrows, -1, ncols)
                 .swapaxes(1, 2)
                 .reshape(-1, nrows, ncols))


st.header('noise characterization')

sampling_rate=st.sidebar.slider('sampling rate GHz', 56, 560, 220, 1) # 220
number_of_samples=st.sidebar.slider('number of samples', 20, 1000, 100, 1) # 100
interesting_frequencies=np.linspace(0, sampling_rate/2, number_of_samples//2+1, endpoint=True).tolist()
del number_of_samples

relevant_files=glob(r'/nfs/iil/disks/ams_regruns/dkl/users/lisrael1/msv/temp_del/tf_functions_for_gadi/from_*/*.csv')
st.write('reading files from /nfs/iil/disks/ams_regruns/dkl/users/lisrael1/msv/temp_del/tf_functions_for_gadi')
df=pd.DataFrame(relevant_files, columns=['file_name'])

# extract key value from file_name. format is key1%value1__key2%value2.csv
tmp=df.file_name.str.replace('\\','/').str.rsplit('/',1).str[-1].str.extractall('(?P<key>[^%]*)%(?P<val>.*?)(__|.csv)').reset_index('match')
df=tmp.join(df)
# reshape table so key will be column name and value will be the content of that . so you want table with key1 key2 filename
df=df.pivot_table(index='file_name', columns='key', values='val', aggfunc='last').reset_index()
df['file_hash'] = df.file_name.apply(hash_file)

relevant_places='input_network,st1,st2,st3,prebuf'.split(',')  # has to be at the design order
st.write(f'parsing only {relevant_places}')
df=df.query('place in @relevant_places')
# finding missing data
missing_places=df.groupby(['corner']).apply(lambda g:g.place.unique()).rename('places').reset_index()
missing_places['missing_places']=missing_places.places.apply(lambda t: set(relevant_places)-set(t))
missing_places['how_much_are_missing_places']=missing_places.missing_places.apply(len)
if not missing_places.query('how_much_are_missing_places!=0').empty:
    st.error('error - some corners are missing places! removing them from view lists')
    st.write(f'dropping the next corners: {missing_places.query("how_much_are_missing_places!=0").corner.unique().tolist()}')
    st.write(missing_places)

             
             

# looking for missing values
missings=df.groupby(['place','corner']).apply(lambda g:g.type.unique()).rename('types').reset_index()
missings['missing_types']=missings.types.apply(lambda t: set('c2c,c2d,d2d,p2c,p2d'.split(','))-set(t))
missings['how_much_are_missing_types']=missings.missing_types.apply(len)
if not missings.query('how_much_are_missing_types!=0').empty:
    st.error('error - some corners are missing types! removing them from view lists')
    st.write(f'dropping the next corners: {missings.query("how_much_are_missing_types!=0").corner.unique().tolist()}')
    st.write(missings)
corners_to_remove = missing_places.query("how_much_are_missing_places!=0").corner.unique().tolist() + missings.query("how_much_are_missing_types!=0").corner.unique().tolist()
df=df.query(f'corner not in {corners_to_remove}')
assert not df.empty, 'table is empty, no data to parse'
     
             
             
             
corner = st.sidebar.selectbox('select corner', df.corner.unique().tolist())
df=df.join(df.file_name.progress_apply(fix_table).apply(pd.Series))


st.info('interpolating relevant values, and converting to fft')
st.write(df)
@st.cache(allow_output_mutation=True, hash_funcs={complex: abs})
def wrapping_fft_functions_for_cache(df, interesting_frequencies):
    df['relevant_complex_fft']=df.progress_apply(lambda r: convert_transfer_function_to_interpolated_full_fft(tf_freq=r.original_freq, tf_amp=r.original_amp, tf_angle=r.original_radians, interesting_frequencies=interesting_frequencies)['full_complex_fft'], axis=1)
    freq=np.zeros(len(df.relevant_complex_fft.iloc[0]))
    freq[-len(interesting_frequencies):]=interesting_frequencies
    df['relevant_freq']=[freq]*df.shape[0]
    df=df.join(df.relevant_complex_fft.progress_apply(_R2P).apply(pd.Series).rename(columns=dict(amp='relevant_amp', radians='relevant_radians')))
    df['relevant_amp_db']=df.relevant_amp.apply(lambda x:20*np.log10(x))
    df['relevant_complex_fft_diag']=df.relevant_complex_fft.apply(np.diag)
#     if 0:  # debug - running convert_transfer_function_to_interpolated_full_fft only on one of the files
#         r=df.iloc[0]
#         convert_transfer_function_to_interpolated_full_fft(tf_freq=r.original_freq, tf_amp=r.original_amp, tf_angle=r.original_radians, sampling_freq=sampling_rate, samples_at_data=number_of_samples)['full_complex_fft'].tolist()
    return df
             
df=wrapping_fft_functions_for_cache(df, interesting_frequencies)


places = st.sidebar.multiselect(label='pick places to do the mutiplication', options=df.query('corner==@corner').place.unique().tolist(), default=df.query('corner==@corner').place.unique().tolist())
df=df.query(f'place in {places} and corner==@corner')             
st.subheader('final table')
st.write(df)
             
# doing multiplication
# sorting places by the design order
places.sort(key = lambda i: relevant_places.index(i))  
all_places=[df.query(f'place=="{place}" and corner==@corner').pipe(all_types_into_big_matrix) for place in places]
if not len(places):
    st.sidebar.error('choose at lease one place at the left sidebar')
    assert len(places), 'choose at lease one place at the left sidebar'

multiply_output = np.linalg.multi_dot(all_places) if len(places)!=1 else all_places[0]
st.subheader('after matrices multiplication:')
plot_all_tf_from_matrix(multiply_output, interesting_frequencies)
             
if len(places)==1:
    st.subheader('you choosed only 1 place, so showing original data without the interpolation:')
    tmp=pd.DataFrame()
    for index, row in df.iterrows():
        tmp2=pd.DataFrame()
        tmp2['freq_GHz']=row.original_freq
        tmp2['db']=row.original_amp_db
        tmp2['source']=f'original {row.type}'
        tmp2['type']=row.type
        tmp=tmp.append(tmp2)
        tmp2=pd.DataFrame()
        tmp2['freq_GHz']=interesting_frequencies
        tmp2['db']=row.relevant_amp_db[-len(interesting_frequencies):]
        tmp2['source']=f'interpolates {row.type}'
        tmp2['type']=row.type
        tmp=tmp.append(tmp2)
    st.write(tmp)
#     st.write(tmp.set_index('freq_GHz').figure(xTitle='freq_GHz', yTitle='db', title=f'original {places[0]} data', mode='lines+markers', size=3))
    fig = px.scatter(tmp.sort_values(['source','freq_GHz']), x="freq_GHz", y="db", color="source").update_traces(mode='lines+markers')
    st.write(fig)

# tf_type = st.sidebar.radio('select which output you want to see', ['d2d','c2d','c2c','p2d','p2c'])
# plot_tf(place_matrix_into_types(multiply_output)[tf_type], sampling_rate//2)
# plot_tf(df.query('place=="st3" and corner=="affs_hot_lc_hv" and type=="d2d"').complex_fft.iloc[0], np.linspace(0, sampling_rate//2, 100))
# df.query('place=="st3" and corner=="affs_hot_lc_hv" and type=="c2c"').complex_fft.apply(np.abs).iloc[0]
# df.query('place=="st3" and corner=="affs_hot_lc_hv" and type=="c2c"').complex_fft.iloc[0]
# df.query('place=="st3" and corner=="affs_hot_lc_hv" and type=="d2d"').amp.iloc[0]