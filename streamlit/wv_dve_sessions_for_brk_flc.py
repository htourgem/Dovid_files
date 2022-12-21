import streamlit as st
import datetime
import re
from collections import OrderedDict
import sys, os
repo_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def find_replace():
    f = []
    r = []
    st.sidebar.success(f'find replace on net names (supports python regex):')
    while True:
        elements = len(f)
#         st.sidebar.success(f'find replace {elements+1}:')
        st.sidebar.image(repo_path + '/streamlit/line.jpg')
        f.append(st.sidebar.text_input(f'find {elements+1}' , key=elements))
        r.append(st.sidebar.text_input(f'replace {elements+1}' , key=elements))
        if f[-1]=="": # if last input is not empty, add new inputs
            break
    # building the find replace dictionary
    fr = dict()
    for i in range(len(f)-1):
        fr[f[i]]=r[i]
    return fr

st.header('session generator')
st.sidebar.image(repo_path + '/streamlit/wv_dve_sessions_for_brk_flc.jpg', use_column_width=True)

# inputs:
prefix = st.text_input('write sara prefix')
suffix = st.text_input('write sar suffix (net name)')

place=st.sidebar.selectbox('adc place', ['FE','sara'])
tool=st.sidebar.selectbox('wave tool', ['dve','wv'])
add_x=st.sidebar.checkbox('add x like at spice')

fr=find_replace()


if tool == 'wv':
    st.sidebar.info('please run wv with -console')

dve = '''
proc display_wave {net_path alias} {
        set wave "Wave.1";
        gui_list_add -id $wave $net_path;
        gui_list_select -id $wave -selected $net_path;
        gui_list_set_selected_property -id $wave -addalias $alias; 
}
'''
wv ='''
proc display_wave {sig_name alias} {
    set obj [sx_signal $sig_name];
    sx_display $obj;
    sx_set_line_alias [sx_first_line [sx_current_panel]] $alias
}
'''
sara_path='''
display_wave {prefix}.sar_array.sararray_ch_all_sars.q0_qrts.octet0.qrt0.sar0.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q1_qrts.octet0.qrt0.sar0.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q2_qrts.octet0.qrt0.sar0.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q3_qrts.octet0.qrt0.sar0.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q0_qrts.octet1.qrt0.sar0.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q1_qrts.octet1.qrt0.sar0.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q2_qrts.octet1.qrt0.sar0.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q3_qrts.octet1.qrt0.sar0.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q0_qrts.octet1.qrt1.sar0.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q1_qrts.octet1.qrt1.sar0.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q2_qrts.octet1.qrt1.sar0.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q3_qrts.octet1.qrt1.sar0.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q0_qrts.octet0.qrt1.sar0.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q1_qrts.octet0.qrt1.sar0.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q2_qrts.octet0.qrt1.sar0.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q3_qrts.octet0.qrt1.sar0.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q0_qrts.octet0.qrt0.sar1.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q1_qrts.octet0.qrt0.sar1.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q2_qrts.octet0.qrt0.sar1.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q3_qrts.octet0.qrt0.sar1.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q0_qrts.octet1.qrt0.sar1.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q1_qrts.octet1.qrt0.sar1.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q2_qrts.octet1.qrt0.sar1.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q3_qrts.octet1.qrt0.sar1.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q0_qrts.octet1.qrt1.sar1.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q1_qrts.octet1.qrt1.sar1.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q2_qrts.octet1.qrt1.sar1.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q3_qrts.octet1.qrt1.sar1.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q0_qrts.octet0.qrt1.sar1.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q1_qrts.octet0.qrt1.sar1.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q2_qrts.octet0.qrt1.sar1.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q3_qrts.octet0.qrt1.sar1.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q0_qrts.octet0.qrt0.sar2.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q1_qrts.octet0.qrt0.sar2.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q2_qrts.octet0.qrt0.sar2.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q3_qrts.octet0.qrt0.sar2.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q0_qrts.octet1.qrt0.sar2.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q1_qrts.octet1.qrt0.sar2.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q2_qrts.octet1.qrt0.sar2.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q3_qrts.octet1.qrt0.sar2.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q0_qrts.octet1.qrt1.sar2.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q1_qrts.octet1.qrt1.sar2.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q2_qrts.octet1.qrt1.sar2.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q3_qrts.octet1.qrt1.sar2.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q0_qrts.octet0.qrt1.sar2.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q1_qrts.octet0.qrt1.sar2.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q2_qrts.octet0.qrt1.sar2.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q3_qrts.octet0.qrt1.sar2.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q0_qrts.octet0.qrt0.sar3.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q1_qrts.octet0.qrt0.sar3.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q2_qrts.octet0.qrt0.sar3.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q3_qrts.octet0.qrt0.sar3.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q0_qrts.octet1.qrt0.sar3.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q1_qrts.octet1.qrt0.sar3.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q2_qrts.octet1.qrt0.sar3.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q3_qrts.octet1.qrt0.sar3.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q0_qrts.octet1.qrt1.sar3.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q1_qrts.octet1.qrt1.sar3.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q2_qrts.octet1.qrt1.sar3.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q3_qrts.octet1.qrt1.sar3.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q0_qrts.octet0.qrt1.sar3.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q1_qrts.octet0.qrt1.sar3.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q2_qrts.octet0.qrt1.sar3.{suffix} e_
display_wave {prefix}.sar_array.sararray_ch_all_sars.q3_qrts.octet0.qrt1.sar3.{suffix} e_'''
fe_path='''
display_wave  {prefix}.adc_fe.qrt0.pi_th1_ffe_0_.th1_ffe.brk_th.{suffix} e_
display_wave  {prefix}.adc_fe.qrt1.pi_th1_ffe_0_.th1_ffe.brk_th.{suffix} e_
display_wave  {prefix}.adc_fe.qrt2.pi_th1_ffe_0_.th1_ffe.brk_th.{suffix} e_
display_wave  {prefix}.adc_fe.qrt3.pi_th1_ffe_0_.th1_ffe.brk_th.{suffix} e_
display_wave  {prefix}.adc_fe.qrt0.pi_th1_ffe_1_.th1_ffe.brk_th.{suffix} e_
display_wave  {prefix}.adc_fe.qrt1.pi_th1_ffe_1_.th1_ffe.brk_th.{suffix} e_
display_wave  {prefix}.adc_fe.qrt2.pi_th1_ffe_1_.th1_ffe.brk_th.{suffix} e_
display_wave  {prefix}.adc_fe.qrt3.pi_th1_ffe_1_.th1_ffe.brk_th.{suffix} e_
display_wave  {prefix}.adc_fe.qrt0.pi_th1_ffe_2_.th1_ffe.brk_th.{suffix} e_
display_wave  {prefix}.adc_fe.qrt1.pi_th1_ffe_2_.th1_ffe.brk_th.{suffix} e_
display_wave  {prefix}.adc_fe.qrt2.pi_th1_ffe_2_.th1_ffe.brk_th.{suffix} e_
display_wave  {prefix}.adc_fe.qrt3.pi_th1_ffe_2_.th1_ffe.brk_th.{suffix} e_
display_wave  {prefix}.adc_fe.qrt0.pi_th1_ffe_3_.th1_ffe.brk_th.{suffix} e_
display_wave  {prefix}.adc_fe.qrt1.pi_th1_ffe_3_.th1_ffe.brk_th.{suffix} e_
display_wave  {prefix}.adc_fe.qrt2.pi_th1_ffe_3_.th1_ffe.brk_th.{suffix} e_
display_wave  {prefix}.adc_fe.qrt3.pi_th1_ffe_3_.th1_ffe.brk_th.{suffix} e_'''

assert len(prefix)*len(suffix)!=0, st.warning('please update prefix and suffix')
text = dict(FE=fe_path, sara=sara_path)[place][1:]  # removing the new line at the begining
if add_x:
    text = text.replace('.','.x').replace('.x{suffix}','.{suffix}')
text = text.format(**locals())

# running the find replace
for k,v in fr.items():
    text = re.sub(k,v,text)

# now removing duplications and adding enumeration
text=list(OrderedDict.fromkeys(text.split('\n')))
text = '\n'.join([f'{c}{i:03}' for i,c in enumerate(text)])

# adding the tool (dve/wv) function
text = dict(dve=dve, wv=wv)[tool]+text
st.write('tcl code')
st.code(text)

# saving tcl code to file, so you can do source on it
output_file = f'/nfs/iil/disks/ams_regruns/dkl/users/lisrael1/msv/temp_del/verilog_helper/{tool}_session_{datetime.datetime.now().strftime("%d-%m-%Y-%H.%M.%S")}.tcl'
f=open(output_file, 'w')
f.write('#!/usr/intel/bin/tcl')
f.write(f'# tcl script for {tool}')
f.write(text)
f.close()

st.sidebar.info(f'now run it at {tool} by:')
st.sidebar.code(f'source {output_file}')
if tool == 'wv':
    st.write('general example - you can also run:')
    st.code('sx_display [sx_signal *q*_qrts.octet*.qrt*.sar*.i_sar_clk]')
    
    
