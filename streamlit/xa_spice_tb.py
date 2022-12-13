import streamlit as st
import pandas as pd
import re
import plotly.express as px

def get_table_download_link(df):
    """Generates a link allowing the data in a given pandas dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    import base64
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}" download="abc.csv">Download csv file</a>'
    return href

def convert_si(si):
    import si_prefix  #pip install si-prefix
    si_prefix.SI_PREFIX_UNITS='yzafpnum kMGTPEZY' # to replace µ with u
    try:
        return si_prefix.si_parse(si)
    except:
        return si

st.header('build xa spice tb')
st.sidebar.image('/nfs/iil/disks/hip_ana_sim_01/dgottesm/analysis_and_tools/streamlit/xa_spice_tb.jpg', use_column_width=True)
demo_data = st.sidebar.checkbox('use demo data')
if demo_data:
    demo_spice='/nfs/iil/disks/hip_ana_sim_01/dgottesm/analysis_and_tools/streamlit/demo_data/xa_spice_tb/ipn5brk2top_lane_top.sp'
    sp = open(demo_spice).read().replace('\n+','')
    top='ipn5brk2top_lane_top'
    st.warning(f'running demo with spice {demo_spice}')
else:
    sp = st.sidebar.file_uploader('upload spice netlist that contains the top block', type=['sp'])
    if not sp:
        st.stop()
    sp = sp.read().decode('utf8').replace('\n+','')

    modules = ['']+re.compile('\.subckt\s+(\w+)\s+').findall(sp)
    top = st.sidebar.selectbox('select top module', modules)
    if top=='':
        st.stop()

with st.beta_expander('block details'):
    st.header(top)
    interface = re.compile(f'\.subckt\s+{top}\s+([^\n]+)').findall(sp)[0].split(' ')
    st.write(f'all {len(interface)} interface nets:')
    st.code(",".join(st.multiselect('interface nets',interface)))
    st.write(interface)


# input voltages:
with st.beta_expander('default values table and example'):
    values_df = pd.DataFrame('vcc,vcc,vcc,vss'.split(','), columns=['net']).assign(sim_time='0u,1u,1.01u,0u'.split(','), voltage=[0,0,1,0])
    st.write('example of pulling vcc up at 1us:')
    st.write(values_df)
    values_df = pd.DataFrame(interface, columns=['net']).assign(sim_time='0u', voltage=0)
    st.write('table with all nets at 0v:')
    st.markdown(get_table_download_link(values_df), unsafe_allow_html=True)
    st.write(values_df)
    
if demo_data:
    demo_values = '/nfs/iil/disks/hip_ana_sim_01/dgottesm/analysis_and_tools/streamlit/demo_data/xa_spice_tb/values.csv'
    values = pd.read_csv(demo_values)
    st.warning(f'running demo with values from {demo_values}')
else:
    values = st.sidebar.file_uploader('upload table with time and voltage values', type=['csv','xlsx'])
    if not values:
        st.stop()
    try:
        values = pd.read_csv(values)
    except:
        values = pd.read_excel(values)
default_voltage=st.sidebar.number_input('default input voltage', format= '%.2f', value=0.0, min_value=0.0, max_value=3.0, step=0.1)


if not pd.Series(['net','sim_time','voltage']).isin(values.columns).all():
    st.error('table with time and voltage values should contains the columns net, sime_time and voltage')
    st.write(values)
    st.stop()
    
# adding missing nets:
values=values.append(pd.DataFrame(set(interface)-set(values.net.unique().tolist()), columns=['net']).assign(voltage=default_voltage, sim_time='0u'))
values['sim_time_us']=values.sim_time.apply(convert_si)*1e6
# adding 0us to the nets that doesnt have this timestamp:
nets_without_zero_time = values.sort_values('sim_time_us').groupby('net', as_index=False).first().query('sim_time_us!=0').copy()
values=values.append(nets_without_zero_time.assign(sim_time_us=0, sim_time='0u'))
values['pwl']=values.sim_time+' '+values.voltage.astype(str)
# counting rows per net so we can know which has pwl and which has simple source:
values=values.merge(values.assign(voltage_changes=1).groupby('net').voltage_changes.sum(), on='net')
values['net_without_brackets']=values.net.replace(['\[','\]'],'_', regex=True)  # just for naming
values=values.sort_values(['net','sim_time_us'])


with st.beta_expander('view values table'):
    st.write(values)
    
with st.beta_expander('plotting values'):
    nets_for_plot = values.loc[values.eval('sim_time_us != 0 or voltage !=0')].net.drop_duplicates()
    nets_for_plot = nets_for_plot.to_frame().merge(values, how='left')
    nets_for_plot=nets_for_plot.append(pd.DataFrame(nets_for_plot.net.unique(), columns=['net']).assign(sim_time_us=nets_for_plot.sim_time_us.max()))
    nets_for_plot = nets_for_plot.sort_values(['net','sim_time_us']).fillna(method='ffill')
    st.write(px.line(nets_for_plot, x='sim_time_us', y='voltage', color='net'))
    st.write(px.line(nets_for_plot, x='sim_time_us', y='voltage', facet_row='net', height=300*nets_for_plot.net.unique().shape[0]))

with st.beta_expander('tb stimuli'):
    pwl = values.query('voltage_changes>1', engine='python').groupby(['net_without_brackets', 'net'], as_index=False).pwl.apply(lambda g: 'v_'+g.name[0]+' '+g.name[1]+' 0 pwl ('+g.add(' ').sum()+' )')
    pwl="\n".join(pwl.pwl.values)
    simple_sources = values.query('voltage_changes==1').apply(lambda g: 'v_'+g.net_without_brackets+' '+g.net+' 0 '+str(g.voltage), axis=1)
    simple_sources="\n".join(simple_sources.values)
    tb=''
    tb+='* update spice file name.\n'
    tb+='* if you dont have hsp file, add it also. \n'
    tb+='* comment out all voltage source that are on the outputs\n\n'
    tb+="* .lib '/nfs/site/proj/tech1/n5/tech-release/v1.1.8/models/1P17M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_5Y_vhvhv_2Yy2Yx2R/hspice/include.hsp' nom\n"
    tb+='.option tmiflag=1\n'
    tb+='.option tmiusrflag=1\n'
    tb+=f'.inc {top}.sp\n\n'
    #tb+=f'* dont forget to add instantiation for tb_{top} at the header !!!\n'
    #tb+=f'.subckt tb_{top}\n'
    tb+=f'x{top} {" ".join(interface)} {top}\n'
    tb+='*'*100+'\n'
    tb+='* pwl:\n'
    tb+=pwl+'\n'
    tb+='*'*100+'\n'
    tb+='* simple voltage source:\n'
    tb+=simple_sources+'\n'
    #tb+='.ends\n'
    #tb+=f'* end of tb_{top}\n\n'
    tb+='.end\n'
    st.code(tb)
    
with st.beta_expander('using this tb'):
    st.write('you need to write header.sp and cfg')
    st.write('at the header you dont need voltage sources. i already added instansiation of the DUT in the header.sp...')
    st.write('then run it with xa -hspice header.sp -c cfg')
    st.warning('remember to remove all drivers from the output nets!')

with st.beta_expander('vcs xa setup'):
    st.write('first open ion shell')
    st.write('then run those lines:')
    vcs_xa_setup='''
setenv SNPSLMD_LICENSE_FILE 26586@synopsys23p.elic.intel.com:26586@synopsys11p.elic.intel.com:26586@synopsys09p.elic.intel.com:26586@synopsys01p.elic.intel.com:26586@synopsys03p.elic.intel.com:26586@synopsys21p.elic.intel.com:26586@synopsys22p.elic.intel.com:26586@synopsys23p.elic.intel.com:26586@synopsys11p.elic.intel.com:26586@synopsys09p.elic.intel.com:26586@synopsys01p.elic.intel.com:26586@synopsys03p.elic.intel.com:26586@synopsys21p.elic.intel.com:26586@synopsys22p.elic.intel.com:26586@synopsys23p.elic.intel.com

# for XA:
setenv XA_HOME /p/hdk/cad/xa/O-2018.09-SP5
setenv XA_HOME /p/hdk/cad/xa/P-2019.06-SP5-T-20200326
setenv XA_HOME /p/hdk/cad/xa/Q-2020.03-SP4/
setenv XA_HOME /p/hdk/cad/xa/R-2020.12/
setenv XA_64 1
setenv XA_SHARED_LICENSE_ORDER hsim-cosim:hsim-sc:hsim-ms:xsim:fastspice_xa+hsim-xl
setenv XA_GCC /p/hdk/rtl/cad/x86-64_linux30/synopsys/xa/P-2019.06-SP5/GNU/linux64/gcc-6.2.0/bin/gcc
setenv VG_GNU_PACKAGE /p/com/eda/synopsys/vggnu/2014.12

# for vcs:
setenv VCS_HOME /p/hdk/cad/vcsmx/O-2018.09-SP2-5
setenv VCS_HOME /p/hdk/cad/vcsmx/P-2019.06-SP2-3
setenv VCS_HOME /p/hdk/rtl/cad/x86-64_linux30/synopsys/vcsmx/R-2020.12-1/
setenv VCS_TARGET_ARCH suse64
unsetenv SYNOPSYS_SIM_SETUP

setenv VERDI_HOME /p/hdk/rtl/cad/x86-64_linux30/synopsys/verdi3/P-2019.06-SP2
setenv PATH "$VCS_HOME/bin:$XA_HOME/bin:$VERDI_HOME/bin:/p/hdk/cad/wv/Q-2020.03-SP1/bin/:$PATH"
    '''
    st.code(vcs_xa_setup)
