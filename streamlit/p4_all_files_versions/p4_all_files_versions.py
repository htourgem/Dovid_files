import pandas as pd
pd.options.display.max_rows=200
import plotly.express as px
import streamlit as st

'''
# show versions over time per file type
'''
@st.cache(suppress_st_warning=True)
def data(p4_output):
    st.write('no cache, need to rebuild df, can take 30 sec')
    df=pd.DataFrame(open(p4_output).read().split('\n'), columns=['original'])
    st.write('done reading txt file')
    df=df.join(df.original.str.extract(r'^(?P<p4_path>//.*)').fillna(method='ffill'))
    df=df.join(df.original.str.extract(r"""... #(?P<version>\d+) change (?P<change>\d+) \w+ on (?P<date>[\d/]+) (?P<time>[\d:]+) by (?P<user>[^@]+)[^']+ '(?P<comment>[^']+)'"""))
    st.write('done parsing file')
    df=df.dropna()  # after we took the p4_path from last line, we can drop this line
    st.write('extracting extra data')
    # df['file_name']=df.p4_path.str.rsplit('/',1).str[-1]
    # df['block_name']=df.p4_path.str.rsplit('/',3).str[-3]
    # df['library_name']=df.p4_path.str.rsplit('/',4).str[-4]
    df['library_name'],df['block_name'],_,df['file_name']=zip(*df.p4_path.str.rsplit('/',4).str[-4:])
    df['file_type']=df.file_name.str.rsplit('.',1).str[-1]
    st.write('extracting date time')
    df['date_time']=pd.to_datetime(df.apply(lambda r:f'{r.date} {r.time}', axis=1), format="%Y/%m/%d %H:%M:%S")
    # print(df.describe())
    st.write('building huver data to plot')
    df['user_and_comment']=df.apply(lambda r:f'{r.user}:{r.comment}', axis=1)
    df.version=df.version.astype(int)
    return df

# generate this  file by:
# p4 filelog -t //barak2/... > $del/library_manager_versions.txt
p4_output='/nfs/iil/disks/hip_ana_sim_01/dgottesm/analysis_and_tools/debug/script_logs/library_manager_versions.txt'

st.write('reading data')
df=data(p4_output)
st.write('sampled df')
st.write(df.sample(10000))

file_type=df.file_type.value_counts().to_frame('counts').reset_index().astype(str).apply(lambda r:f'{r["index"]}   [{r.counts}]', axis=1).values
file_type=st.sidebar.selectbox('choose your file type', file_type[::-1])
st.write('done reading data')

file_type=file_type.split('   ')[0]
df_plot=df.query(f'''file_type=="{file_type}"''')

st.write('building plot')
fig=px.scatter(df_plot, x='date_time', y='version', color='block_name', hover_name='user_and_comment', height=400, width=1000).update_traces(mode='lines+markers')
st.write('done creating plot')

st.write(fig)
