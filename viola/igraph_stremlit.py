import pandas as pd
import os
import streamlit as st
import re
from os.path import join
from os.path import exists
import sys
import glob
import numpy as np
from datetime import datetime
sys.path.append("/nfs/iil/disks/falcon_tc2-rtl/TC2/users/yehudabe/work/analog_sa/verif/scripts/")
from sv_netlist_analyzer import sv_analyze as sv
sys.path.append('/nfs/iil/disks/home18/yehudabe/python/')

project_identifier="eth"

fix_lists_path='/nfs/iil/disks/ams_regruns/dkl/users/yehudabe/bmods_tool/fixes/'
@st.cache(allow_output_mutation=True,suppress_st_warning=True )
def create_sst():
    from sst import sst
    sst=sst()
    return sst
sst=create_sst()

columns2view=['instance','father_block', 'father_net', 'father_type', 'son_block', 'son_net', 'son_type', 'son_direction','father_file', 'son_file']
st.title("SV netlist analyzer")
#st.set_page_config(layout="wide")
st.header('SV netlist anlyzing for BMOD Purpose')
st.warning('NOTE! -- The netlist will be analyzed only  AT FIRST RUN . In order to re-analyzed please click menu(at right up corner)-->Clear Cache.\n\n\nAfeter first run the only running perocedure is the Net Visualizer')
local_folder = st.sidebar.text_input('Netlis folder to analyze ')
only_type_conflict=0#st.sidebar.checkbox("Run only tree chart", value=False)
top_module=st.sidebar.text_input('Optional: Top module for partial analisys')

st.sidebar.image("/nfs/iil/disks/home18/yehudabe/images/tree.jpg")
if not  os.path.isdir(local_folder):
  st.warning('Please input a corect SV netlis')
  st.stop()


def fix_file(f, find_ptrn, replace_ptrn):
    if not exists(f) :
        st.warning(f'file {f} not exixst something went wrong please check..') 
    else:
        if (f.split('.')[1]=='sv'):
            st.warning(f'You changing leaf file - You shoud fix virtuoso DB as well') 
        with open(f,'r+') as fl:
            if not fl.writable():
                st.warning(f'file not writeble please run:\n chmod g+w {f}')
            else:
                d=fl.read()
                n=re.sub(find_ptrn,replace_ptrn, d)
                fl.seek(0)
                fl.write(n)
                fl.truncate()

def fix_present(f, find_ptrn, replace_ptrn):
    if not exists(f) :
        st.warning(f'file {f} not exixst something went wrong please check..') 
        return 0
    else:
        if (f.split('.')[1]=='sv'):
            st.warning(f'You changing leaf file - You shoud fix virtuoso DB as well') 
        with open(f,'r+') as fl:
            st.write(f'replacing {find_ptrn} with {replace_ptrn} on file {f}')
            d=fl.read()
            n=re.sub(find_ptrn,replace_ptrn, d)
            st.warning(set(d.split('\n')) ^ set(n.split('\n')))
            return n 

@st.cache(allow_output_mutation=True)
def get_file_with_t_stamp(fix_lists_path,top_level):
    return join(fix_lists_path,top_level+'_'+datetime.now(tz=None).strftime("%d-%b-%Y__%H:%M")+'.csv')

#look for existing fix list 
create_list_file=False
file_list=os.listdir(fix_lists_path)
file_list.append('Create New')
fix_list_req=st.selectbox('Choose file Load/Add to  fix list',file_list, index=len(file_list)-1) 
st.write(f'file list req {fix_list_req }')
if sst.fix_list_req ==None and  fix_list_req !='Create New':
    sst.fix_list_file=join(fix_lists_path,fix_list_req)  

st.write('Means -')
st.write('If you just choose file - the fixes you do will be adde to it,')
st.write('If you Choose file and hit "apply to netlist" - all fixes exist in csv will be apply to your nrtlist and new fixes will be added to this file.')
st.write('When choosing "Create New" - new file will be created according to your top level + time stamp')

if st.button('Apply to new netlist'):
    fixes_df=pd.read_csv(sst.fix_list_file)
    fixes_df.apply(lambda row: fix_file(glob.glob(join(local_folder,row.block_name+'.*v'))[0],row.find_ptrn,row.replace_ptrn), axis=1)

#create netlistt DB 
@st.cache(allow_output_mutation=True)
def get_sv_object(path,top_module=None):
    s=sv(path) if top_module==None else sv(path,top_module)
    s.create_netlist_db()
    return s
if not sst.run:
    sst.run= st.button('Create Netlist DB')
else: 
    st.write('Creating SV netlist DB- can take few min')
    s=get_sv_object(local_folder,top_module) if top_module else get_sv_object(local_folder)
    
        #sst.fix_list_file=get_file_with_t_stamp(fix_lists_path,s.df.instance.iloc[1].split(".")[0])
        #fix_df=pd.DataFrame(columns=['block_name', 'find_ptrn','replace_ptrn'])
        #fix_df.to_csv( sst.fix_list_file)
    sst.fix_list_req=fix_list_req
    st.write(f'uses {sst.fix_list_file} for fix list')
    if 'var' in s.df['son_type'].unique():
        st.warning(f'Your Netlist include "var" - it may cuse issues. Please run \n\n sed -i \'s@ var @ @g\' {local_folder}/* \n\n sed -i \'s@^var @ @g\' {local_folder}/* ')
    st.write(f'df max:{max(s.df.index)} df min: {min(s.df.index)}')
    st.header('SV Net Visualizer:')
    index=st.number_input("enter net index to view",min_value=min(s.df.index), max_value=max(s.df.index), step=1)
    index=int(index)
    #if not index:
    #  st.warning('Please input index')
    #  st.stop()
    if index:
        index=s.net_root(index)
        net_df=s.trace_net(block=s.df.iloc[index].father_block, net=s.df.iloc[index].father_net, instance=s.df.iloc[index].instance.split(".<")[0])
        st.write(f'Number of instances in net- {len(net_df.index)} Net instances:')
        st.write(net_df[columns2view])
        f=s.get_net_fig(net_df)
        st.plotly_chart(f,use_container_width=False)
        
    #### Fixing files 
            
        find_ptrn=None
        replace_ptrn=None
    
        def show_source(f,ptrn):
            if not exists(f) :
                st.warning(f'file {f} not exixst something went wrong please check..') 
            else:
                st.write('Source Code:')
                with open(f,'r') as fl:
                    for l in fl.read().split('\n'):
                        d=re.findall(ptrn,l)
                        if d:
                            st.write('-   '+l)
            #st.write('show source Done!')
         
        fix_block=st.selectbox("Module to fix",np.unique(net_df[['father_block', 'son_block']].values))
        net_list=np.unique(np.append(net_df.query(f'father_block=="{fix_block}"')['father_net'].values,net_df.query(f'son_block=="{fix_block}"')['son_net'].values))
        if len(net_list)>1: fix_net=st.selectbox("Net to fix",net_list)
        else: fix_net=net_list[0]
        fix_filed= st.selectbox('What to fix',('Direction', 'Type'))
        
        type_list=np.unique(net_df[['son_type','father_type']].values).tolist()
        if '-1' in type_list:
            type_list.remove('-1')
        if '--inter_wire_not_declared--' in type_list:
            type_list.remove('--inter_wire_not_declared--')
        if '--subcell_exist_but_error_port--' in type_list:
            type_list.remove('--subcell_exist_but_error_port--')
        
        if fix_filed=='Direction':
            father_son='son'
            fix_to = st.selectbox('Choose Direction',('in', 'out'))
            if (net_df.query(f'son_block=="{fix_block}"').head(1).son_direction.values not in ['in','out']):
                st.write("Sory Can't ...")
                find_ptrn=None
                replace_ptrn=None
            else:
                d=net_df.query(f'son_block=="{fix_block}"').son_direction
                t='' if (net_df.query(f'son_block=="{fix_block}"').head(1).son_type.values=='wire') else net_df.query(f'son_block=="{fix_block}"').son_type
                n=fix_net #net_df.query(f'son_block=="{fix_block}"').son_net
                find_ptrn=f'{d}put\s+{t}\s\+{n}([,;\s])'
                replace_ptrn=f'{fix_to}put {t} {n}\g<1>'
        else:
            
            manual=st.checkbox('I want to put my own type')
            if not manual: 
                fix_to = st.selectbox('Choose Type:',type_list)
            else:   
                fix_to= st.text_input('Insert your type:')
            #if (father_son=='son'):
            #    p=s.df.iloc[fix_index][f'{father_son}_direction']
            #    t='' if s.df.iloc[fix_index][f'{father_son}_type']=='wire' else s.df.iloc[fix_index][f'{father_son}_type']
            #    n= s.df.iloc[fix_index][f'{father_son}_net']
            #    find_ptrn=f'{p}\+{t}\s\+{n}'
            #    replace_ptrn=f'{p}put\s\+{fix_to}\s\+{n}'
            #else:
            father_son=''
            b_df=net_df.query(f'father_block=="{fix_block}" & father_net=="{fix_net}"')
            if  b_df.empty:
                b_df=net_df.query(f'son_block=="{fix_block}" & son_net=="{fix_net}"')
                if b_df.empty:
                    st.write("Sory Can't ...")
                else:
                    father_son='son'
            else:
                father_son='father'
            if len(b_df.index)>1: 
                b_df=b_df.head(1)
            t= b_df[f'{father_son}_type'].iloc[0]
            if t in s.logic_family :
                t_f='((wire|wire logic|logic|wire real)|(?P<u>ut))'
            elif ('_not_declared--' in t) or ('_error_port--' in t):
                t_f='(?P<u>ut)*\s+[\w\d_]+'
            else: t_f='(?P<u>ut)*'+t
            n=fix_net #b_df[f'{father_son}_net'].iloc[0]
            find_ptrn='{}\s+(?P<b>[\[\]\d:\s]*){}(?P<d>[;,\s])'.format(t_f,n) if  'real' not in t else r'{}\s+{}(?P<b>[\[\]\d:\s]*)(?P<d>[;,\s])'.format(t_f,n)
            replace_ptrn=f'\g<u> {fix_to} \g<b>{n}\g<d>' if fix_to in s.logic_family else f'\g<u> {fix_to} {n} \g<b>\g<d>' 
        
        if (find_ptrn!=None  and replace_ptrn!=None):
            file_to_fix=glob.glob(net_df.query(f'{father_son}_block=="{fix_block}"').head(1)[f'{father_son}_file'].iloc[0])[0]
            present_flag=st.button('Suggest Fix')#, on_click=fix_file, args=(file_to_fix, find_ptrn, replace_ptrn)) 
            if present_flag:
                n=fix_present(file_to_fix, find_ptrn, replace_ptrn)
            approve_flag=st.button('Approve Fix')
            if approve_flag and n:
                    fix_file(file_to_fix, find_ptrn, replace_ptrn)
                    if sst.fix_list_file!=None :
                        fix_df=pd.read_csv(sst.fix_list_file)
                    else:
                        sst.fix_list_file=get_file_with_t_stamp(fix_lists_path,s.df.instance.iloc[1].split(".")[0])
                        fix_df=pd.DataFrame(columns=['block_name', 'find_ptrn','replace_ptrn'])
                    fix_df=fix_df.append( {'block_name':fix_block, 'find_ptrn':find_ptrn,'replace_ptrn':replace_ptrn},ignore_index=True)
                    st.write(fix_df)
                    fix_df.to_csv(sst.fix_list_file,index=False)
            #When first hit go fix 
            u=st.button('Show Source')
            if u:show_source(  file_to_fix, f'[{"|".join(type_list)}|wire logic|wire real]\s+{n}')
            
    ############## Checkers
    
    st.markdown("<h2 style='text-align: center; color: red;'>-~-~-~-~-~-~-~-~-Checkers~-~-~-~-~-~-~-~</h2>", unsafe_allow_html=True)
    #st.write("-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~")
    if not only_type_conflict:
    
        #### Checking types conflicts
        @st.cache(allow_output_mutation=True,suppress_st_warning=True )
        def get_conf_df(): 
            conf_df=s.df[~s.df.apply(lambda row: ((row.son_type in s.logic_family) and (row.father_type in s.logic_family)), axis=1 )]
            conf_df=conf_df.query('((son_type!="--subcell_exist_but_error_port--")&(father_type!="--inter_wire_not_declared--"))')
            return conf_df.query('(son_type!=father_type)')
        conf_df=get_conf_df()
        if not conf_df.empty:
            st.header('Type Conflicts : ')
        #    with st.beta_expander('Type conflicts'):
            st.write(conf_df[columns2view])
            #if index:
            #    m=st.button('Remove current net from conflict list')
            #    if m :conf_df=conf_df[conf_df.index.isin(net_df.index)]
    
        ### Check drivers VSS 
        @st.cache(allow_output_mutation=True)
        def get_vss_d_df():
            return s.df[s.df.apply(lambda row : "vss" in row.father_net.lower(),axis=1)].query('(son_direction=="out")')#.query('(father_net=="vssx")')#&((son_direction=="out")|(son_direction=="inout"))')
        vss_d_df=get_vss_d_df()
        if not vss_d_df.empty:
            st.header('VSS drivers : ')
            st.write(vss_d_df[columns2view])
        
        
        ### Check drivers on Vcc 
        @st.cache(allow_output_mutation=True)
        def get_vcc_d_df():
            return s.df[s.df.apply(lambda row : row.father_net.lower().startswith("vcc"),axis=1)].query('(son_direction=="out")')
        vcc_d_df=get_vcc_d_df()
        if not vcc_d_df.empty:
            st.header('VCC drivers : ')
            st.write(vcc_d_df[columns2view])
        
        ### check vcc and vss inout in custom cells 
        @st.cache(allow_output_mutation=True)
        def get_sup_inout_df(): 
            sup_inout_df=s.df[s.df.apply(lambda row : (row.son_net.lower().startswith("vcc") or row.son_net.lower().startswith("vss") )  and row.son_block.lower().startswith(project_identifier) ,axis=1)].query('(son_direction=="inout")')
            return sup_inout_df.drop_duplicates()
        sup_inout_df=get_sup_inout_df()
        if not sup_inout_df.empty:
            st.header('VCC and VSS inout : ')
            st.write(sup_inout_df[columns2view])
            fix_inout=st.button('Fix All to input')
            st.write('WARNING - You should better beckoup you netlist befor hitting this button ! ' )  
            if (fix_inout): 
                sup_inout_df.apply(lambda row: fix_file(glob.glob(row.son_file)[0],f'inout\s+{row.son_net}',f'input {row.son_net}'), axis =1)
        
        ### check for supply connect to real/nettype
        @st.cache(allow_output_mutation=True)
        def get_sup2r_df(): 
            sup2r_df=s.df[s.df.apply(lambda row : (row.son_net.lower().startswith("vcc") or row.son_net.lower().startswith("vss") )  and row.son_block.lower().startswith(project_identifier) ,axis=1)]
            sup2r_df=sup2r_df[sup2r_df.apply(lambda row: row.father_type not in s.logic_family,axis=1)]
            return sup2r_df.drop_duplicates()
        sup2r_df=get_sup2r_df()
        if not sup2r_df.empty:
            st.header('VCC and VSS connected to real : ')
            st.write(sup2r_df[columns2view])
    
        ### Check for multi driver on 'real' net 
        @st.cache(allow_output_mutation=True)
        def get_multi_drive_df():
            multi_drive_df=s.df[s.df.apply(lambda row : (row.son_type not in s.logic_family) and (row.son_direction=="in")  , axis=1) ]
            multi_drive_df=multi_drive_df.query('((son_type!="--subcell_exist_but_error_port--")&(father_type!="--inter_wire_not_declared--"))')
            def driver_num(index):
                root=s.net_root(index)
                net_df=s.trace_net(block=s.df.iloc[root].father_block, net=s.df.iloc[root].father_net, instance=s.df.iloc[root].instance.split(".<")[0])
                net_df['leaf']=net_df.apply( lambda row: len(net_df.query(f'(father_block=="{row.son_block}") & (father_net=="{row.son_net}")'))==0 , axis=1)
                return len(net_df[net_df.leaf].query('son_direction=="out"').index)
            multi_drive_df['number_of_drivers']=[driver_num(multi_drive_df.index[i]) for i in range(len(multi_drive_df.index))]
            multi_drive_df=multi_drive_df.query('number_of_drivers>1')
            return multi_drive_df.drop_duplicates()
        #multi_drive_df=get_multi_drive_df()
        #if not multi_drive_df.empty:
        #    st.header('Multi Drivers on "real" net : ')
        #    st.write(multi_drive_df[columns2view])


st.write('Done')



