import streamlit as st

st.header('code coloring')
text = st.text_area('write you code here')
st.write('colored code:')
language=st.selectbox('language', ['python','bash','c'])
st.code(text, language=language)