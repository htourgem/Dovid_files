# BTW you have jupyter notebook like this one, called convert msv log to df at upload to art

import sys, os
repo_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(repo_path + '/upload_to_art/')
# from imp import reload 
# import parse_msv_report
# reload(parse_msv_report) 
# import parse_msv_report
# st.write(parse_msv_report.__dict__)
from parse_msv_report import msv_report_lines_to_df, parse_oct_sar_place, msv_sniffers_time_ns_cursur_in_log, last_time_ns_timestamp


import pandas as pd
import numpy as np
import io
import re
import os
import streamlit as st
import base64
import plotly as py
import cufflinks
import hashlib
import io
import datetime
from time import sleep
from contextlib import redirect_stdout

# from tqdm import tqdm
# from tqdm._tqdm_notebook import tqdm_notebook as tqdm
# tqdm.pandas()

# df = pd.DataFrame(np.random.randint(0, int(1e2), (10000, 1000)))
# st.markdown(df.groupby(0).progress_apply(lambda x: x**2))
# st.write('done ')

# st.image('/nfs/iil/disks/hdk_ws/ckt/lisrael1/lior_dir//jupyter/under_construction.jpg', width=700)

# from parse_msv_report import *#msv_report_lines_to_df, parse_oct_sar_place


def get_table_download_link(df):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}" download="abc.csv">Download csv file</a>'
    return href

def usage_logger(log_path):
    usage_log_path=os.path.dirname(os.path.abspath(__file__))+'/msv_sniffers_log_to_df.log'
    usage_log=open(usage_log_path,'a')
    usage_log.write('\n'+'*'*50+'\n')
    usage_log.write(pd.datetime.now().strftime('%Y.%m.%d_%H.%M.%S\n'))
    usage_log.write(log_path)
    usage_log.close()

st.sidebar.info(f"tool last update {datetime.datetime.fromtimestamp(os.path.getmtime(os.path.abspath(__file__))).strftime('%d-%m-%Y-%H:%M:%S')}")

st.sidebar.image(repo_path + '/streamlit/msv_sniffers_log_to_df.jpg', use_column_width=True)

class Strct: pass
global_info = Strct()
st.header('msv log with sniffers to csv')
st.write('looking for lines like')
st.code('''<MSV_REPORT_HASH>{'printer':'MSV_REPORT_DATA_PATH_MONITOR','data_type':'align_output','place':'tb.top.adctop_bmod_sniffer.MSV_REPORT_HASH.unnamed$$_0.MSV_REPORT_HASH_sar_63','pos_neg_dif':'d','value':0,'time_ns':1657.955410,'read_number':9215}</MSV_REPORT_HASH>
<MSV_REPORT_HASH>{'printer':'MSV_REPORT_DATA_PATH_MONITOR','data_type':'sar_output','place':'tb.top.sar_array.sararray_ch_all_sars.q0_qrts.octet0.qrt0.sar0.isniffer.unnamed$$_0','pos_neg_dif':'d','value':18,'time_ns':1658.016350,'read_number':142}</MSV_REPORT_HASH>
<MSV_REPORT_HASH>{'printer':'MSV_REPORT_DATA_PATH_MONITOR','data_type':'th2_input','place':'tb.top.sar_array.sararray_ch_all_sars.q0_qrts.octet0.qrt0.sar0.isniffer','pos_neg_dif':'p','value':0.285646,'time_ns':1658.124070,'read_number':143}</MSV_REPORT_HASH>''')

upload_to_art_or_just_view = st.sidebar.selectbox('upload to art or just view results locally',['non','explore','upload', 'upload specific place'])
st.sidebar.info('with "upload" you can run at ART msv_data_path analysis. with "upload specific place" you can run sin/prbs/square_wave analysis')
if 'upload' == upload_to_art_or_just_view or 'upload specific place' == upload_to_art_or_just_view:
    username=st.sidebar.text_input('user name that will be in ART')
    project_name=st.sidebar.selectbox('project name', ['Falcon','BRK_GEN1','BRK_GEN2'])
    session_name=st.sidebar.text_input('session name that will be in ART. you can easily change it later at the ART', 'msv sniffers')
    additional_art_dictionary=st.sidebar.text_input('''extra art columns for example col2:2,col3:stam ''', '')
    try:
        additional_art_dictionary = eval('{"'+additional_art_dictionary.replace(',','","').replace(':','":"')+'"}')
        if additional_art_dictionary=={''}:
            additional_art_dictionary = dict()
        if type(additional_art_dictionary) is not dict:
            st.sidebar.error('extra art columns has wrong syntax. dropping it')
            additional_art_dictionary = dict()
    except:
        st.sidebar.error('extra art columns has wrong syntax. dropping it')
        additional_art_dictionary = dict()
    additional_art_dictionary['upload_type']='streamlit'
    if 'sampling_rate_ghz' not in additional_art_dictionary:
        additional_art_dictionary['sampling_rate_ghz'] = 112 if project_name=='Falcon' else 56
    
example_log ='/nfs/iil/disks/ams_regruns/dkl/users/lisrael1/msv/temp_del/slow_sim_brk2_cfir/skip_and_simplipy_games/example_log'
example_log = '/nfs/iil/disks/ams_regruns/dkl/users/dgottesm/brk_tc2_msv/prbs_msv_1/log.txt'
global_info.sim_log=st.text_area('full path to msv log', value=example_log)
usage_logger(global_info.sim_log)
# removing some shell characters to avoid running sub commands 
global_info.sim_log=re.sub('[;&:=$()%!^~`\n]','',global_info.sim_log)
global_info.sim_log=re.sub('\s+$','',global_info.sim_log)
global_info.sim_log=re.sub('^\s+','',global_info.sim_log)

global_info.last_time_ns = last_time_ns_timestamp(global_info.sim_log)
def pick_time_ns(last_time_ns):
    st.write(f'last sim time is {last_time_ns:,f}')
    max_time_ns=last_time_ns//100*100+100
    zoom_out = st.slider(f'time ns range zoom out to upload / explore (max is {last_time_ns:,f}ns): ', 0., max_time_ns, (max_time_ns*0.9, max_time_ns))
    zoom_in = st.slider('time ns range zoom in: ', zoom_out[0], zoom_out[1], (zoom_out[0], max(zoom_out[0]+1,zoom_out[1])))
    sleep(4)
    st.write(f'total time {zoom_in[1] - zoom_in[0]:.3f} [ns]')
    return zoom_in[0], zoom_in[1]
if global_info.last_time_ns is None:
    st.error('didnt find "time_ns" at the log...')
global_info.starting_time_ns, global_info.ending_time_ns = pick_time_ns(global_info.last_time_ns)

@st.cache(suppress_st_warning=True)
def last_simulation_cache(file_path, file_date, max_lines_from_tail):  # adding file hash to cache will be updated on file update
    with io.StringIO() as buf, redirect_stdout(buf):
        output=msv_report_lines_to_df(file_path, max_lines_from_tail)
        for l in buf.getvalue().split('\n'):
            st.write(l)
    return output
                
@st.cache(suppress_st_warning=True)
def hist_on_uploaded_df(uploaded_df):
    return uploaded_df.time_ns.figure(kind='hist', bins=min(200, df.shape[0]), title='events per sim time_ns', xTitle='time_ns', yTitle='#events')

@st.cache(suppress_st_warning=True)
def prints_on_df(df, file_date):
    prints=[]
    df=original_df.copy()
        
    prints+=['parsing...']
    df=df.join(parse_oct_sar_place(df.place))
    #if not df.query(f'data_type.str.contains("th_input|align_output") and parsed_lace.str.contains("\.")').empty: dgottesm
    #if not df.query(f'data_type.str.contains("th_input|align_output") and place.str.contains("\.")').empty:
    #    prints+=[' WARNING in parsing th1 th2 align path! check if "path" column is ok']
    df=df.rename(columns=dict(place='path'))
    df['place']=df.data_type+'_'+df.pos_neg_dif  # this will fix the full path place into format of sar_output_d th1_input_p align_output_d
    if 'value' in df.columns:
        df['numeric_value']=pd.to_numeric(df.value, errors='coerce')

    prints+=[f'total parsed line {df.shape[0]:,}. sampling 1000 lines from it:']
    if df.shape[0]>1000:
        prints+=[df.sample(1000)]
    else:
        prints+=[df]


    prints+=['-'*200]
    st.header('a bit of statistics on the data')
    if 'data_type' in df.columns:
        prints+=[f'unique values at data_type: {df.data_type.unique()}']
        prints+=[df.data_type.value_counts().to_frame('#counts')]
    prints+=['statistics on string columns:']
    prints+=[df.describe(include=np.object)]
    prints+=['statistics on numeric columns:']
    prints+=[df.describe()]
    return df, prints

def upload_data_to_art(username, rawdata_str, session_name, extra_dict=dict(), project_name='BRK_GEN2'):
    import sys
    sys.path.append(repo_path + '/upload_to_art/')
    from simple_art_uploader import simple_art_dict, upload_to_ogre
    
    import io
    from contextlib import redirect_stdout
    with io.StringIO() as buf, redirect_stdout(buf):
        main_dict=dict(rawdata=rawdata_str)
        main_dict.update(extra_dict)
        tmp_dct=simple_art_dict(user=username, dct=main_dict, session_name=session_name, hidden_dict={}, project_name=project_name)
        upload_to_ogre([tmp_dct])
        for l in buf.getvalue().split('\n'):
            l=re.sub('\\0.*\\033\[0m','',l)  # didnt work for me... need to fix
            l=re.sub('\n.*http','http',l)
            st.write(l)

def pick_time_to_upload(uploaded_df, starting_time_ns, ending_time_ns):
    #time_ns_range_to_upload = st.slider('time ns range to upload: ', uploaded_df.time_ns.min(), uploaded_df.time_ns.max(), (uploaded_df.time_ns.min(), uploaded_df.time_ns.max()))
    df_max_time = df.time_ns.max()
    original_df_size = uploaded_df.shape[0]
    assert original_df_size, 'df at pick_time_to_upload is empty - the function that pick relevant time got empty df'
    uploaded_df=uploaded_df.copy().query(f'{starting_time_ns}<time_ns<{ending_time_ns}')
    st.write(f'you took {100*uploaded_df.shape[0]/original_df_size:.2f}% of the data: {uploaded_df.shape[0]:,} lines out from total of  {original_df_size:,} lines')
    st.write(f'{ending_time_ns:.2f} - {starting_time_ns:.2f} = {ending_time_ns-starting_time_ns:.2f} ns out of {df_max_time:.2f} ns')
    if ending_time_ns - df_max_time > 200 or df_max_time < starting_time_ns or uploaded_df.shape[0]<100:
        st.error('you may need to clear cache! "3 lines" -> clear cache ')
    return uploaded_df


            
            
            
assert os.path.exists(global_info.sim_log), 'no such file'

file_date=os.path.getmtime(global_info.sim_log)  // (2*60)  # rounding to 2 minutes so if you read log of a running sim, you will not get refresh every second. file_hash=hashlib.md5(open(global_info.sim_log,'rb').read()).hexdigest()  # too slow
st.write('reading file and grepping relevant rows')
file_size_gb=os.path.getsize(global_info.sim_log)*1e-9
max_lines_from_tail='1M'
if file_size_gb>1:
    max_lines_from_tail='500K'
    st.write(f'file is too big (about {file_size_gb:f} GB), taking only last {max_lines_from_tail} lines')
original_df=last_simulation_cache(global_info.sim_log, file_date, max_lines_from_tail)
assert not original_df.empty ,'no data to parse from the given file'
st.write(original_df)
df, prints=prints_on_df(original_df, file_date)
st.write(f'rows at original df {original_df.shape[0]:,.0f} and at df {df.shape[0]:,.0f}')
for p in prints:
    st.write(p)

if 'explore' == upload_to_art_or_just_view:
    st.header('exploring data')
    st.write('saving file...')
    if df.memory_usage().sum()/1024**2 > 50:  # if file is bigger than 50MB we will save it to local file instead of download link
        st.write(f"file size is {df.memory_usage().sum()/1024**2:,.3f}MB and it's more than 50MB so saving to local file")
        file_path = '/nfs/iil/disks/ams_regruns/dkl/users/lisrael1/msv/temp_del/msv_log_tmp/msv_sniffers_tmp.csv'
        df.to_csv(file_path)
        st.write(file_path)
        st.write(r'\\\\isamba.iil.intel.com'+file_path.replace("/","\\"))
    else:
        st.markdown(get_table_download_link(df), unsafe_allow_html=True)

    if 'data_type' in df.columns:
        data_type=st.selectbox('select data type to plot',['none']+df.data_type.unique().tolist())
        fig=df.query(f'data_type=="{data_type}" and time_ns>1')
        fig = pick_time_to_upload(fig, global_info.starting_time_ns, global_info.ending_time_ns)
        pos_neg_dif=st.selectbox('select which side to plot',fig.pos_neg_dif.unique().tolist())
        fig=fig.query(f'pos_neg_dif=="{pos_neg_dif}"').sort_values(['parsed_place','time_ns'])
        oct_number=st.multiselect('which octet to plot',['all']+fig.oct_number.unique().tolist())
        if not 'all' in oct_number:
              fig=fig.query(f'oct_number in {oct_number}')
        fig=fig.figure(kind='scatter', x='time_ns', y='numeric_value', categories='parsed_place', xTitle='ns', yTitle='v/code', title=data_type)
        for i in range(len(fig['data'])):
            fig['data'][i]['mode']='lines'
        st.write(fig)
if 'upload' == upload_to_art_or_just_view:
    st.header('uploading data to ART')
    uploaded_df=df.copy()#.query('time_ns>0')
#             fig=hist_on_uploaded_df(uploaded_df)
#             st.write(fig)
    uploaded_df = pick_time_to_upload(uploaded_df, global_info.starting_time_ns, global_info.ending_time_ns)
    if len(username):
        submit = st.sidebar.button('upload to ART')
        if submit:
            upload_data_to_art(username = username, rawdata_str = uploaded_df.to_csv(), session_name = session_name, extra_dict = additional_art_dictionary, project_name=project_name)
if 'upload specific place' == upload_to_art_or_just_view:
    st.header('uploading part of the data to ART')
    place = st.sidebar.selectbox('place to upload', df.place.unique())
    clock_or_data = st.sidebar.selectbox('clock or data', ['clock', 'data'])
    uploaded_df = df.copy().query(f'place=="{place}"')
    uploaded_df = pick_time_to_upload(uploaded_df, global_info.starting_time_ns, global_info.ending_time_ns)
    assert not uploaded_df.empty, 'df is empty - probably no samples to {place} between {global_info.starting_time_ns}[ns] to {global_info.ending_time_ns}[ns]'
    st.write('samples from the uploaded data - (uploading just some of the columns)')
    st.write(uploaded_df.sample(200))
    if clock_or_data == 'data':
        str_to_upload = str(uploaded_df.numeric_value.values.tolist())    
    else:
        if 'th1' in place:
            str_to_upload = uploaded_df.copy().query('sar_number==-1').assign(unit_number = lambda r:r.oct_number, timestamp_ps = lambda r:r.time_ns*1e3)[['unit_number','timestamp_ps']].to_csv()
        else:
            str_to_upload = uploaded_df.copy().query('sar_number!=-1').assign(unit_number = lambda r:r.sar_number, timestamp_ps = lambda r:r.time_ns*1e3)[['unit_number','timestamp_ps']].to_csv()
    assert len(username), 'please enter username'
    submit = st.sidebar.button('upload to ART')
    if submit:
        upload_data_to_art(username = username, rawdata_str = str_to_upload, session_name = session_name, extra_dict = additional_art_dictionary, project_name=project_name)
        st.balloons()
