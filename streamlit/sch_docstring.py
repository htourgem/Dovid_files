import pandas as pd
import numpy as np
import streamlit as st
from tqdm import tqdm_notebook as tqdm

st.header('docstring per sch block')
st.subheader("choose a cell, then read and update its documentation")
st.write("if some port is alias of another port, you can write another_port@another_block for example vin_p@ipn5brk2adctop_adc_top")
log='/nfs/iil/disks/hip_ana_sim_01/dgottesm/analysis_and_tools/jupyter_notebooks/streamlit/sch_docstring.csv'
df=pd.read_csv(log).fillna('')
# df=df.sort_values(['cell','port_direction','port_name'])

cells=df.query('port_direction=="description"').cell.values.tolist()+['']
cell = st.selectbox('pick a cell', cells)
if cell:
    relevant = df.query(f'cell=="{cell}"').sort_values('port_direction')


    st.sidebar.info('about this block:')
    # st.sidebar.info(f'''{relevant.query('port_name=="description"').description.values[0]}''')
    st.sidebar.success(relevant.query('port_name=="description"').description.values[0])
    st.sidebar.image('/nfs/iil/disks/hip_ana_sim_01/dgottesm/analysis_and_tools/jupyter_notebooks/streamlit/docstring.jpg', use_column_width=True)



    st.write(f'{relevant.shape[0]} ports:')
    st.write(relevant)
    relevant['user_updates']=relevant.description
    user_values=dict()
    updates=False
    for i, row in relevant.iterrows():
        st.subheader(f'{row.port_name} ({row.port_direction})')
        relevant.loc[i,'user_updates']=st.text_area('', value = row.user_updates, key=i)
        if relevant.loc[i,'user_updates']!= row.description:
            st.error('updated field. please press on "update db" to save the changes')
            updates=True
    if updates:
        if st.sidebar.button('update db'):
            relevant.description=relevant.user_updates
            df.update(relevant)
            df.to_csv(log, index=None)
            st.sidebar.warning('done. to see your changes at the gui, press "update db" again or choose another block')
        