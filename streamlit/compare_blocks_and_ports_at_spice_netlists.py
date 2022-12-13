import streamlit as st
import pandas as pd
from glob import glob
import os
import numpy as np

st.header('compare blocks and their ports at 2 spice netlists')
st.write('enter 2 netlists with full path, and this tool will look for missing blocks or missing ports')
st.write('assuming ports are sorted as spice should be')

def check_if_file_exist(f):
    if not len(f):
        return None
    f_out=glob(f)
    if len(f_out)!=1:
        st.write(f'there is no "{f}" file (or more than 1 match)')
        return None
    return f_out[0]

@st.cache(suppress_st_warning=True)
def parse_blocks_and_ports_from_spice_netlist(file_path, file_date):
    content = open(file_path).read().replace('\n+','')
    block_line = r'^\.subckt\s+(?P<block_name>[\w_\d\[\]]+)\s+(?P<port_names>[\w_\d\[\]\s]+)'
    df=pd.DataFrame(content.split('\n'), columns=['lines'])
    df=df.join(df.lines.str.extract(block_line)).dropna()
    df['number_of_ports_in_block_with_bus_split']=df.port_names.str.split(' ').str.len()
    df['unique_ports']=df.port_names.apply(parse_ports_string)
    df['number_of_ports_in_block']=df.unique_ports.str.split(' ').str.len()
    return df
    
def parse_ports_string(ports):
    df=pd.DataFrame(ports.split(' '), columns=['original'])
    df['port_number']=df.original.str.extract(r'\[(?P<num>\d+)\]')
    df['block_name']=df.original.str.extract(r'(?P<block>[^[]+)')
    ports_and_bus = df.groupby('block_name').port_number.apply(lambda n:f'[{max(n)}:{min(n)}]' if min(n)==min(n) else '').reset_index().sum(1)
    return ports_and_bus.sort_values().add(' ').sum()
    
spice1=check_if_file_exist(st.text_input('first spice netlist full path'))
spice2=check_if_file_exist(st.text_input('second spice netlist full path'))

if spice1 is not None:
    st.write('parsing spice 1')
    file_date1=os.path.getmtime(spice1)
    spice1=parse_blocks_and_ports_from_spice_netlist(spice1, file_date1).assign(netlist='spice1')
    st.write(f'found {spice1.shape[0]} blocks')
    st.sidebar.code(f'{spice1.shape[0]} blocks in spice 1')
    st.write(spice1)

if spice2 is not None:
    st.write('parsing spice 2')
    file_date2=os.path.getmtime(spice2)
    spice2=parse_blocks_and_ports_from_spice_netlist(spice2, file_date2).assign(netlist='spice2')
    st.write(f'found {spice2.shape[0]} blocks')
    st.sidebar.code(f'{spice2.shape[0]} blocks in spice 2')
    st.write(spice2)
    
if spice1 is not None and spice2 is not None:
    st.header('comparing')
    s1_not_s2 = spice1.query(f'not block_name.isin({spice2.block_name.values.tolist()})')
    st.write(f'{s1_not_s2.shape[0]} blocks are at spice 1 but not at spice 2')
    st.sidebar.code(f'{s1_not_s2.shape[0]} blocks at spice 1 and missing at spice 2')
    st.write(s1_not_s2)
    
    s2_not_s1 = spice2.query(f'not block_name.isin({spice1.block_name.values.tolist()})')
    st.write(f'{s2_not_s1.shape[0]} blocks are at spice 2 but not at spice 1')
    st.sidebar.code(f'{s2_not_s1.shape[0]} blocks at spice 2 and missing at spice 1')
    st.write(s2_not_s1)
    
    # full match 
    s1_match_s2 = pd.concat([spice1,spice2], axis=0)
    s1_match_s2 = s1_match_s2[s1_match_s2.duplicated(['block_name','unique_ports'],keep=False)]
    st.write(f'{s1_match_s2.shape[0]} blocks has same name and ports at spice 2 and at spice 1. perfect!')
    st.sidebar.code(f'{s1_match_s2.shape[0]} match blocks and ports between spice 1 and 2')
    st.write(s1_match_s2)

    
    st.header('same blocks different ports')
    spice1_ports = spice1.assign(split_unique_ports=lambda x:x.unique_ports.str.split(' ')).explode('split_unique_ports')
    spice2_ports = spice2.assign(split_unique_ports=lambda x:x.unique_ports.str.split(' ')).explode('split_unique_ports')
    
    same_block_list = np.intersect1d(spice1.block_name,spice2.block_name).tolist()
    different_ports = pd.concat([spice1_ports.query(f'block_name.isin({same_block_list})'), spice2_ports.query(f'block_name.isin({same_block_list})')], axis=0).drop_duplicates(['block_name','split_unique_ports'], keep=False)
    st.write(f'missing ports - those {different_ports.shape[0]} ports doesnt have a friend at the other netlist')
    st.sidebar.code(f'{different_ports.shape[0]} missing ports')
    st.write(different_ports[['block_name','split_unique_ports','netlist']])

    st.write('those blocks has different number of ports')
    same_block_different_ports = pd.merge(spice1, spice2, how='inner', on='block_name', suffixes=['_spice1','_spice2'])
    same_block_different_ports = same_block_different_ports.query('number_of_ports_in_block_with_bus_split_spice1!=number_of_ports_in_block_with_bus_split_spice2 or number_of_ports_in_block_spice1!=number_of_ports_in_block_spice2')
    st.sidebar.code(f'{same_block_different_ports.shape[0]} blocks with different number of ports')
    st.write(same_block_different_ports)
