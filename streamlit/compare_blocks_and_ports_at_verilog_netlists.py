import streamlit as st
from glob import glob
import re
import numpy as np
import pandas as pd

# st.beta_set_page_config(layout="wide")

def extract_ports_from_v_file(v_file_content):
    pattern_direction = '(?P<direction>input|output|inout|ref)'
    pattern_name = '(?P<net_name>[^ \[]+)'
    pattern_type = '(?P<net_type>real|wrealsum|wrealavg|wreal1driver|wreal|bit)'
    pattern_bus = '(?P<bus_shape>\[\d+:\d+\])'

    patterns=dict()
    patterns['pattern_simple'] = f'{pattern_direction}\s+{pattern_name}\s*$'
    patterns['pattern_single_real'] = f'{pattern_direction}\s+{pattern_type}\s+{pattern_name}\s*$'
    patterns['pattern_bus_packed'] = f'{pattern_direction}\s+{pattern_bus}\s+{pattern_name}\s*$'
    # pattern_bus_packed = f'{pattern_direction}\s+{pattern_bus}\s+{pattern_name}\s*$'
    patterns['pattern_bus_unpacked'] = f'{pattern_direction}\s+{pattern_type}\s+{pattern_name}\s+{pattern_bus}\s*$'
    # TODO - need to add bus_packed with bit type, and also internal nets that are not ports

    df=pd.Series(v_file_content)
    df=df.str.split(',|;|\)').explode().to_frame('original_code')
    df['simplified_code']=df.original_code.copy().replace(r'\b(wire|logic)\b', '', regex=True).replace('\s+',' ', regex=True)
    df=df.query('simplified_code.str.contains("^\s+(input|output|inout)")').reset_index(drop=True)

    tmp=pd.DataFrame()
    for key, val in patterns.items():
        tmp=tmp.append(df.simplified_code.str.extract(val).dropna().assign(pattern=key))
    return df.join(tmp)


class c: pass
data=[c(),c()]

data[0].path = glob(st.text_area('enter full path of the first  verilog folder').replace('\n',''))
data[1].path = glob(st.text_area('enter full path of the second verilog folder').replace('\n',''))

if len(data[0].path)!=1 or len(data[1].path)!=1:
    st.error('please enter 2 full path')
    st.stop()

for i in [0,1]:
    data[i].path = data[i].path[0]
    data[i].files = [i.split('/')[-1] for i in glob(data[i].path+'/*')]
for i in [0,1]:
    data[i].unique = list(set(data[i].files) - set(data[not i].files))
    data[i].common = list(set(data[i].files) & set(data[not i].files))
# st.write(data[0].common)
st.write(f'{len(data[0].common)} in common, {len(data[0].unique)} uniques on 0 and {len(data[1].unique)} uniques on 1')

my_expander = st.beta_expander('show files content')
col1, col2 = my_expander.beta_columns(2)
col1.selectbox('', pd.Series(data[0].files))
col2.selectbox('', pd.Series(data[1].files))


file_to_compare = st.selectbox('choose file to compare', ['']+data[0].common)


if file_to_compare!='':
    my_expander = st.beta_expander('show files content')
    col1, col2 = my_expander.beta_columns(2)
    file1=open(f'{data[0].path}/{file_to_compare}', 'r').read()
    file2=open(f'{data[1].path}/{file_to_compare}', 'r').read()

    file1_df=extract_ports_from_v_file(file1).fillna('')
    file2_df=extract_ports_from_v_file(file2).fillna('')
    if (file1_df.simplified_code==file2_df.simplified_code).all():
        my_expander.write(f'ports at both files are identical')
    else:
        my_expander.write(f'ports at both files differs')
        differ_df=pd.merge(file1_df, file2_df, on='net_name')
        differ_df=differ_df.T.sort_index().T
        net_to_show = my_expander.selectbox('choose port to show:', ['']+differ_df.net_name.unique().tolist())
        my_expander.write(differ_df.query('net_name==@net_to_show').T)
        my_expander.write(differ_df)
#         my_expander.write(file1_df!=file2_df)
    col1, col2 = my_expander.beta_columns(2)
    col1.write(file1_df)
    col2.write(file2_df)
    
    col1.write('file from first path')
    col2.write('file from second path')
    col1.code(file1)
    col2.code(file2)


# code = open(f'{data[0].path}/{file_to_compare}', 'r').read()
# code=re.split(',|;',code)
# code= [re.sub('^\s+','', i) for i in code]
# st.write(f'"{code[3]}"')
# st.write(code)


# df=extract_ports_from_v_file(open(f'{data[0].path}/{file_to_compare}', 'r').read())
# st.write('---')
# st.write(df.fillna(''))
