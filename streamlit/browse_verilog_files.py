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
data=c()

data.path = glob(st.text_area('enter full path of the verilog folder').replace('\n',''))

if len(data.path)!=1:
    st.error('please enter existing full path')
    st.stop()
data.path = data.path[0]
data.files = [i.split('/')[-1] for i in glob(data.path+'/*')]
st.write(f'{len(data.files)} files')

file_to_compare = st.selectbox('choose file to compare', ['']+data.files)

if file_to_compare!='':
    file1=open(f'{data.path}/{file_to_compare}', 'r').read()
    file1_df=extract_ports_from_v_file(file1).fillna('')
    st.write(file1_df)
    
    net_to_show = st.selectbox('choose port to show:', ['']+file1_df.net_name.unique().tolist())
    st.write(file1_df.query('net_name==@net_to_show').T)
    
    st.code(file1)

