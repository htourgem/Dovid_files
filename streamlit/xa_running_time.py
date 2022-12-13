# TODO - when i had few simulations runing it was loading the page in loop... i reduce the reading of the log from 3 places to 1 and maybe it solved the issue. i comment our the @st.cache, you can try returning it if you still have the issue
import pandas as pd
import numpy as np
import streamlit as st
import plotly as py
import cufflinks
from glob import glob
import os
import re
import subprocess
from time import sleep
import plotly.express as px
st.set_page_config(layout="wide")

pd.options.display.max_rows=200
usage_log_path=os.path.dirname(os.path.abspath(__file__))+'/xa_running_time.log'

class timer:
    def __init__(self):
        import time
        self.time=time
        self.start = time.time()  # you can also use time.perf_counter() instead, might be more accurate. return float seconds
    def current(self):
        return f"{self.time.time() - self.start:.2f} sec"

t=timer()

class tqdm:
    def __init__(self, iterable, title=None):
        if title:
            st.subheader(title)
        self.current_itteration = st.empty()
        self.prog_bar = st.progress(0)
        self.iterable = iterable
        self.length = len(iterable)
        self.i = 0

    def __iter__(self):
        for obj in self.iterable:
            display_text = str(obj)
            display_text = display_text[-80:] if len(display_text)>80 else display_text
            self.current_itteration.text(f'{display_text}')
            yield obj
            self.i += 1
            current_prog = self.i / self.length
            self.prog_bar.progress(current_prog)

#@st.cache(suppress_st_warning=True)
def read_file(file_path, file_date):
    return open(file_path,'r').read()

def get_table_download_link(df):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    import base64
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}" download="abc.csv">Download csv file</a>'
    return href

def dhms_to_sec(dhms_str, factor=1):
    '''supporting also format of d:h:m:s, h:m:s, m:s and s'''
    if type(dhms_str)!=str:
        return dhms_str
    _,d,h,m,s = (':0'*10+dhms_str).rsplit(':',4)
    return (int(d)*24*60*60+int(h)*60*60+int(m)*60+int(s))/factor

#@st.cache(suppress_st_warning=True)
def xa_compilation_time(log):
    ptrn='cpu=(?P<cpu_minutes>[0-9.:]+)/wall=(?P<wall_minutes>[0-9.:]+)/(?P<ram_MB>\d+)MB'
#     sr=pd.Series(open(log).read().split('\n'))
    sr=pd.Series(log)
    sr=sr[sr.str.startswith('cpu=')]
    res=dict()
    for pattern in [['parsing_netlist','Setting up netlist databas'],['optimization','Fast-spice optimization']]:
        df=sr.copy()[sr.str.contains(pattern[1])].str.extract(ptrn, expand=True).dropna()
        if df.empty: continue
        a=df.drop(columns=['ram_MB']).applymap(lambda c:dhms_to_sec(c, 60)).agg(np.ptp)
        a['ram_GB']=df['ram_MB'].astype(int).agg(np.max)/1000
#         df=df.applymap(lambda c:dhms_to_sec(c, 60))
#         a=df.agg(np.ptp)
        a.index=pattern[0]+'_'+a.index
        res.update(a.to_dict())
    return res

#@st.cache(suppress_st_warning=True)
def per_log(log):
    ptrn='cpu=(?P<cpu_hours>[0-9.:]+)/wall=(?P<wall_hours>[0-9.:]+)/(?P<ram_MB>\d+)MB.*t=(?P<sim_time_ns>\d+)ns'
#     sr=pd.Series(open(log).read().split('\n'))
    sr=pd.Series(log)
    sr=sr[sr.str.startswith('cpu=')]
    df=sr.str.extract(ptrn, expand=True).dropna()#.mem.apply(float).plot()  
    if df.empty: return False
    df.cpu_hours=df.cpu_hours.apply(dhms_to_sec)/3600
    df.wall_hours=df.wall_hours.apply(dhms_to_sec)/3600
    df['ram_GB']=df.ram_MB.apply(float)*1e-3
    df=df.drop('ram_MB', axis=1)
    df.sim_time_ns=df.sim_time_ns.apply(int)
    #df['ns_per_wall_h']=(df.sim_time_ns-df.sim_time_ns.shift(-1))/(df.wall_hours-df.wall_hours.shift(-1))
    #df['last_cpu_hour_ns_per_hour']=df.query(f'cpu_hours>{df.cpu_hours.values[-1]-1}').ns_per_wall_h.mean()
    df['ns_per_last_wall_h']=df.query(f'wall_hours>{df.wall_hours.values[-1]-1}').eval('(sim_time_ns.iloc[-1]-sim_time_ns.iloc[0])/(wall_hours.iloc[-1]-wall_hours.iloc[0])')
    df['ns_per_last_cpu_h']=df.query(f'cpu_hours>{df.cpu_hours.values[-1]-1}').eval('(sim_time_ns.iloc[-1]-sim_time_ns.iloc[0])/(cpu_hours.iloc[-1]-cpu_hours.iloc[0])')
    df['ns_per_day']=df.ns_per_last_cpu_h*8*24  # 8 cpus in average
    return df

#@st.cache(suppress_st_warning=True)
def number_of_nodes(file_content):
    return pd.Series(file_content).str.extract(r'\|\s*TOTAL\s*\|\s*\|\s*(?P<nodes_in_M>\d+)\s*\|\s*\d+\s*\|').dropna().astype(int)

def bar_by_column(df):
    columns = st.multiselect('select columns to plot:', df.columns, default=None)
    if len(columns):
        st.write(df[columns].figure(kind='bar'))
# reading the line cpu=3:20:10/wall=3:26:43/3549MB t=5759ns. Estimated: unknown(s) remaining

st.header('checking xa|msv running time')
folders_or_logs=st.text_area('write full path to msv log or to folder where you have msv logs', value='examples /nfs/iil/disks/ams_regruns/dkl/users/lisrael1/msv/temp_del/slow_sim_brk2_cfir/skip_and_simplipy_games/sim_level_5/easygui_output.log1\n/nfs/iil/disks/ams_regruns/dkl/users/lisrael1/msv/temp_del/slow_sim_brk2_cfir/skip_and_simplipy_games/1*')
st.write('you can put multiple folders and logs seperated by space, comma, new line or tab. you can use *')
# st.write('the script will look for \*output.log and \*dve_gui.log files')

# st.write('the script will look for \*.log files only!')
log_name = st.sidebar.text_input('the name of the log file to look for. you can use reges', value = '.*\.log')
log_name=log_name.replace('"','').replace("'",'')
st.sidebar.image('/nfs/iil/disks/hip_ana_sim_01/dgottesm/analysis_and_tools/jupyter_notebooks/streamlit/xa_running_time.jpg', use_column_width=True)




if len(folders_or_logs):
    # list_of_all_files=[f for sub in [glob(folder+'/**', recursive=True) for folder in folders_or_logs.split(',')] for f in sub if 'output.log' in f or 'dve_gui.log' in f]
    folders_or_logs=re.sub('[\n\t,]',' ',folders_or_logs)
    
    # searching log:
    usage_log=open(usage_log_path,'a')
    usage_log.write('\n'+'*'*50+'\n')
    usage_log.write(pd.datetime.now().strftime('%Y.%m.%d_%H.%M.%S\n'))
    usage_log.write(folders_or_logs)
    
    # removing some shell characters to avoid running sub commands 
    folders_or_logs=re.sub('[;&:=$()%!^~`]','',folders_or_logs)

#     cmd=r'find %s -iregex "[^\.]*\(.*output\.log\|dve_gui\.log\).*" -exec grep -q -m 1 "^cpu=" {} \; -print'%folders_or_logs
#     cmd=r'find %s -iregex ".*\.log\(##\)?" -exec grep -q -m 1 "^cpu=" {} \; -print'%folders_or_logs
    cmd=f'find {folders_or_logs} -iregex ".*/{log_name}" -exec grep -q -m 1 "^cpu=" {{}} \; -print'
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    timer_widget = st.empty()
    t = timer()
    while process.poll() is None:
        sleep(0.1)
        timer_widget.info(f'time to find relevant files {t.current()}')
    list_of_all_files=set(process.stdout.read().decode('utf8').split('\n')[:-1])
    st.write(f'found {len(list_of_all_files)} files')

    usage_log.write(f'\nfound {len(list_of_all_files)} files\n')
    usage_log.close()
else:
    list_of_all_files=[]

if not len(list_of_all_files):
    if len(folders_or_logs):
        st.code(cmd)
    st.error('no input found')
    st.stop()
df=pd.DataFrame()


for log in tqdm(list_of_all_files, 'parsing logs:'):
    file_content=read_file(log, os.path.getmtime(log) // (3*60))  # refreshing cache only every 3 minutes
    if '\ncpu=' not in file_content:
        continue
    res=dict()
    res['log_name']="-".join(log.replace('/DVEfiles','').rsplit('/',3)[-2:-1])  # you can replace -2 with -3
    file_content = file_content.split('\n')
    tmp=number_of_nodes(file_content)
    if tmp.empty:
        continue
    res['nodes_in_M']=tmp.nodes_in_M.values[0].astype(int)/1e6
#         res['nodes_in_M']=f'nodes {int(res["nodes_in_M"]//1e3):,}k'
    res['full_path']=log
    res.update(xa_compilation_time(file_content))
    # res['directory_size_GB']
    tmp=per_log(file_content)
    if type(tmp)==pd.DataFrame:
        df=df.append(tmp.assign(**res))
if df.empty:
    st.info('seems like those log files are not relevant, so no data to process')
    st.stop()

df['progress_in_ns_per_day']=24*8*((df.sim_time_ns-df.sim_time_ns.shift(1))/(df.cpu_hours-df.cpu_hours.shift(1))).fillna(0).\
rolling(10, win_type='hamming').mean()

with st.beta_expander('sim ns per wall hours'):
    st.write(px.line(df, x='wall_hours', y='sim_time_ns', color='log_name', height=500, width=1200))
with st.beta_expander('sim ns per cpu hours'):
    st.write(px.line(df, x='cpu_hours', y='sim_time_ns', color='log_name', height=500, width=1200))
with st.beta_expander('local progress if you had 8 cpus'):
    st.write(px.line(df, x='sim_time_ns', y='progress_in_ns_per_day', color='log_name', width=1200))
with st.beta_expander('full df'):
    st.write(df)

    
    
    
    
with st.beta_expander('statistics per sim'):
    data_per_sim=df.groupby('log_name').last()
    #         data_per_sim.nodes_in_M=data_per_sim.nodes_in_M.str.replace('nodes ','', regex=True)
    extra_data_per_sim=dict()
    extra_data_per_sim['average_ram_GB']=df.groupby('log_name').ram_GB.mean()
    extra_data_per_sim['peak_ram_GB']=df.groupby('log_name').ram_GB.max()
    #extra_data_per_sim['last_cpu_hour_ns_per_hour']=df.groupby('log_name').last_cpu_hour_ns_per_hour.last()    
    #extra_data_per_sim['avarage_ns_per_cpu_hour']=data_per_sim.sim_time_ns/data_per_sim.cpu_hours
    extra_data_per_sim['number_of_cpus']=data_per_sim.cpu_hours/data_per_sim.wall_hours
    #data_per_sim=data_per_sim.assign(**extra_data_per_sim).drop(['ns_per_wall_h','ram_GB'], axis=1)
    data_per_sim=data_per_sim.assign(**extra_data_per_sim).drop(['ram_GB'], axis=1)
    bar_by_column(data_per_sim)
    st.write(data_per_sim)
    st.markdown(get_table_download_link(data_per_sim.reset_index(drop=False)), unsafe_allow_html=True)
    st.write('\* ns_per_day - estimation by last cpu hour, assuming 8 cpus')

with st.beta_expander('looking for files by'):
    st.code(cmd)#.replace('\\','\\\\').replace('*','\\*'))
    st.write(f'reading files: '+"\n\t".join(list_of_all_files))
    st.code('looking for lines like "cpu=3:16:22/wall=2:59:05/1047MB t=1327ns. Estimated: unknown(s) remaining"')

st.write(f'running time {t.current()}')



