import pandas as pd
import shutil
import os
from glob import glob
import fileinput
import streamlit as st
import io


def check_table(df):
    if 'input_dir' not in df.index or 'output_dir' not in df.index:
        st.write('table must contains input_dir and output dir as one of the index')
        return False
    return True


def get_table_download_link(df):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    import base64
#     xlsx = df.to_excel(index=False)
#     xlsx = df.to_csv(index=False)
    xlsx = df.to_csv()
    b64 = base64.b64encode(xlsx.encode()).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}" download="example.csv">example csv file</a>'
    return href



def single_duplication_per_col(input_dir, output_dir, replace_dict):
#     replace_dict['**date**'] = pd.datetime.now().strftime('%Y.%m.%d_%H.%M.%S')
#     if '**date**' in output_dir:
#         output_dir=output_dir.replace('**date**',replace_dict['**date**'])
    # shutil.rmtree(output_dir, ignore_errors=True)
    if not os.path.exists(input_dir):
        st.write(f'folder "{input_dir}" dosnt exist, skipping this column!')
        return
    if os.path.exists(output_dir):
        st.write(f'folder "{output_dir}" already exist, skipping this column!')
        return
    
    st.write(f'creating directory {output_dir}')
    shutil.copytree(input_dir, output_dir)
    list_of_all_files=[f for f in glob(output_dir+'/**', recursive=True) if os.path.isfile(f)]
    with fileinput.FileInput(files=list_of_all_files, inplace=True) as file:
        for line in file:
            for k,v in replace_dict.items():
                line = line.replace(k, v)
            print(line, end='')

st.header('duplicating folder with find replace')
# df=pd.DataFrame(['hi','del','****'], index=['input_dir','output_dir','abcd'])
st.write('the csv/xlsx file should contains only 1 sheet, first column with patterns that you want to replace, and also input_dir and output_dir, and the rest of columns the replaced value and the directories linux full path.')
st.write('first row is ignored, you can put your names.')
st.write('\**date** in output_dir will be replaced with current time')

example_xslx=pd.DataFrame(index=['input_dir','output_dir', 'replace me'])
example_xslx['test1']=['/nfs/iil/disks/ams_regruns/dkl/users/lisrael1/msv/temp_del/msv_example_test_brk2/','/nfs/iil/disks/ams_regruns/dkl/users/lisrael1/msv/temp_del/msv_example_test_brk2/test_1_**date**', 'to this']
example_xslx['test2']=['/nfs/iil/disks/ams_regruns/dkl/users/lisrael1/msv/temp_del/msv_example_test_brk2/','/nfs/iil/disks/ams_regruns/dkl/users/lisrael1/msv/temp_del/msv_example_test_brk2/test_2_**date**', 'another option']
st.markdown(get_table_download_link(example_xslx), unsafe_allow_html=True)

uploaded_file=st.file_uploader('upload csv or xlsx file',type=['xlsx', 'csv'])
if uploaded_file:
    try:
        df=pd.read_csv(uploaded_file, index_col=[0]).fillna('').astype(str)
    except:
        df=pd.read_excel(uploaded_file, index_col=[0]).fillna('').astype(str)
#     df.loc['**date**'] = [pd.datetime.now().strftime('%Y.%m.%d_%H.%M.%S')]*df.shape[1]
    df=df.replace('\*\*date\*\*', pd.datetime.now().strftime('%Y.%m.%d_%H.%M.%S'), regex=True)
    st.write(df)
    if check_table(df):
        for (column_name, col_sr) in df.iteritems():
            st.write(f'working on column "{column_name}"')
            single_duplication_per_col(col_sr.input_dir, col_sr.output_dir, col_sr.to_dict())  # col_sr.drop(['input_dir','output_dir'])
    st.code(f'''bash -c 'for d in {df.T.output_dir.add(" ").sum()}; do echo $d;done' ''')
