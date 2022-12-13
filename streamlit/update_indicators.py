import streamlit as st
import numpy as np
import pandas as pd

st.header('download sine/prbs excel from ART and update indicators')
uploaded_file=st.file_uploader('upload xlsx file', type='xlsx')

df=pd.read_excel(uploaded_file, index_col=[0]).fillna('').astype(str)