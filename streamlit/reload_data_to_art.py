import pandas as pd
import numpy as np
import streamlit as st
import datetime
import sys, os
import io
from contextlib import redirect_stdout
from print_to_streamlit import st_stdout, st_stderr
repo_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(layout="wide")

def get_session_name():
    sessiondescription = st.sidebar.text_input('session name', 'uploading excel to ART')
    productname = st.sidebar.selectbox('productname', ['Falcon','BRK_GEN2','BRK_GEN1', 'GDR_BRK'])
    return sessiondescription, productname

sys.path.append(repo_path + '/upload_to_art/')
from simple_art_uploader import simple_art_dict, upload_to_ogre

        
current_date=datetime.datetime.now().strftime('%d-%m-%Y-%H_%M_%S')
with open(f'{os.path.dirname(os.path.abspath(__file__))}/reload_data_to_art.txt','a') as f:
    f.write(current_date+'\n')

st.header('---reload data to ART---')
st.subheader('download excel from ART, edit it and reload to ART')
excel_type=st.sidebar.selectbox('select excel type',['ART table','non ART table'])
user=st.sidebar.text_input('user name')
if excel_type!='ART table':
    sessiondescription, productname = get_session_name()

uploaded_file=st.sidebar.file_uploader('upload xlsx/csv file that you downloaded from ART (at csv remove intel confidenial first row)', type=['xlsx', 'csv'])

if uploaded_file is None:
    st.error('please upload file')
    st.stop()
    
if user is '':
    st.error('please enter user name')
    st.stop()

try:
    df=pd.read_excel(uploaded_file, header=[0])  # dropping first row that is 'intel confidential'
except:
    df=pd.read_csv(uploaded_file)
ignore_lines=st.sidebar.multiselect('select lines to ignore', range(df.shape[0]))
df=df.drop(ignore_lines)
df=df.replace(np.nan,'',regex=True).astype(str)
# df=df.drop('TestName', axis=1)
st.write(df)
if ['sessiondescription','productname'] not in df.columns.values:
    if excel_type=='ART table':
        st.sidebar.warning("excel is not from ART, you need to manually add some extra data")
        sessiondescription, productname = get_session_name()
#     df['sessiondescription'], df['productname'] = sessiondescription, productname

# with st_stdout("code"), st_stderr("error"):
tmp_dct_list=[]
with st.beta_expander('view ART dictionaries for upload:'):
    for inx,row in df.iterrows():
        tmp_dct=simple_art_dict(user=user if len(user) else row.user, 
                                  dct=row.to_dict(), session_name=sessiondescription, 
                                  project_name=productname.replace('falcon','Falcon').replace('brk_gen','BRK_GEN'))
        tmp_dct_list+=[tmp_dct]
        st.write(tmp_dct)
with st.beta_expander('python upload code:'):
    python_upload_code='''
def upload_to_ogre(all_data_dict_list, close_art_session=True):
    if not len(all_data_dict_list):
        return 
    import sys
    sys.path.append('/nfs/iil/disks/hip_ana_sim_01/dgottesm/analysis_and_tools/jupyter_notebooks/upload_to_ART/')
    sys.path.append('/nfs/iil/disks/hip_ana_sim_01/dgottesm/analysis_and_tools/jupyter_notebooks/upload_to_ART/OgreInterface/')

    from OgreInterface import OgreControl
    import importlib
    from tqdm import tqdm
    
    ARTHelper = OgreControl.clsOgreControl()
    ARTHelper.initExecusionSession(**all_data_dict_list[0]['initExecusionSession'])  # connection setup
    # all next uploads at this for loop will be at the same table, in different rows
    for data_dict in tqdm(all_data_dict_list):
        ARTHelper.fnWriteToOgre_New(**data_dict['fnWriteToOgre_New'])  # test parameters

    print('done uploading to ART!!')
    print('http://iapp257.iil.intel.com:4887/art')
    if close_art_session:
        'next lines for clearing ogre object so next upload will be new test'
        print('closing art session')
        importlib.reload(OgreControl)
        del ARTHelper
'''+f'data={tmp_dct}\nupload_to_ogre(data)'
    st.code(python_upload_code)
    
    
    
    
    
    
    
    
        
if st.button('click to reload to ART'):
    with st_stdout("code"), st_stderr("error"):
        print("You can print regular success messages")
        print("And you can redirect errors as well at the same time", file=sys.stderr)
        upload_to_ogre(tmp_dct_list)
#     with io.StringIO() as buf, redirect_stdout(buf):
#         upload_to_ogre(tmp_dct_list)
#         st.code(buf.getvalue())
    st.write('done uploading')
