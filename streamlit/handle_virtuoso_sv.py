import pandas as pd
import os
import streamlit as st
import re
from os.path import join
from os.path import isdir

project_list=['BRK2_TC2','BRK2_A0','FLC_TC2_N3']
block_name_dict={'BRK2_TC2':'brk2_tc2_ti','BRK2_A0':'brk2_a0','FLC_TC2_N3':'Unknown'}
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

def get_file_timestamp(f):
    import os
    if not len(f):
        return 0
    try:
        return os.path.getmtime(f)
    except:
        st.error(f'cannot run os.path.getmtime on "{f}"')
        return 0
def timestamp_to_date(timestamp):
    import datetime
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d-%H:%M')

st.header('handle virtuoso sv view')
st.write('help: at first round we will just update all the leafs that are at virtuosu, therfor at the first round we will leave "block name" empty, run p4 update by this tool and get the list of leafs that are different between WS and virtuoso. we will put this list at "block name" and run co chmod and meld, then ci. at meld you can update the changes that you want and hit save.')
st.subheader('co/ci sv views at virtuoso brk2 db and compare to local bmods folder')
#blocks = st.text_area('blocks name (if you leave empty and give it local folder, it will find all differ files)' , 'ipn5adcsarshr_dacsw_1f,ipn5adcsarshr_dacsw_hf,ipn5adcsarshr_dfx_n_mos1_switch,ipn5adcsarshr_dfx_p_mos1_switch')
#local_sv_vs_library_manager_compare_mode=True#bool(len(local_folder))
local_folder = st.sidebar.text_input('BMOD Folder ($WS...)', '/nfs/iil/disks/falcon_tc2-rtl/TC2/users/yehudabe/work/analog_sa/src/bmod/lane_top/lane_top_n3_0p5/')
ws_name = st.sidebar.text_input('virtuoso workspace path ($WORAREA)','/nfs/iil/disks/hip_ana_users_03/yehudabe/flc_n3')
#username = st.sidebar.text_input('username','lisrael1')
project = st.sidebar.selectbox("Choose Project",project_list,index=2)
check_only_modified=st.sidebar.checkbox('Check only modified blocks', value=False)
#diskname = st.sidebar.selectbox('disk',['hip_ana_users_01','hip_ana_users_02','hip_ana_users_03','hip_ana_users_04'])
diskname = 'hip_ana_users_0[1-4]'
local_folder = re.sub('[;&:=$()%!^~`\n]','', local_folder)
st.sidebar.code('virtuoso path for example /nfs/iil/disks/hip_ana_users_04/lisrael1/barak_gen2_n5/lisrael1.default/ams.gen2_tc/.block\nyou can see lisrael1.default which is username.workspace')
cmd='ls '+local_folder+'''/*.sv| awk -F '[/.]' '{printf $(NF-1)","}' '''
blocks=os.popen(cmd).read().split('\n')
blocks=blocks[0]
with st.beta_expander('analysing blocks'):
    os.popen('ls /nfs/iil/disks/hip_ana_users_0{1,2,3,4} -d').read()  # sometimes you cannot see the disks untill you call then directly 
    # you have 3 places that your sv file can be - n5shared barak_gen2 and falcon, but we will run ls and find which one we have
    # p4_path+=p4_path.replace('n5shared','barak_gen2')+p4_path.replace('n5shared','falcon')
    if (project=='FLC_TC2_N3'):
        view='verilog' if isdir(ws_name+'/soswa/lib_data/{lib}/{b_name}/verilog/') else 'systemVerilog'
        virtuoso_nfs_path=ws_name+'/soswa/lib_data/{lib}/{b_name}/*erilog/verilog.*v'
        p4_path=ws_name+'/soswa/lib_data/{lib}/{b_name}/*erilog'
    else:
        virtuoso_nfs_path= ws_name+'/ams.{blockname}/.block/barak2.*-{lib}/cdn/{lib}/{b_name}/systemVerilog/verilog.sv'
        p4_path='//barak2/brk2_tc2/A/{lib}/cdn/{lib}/{b_name}/systemVerilog/... '
    virtuoso_nfs_path = re.sub('[;&:=$()%!^~`\n]','', virtuoso_nfs_path)

    # now we will create command to check them out / in 
    if blocks.replace(" ","").replace(",","")=="":
        cmd='ls '+local_folder+'''/*.sv| awk -F '[/.]' '{printf $(NF-1)","}' '''
        blocks=os.popen(cmd).read().split('\n')
        blocks=blocks[0]
    df=pd.DataFrame(blocks.replace(" ","").split(','), columns=['sv_name']).drop_duplicates()
    df['b_name']=df.sv_name.str.split('.').str[0]
    df['lib']=df.sv_name.str.split('_').str[0]
    df['blockname']=block_name_dict[project]
    df['all_options_virtuoso_nfs_path']=df.apply(lambda r: virtuoso_nfs_path.format(**r), axis=1)
    df['virtuoso_nfs_path']=('ls '+df.all_options_virtuoso_nfs_path).apply(lambda r:os.popen(r).read().rstrip('\n'))#.replace(username,'${USER}')

    df['virtuoso_file_timestamp'] = df.virtuoso_nfs_path.apply(get_file_timestamp)
    df['virtuoso_file_date'] = df.virtuoso_file_timestamp.apply(timestamp_to_date)
    #if local_sv_vs_library_manager_compare_mode:
    df['local_file_timestamp'] = (local_folder+'/'+df.sv_name+'.sv').apply(get_file_timestamp)
    df['local_file_date'] = df.local_file_timestamp.apply(timestamp_to_date)

    #if local_sv_vs_library_manager_compare_mode:
    st.write(f'all parsed block from {local_folder}:')
    #else:
    #    st.write(f'all parsed block at virtuoso by given block names:')
    st.write(df)


# dropping blocks that doesn't have sv view
blocks_that_dont_have_sv_view_at_virtuoso=df.query('virtuoso_nfs_path==""').b_name
if df.query('virtuoso_nfs_path!=""').empty:
    st.error('no files found under the username and virtuoso work directory. check user name and workspace name')
    st.code(('ls '+df.all_options_virtuoso_nfs_path).add('\n').sum())
    st.write(df)
    
df=df.query('virtuoso_nfs_path!=""')

df['project']=project#df.virtuoso_nfs_path.str.split('block/barak2.').str[1].str.split('-').str[0]
df.apply(lambda r:p4_path.format(**r), axis=1)
df['p4_path']=df.apply(lambda r:p4_path.format(**r), axis=1)

if project =='FLC_TC2_N3':
    df['p4_co']="soscmd co "+df.p4_path
    df['p4_update']="soscmd updatesel "+df.p4_path
    df['p4_ci']='soscmd ci -aLog="Virtuoso AV sync" '+df.p4_path
else:    
    df['p4_co']="p4 edit "+df.p4_path
    df['p4_update']="p4 update "+df.p4_path
    df['p4_ci']="p4 submit -d 'SCH_WIP' "+df.p4_path
df['check_and_save']=df.apply(lambda r:f'_teHDLExtractLCV("{r.lib}" "{r.b_name}" "systemVerilog")', axis=1)

#p4_co='p4 edit '+df.p4_path.add(' ').sum()
#p4_update='p4 update '+df.p4_path.add(' ').sum()

if not blocks_that_dont_have_sv_view_at_virtuoso.empty:
    st.write('next blocks doesnt have sv view at the given virtuoso path')
    st.write(blocks_that_dont_have_sv_view_at_virtuoso)
# you cannot run multi files at the same command (but you can for co)
# p4_ci="p4 submit -d 'SCH_WIP' "+df.p4_path.add(' \\\n').sum()


#droping blocks thet havnt changed since the release
if check_only_modified:
    first_date=df.local_file_date.tolist()
    first_date.sort()
    first_date=first_date[0]
    st.write(f'Assumig {first_date} as date of release')
    df=df.query(f'local_file_date!="{first_date}"')



















local_folder_cmd=f'ls -d {local_folder}>/dev/null; echo $?'
local_folder_exist=os.popen(local_folder_cmd).read().split('\n')
local_folder_exist=local_folder_exist[0]=='0'
if local_folder_exist and local_folder.startswith('/'):
    st.header('local files that are not as the version at the db')
    cmd=df.apply(lambda r:f'diff -q {r.all_options_virtuoso_nfs_path} {local_folder}/{r.b_name}.*v', axis=1).add('\n').sum()
    cmd_out=os.popen(cmd).read().split('\n')
    try:
        cmd_out=[b.rsplit('.', 1)[0].rsplit('/', 1)[1] for b in cmd_out if "diff: Try " not in b and "missing operand after" not in b and len(b.rsplit('.', 1)[0].rsplit('/', 1))>1]
    except:
        st.write('******** found error in the script ********')
        st.code(cmd)
        st.write(str(cmd_out))
    df['local_file_differ_from_db']=df.eval(f'b_name in {cmd_out}')
    df.local_file_differ_from_db=df.local_file_differ_from_db.fillna(False)
    if df.local_file_differ_from_db.sum():
        st.write('list of blocks that differ (you can copy them and put at the first input box and rerun this script):')
        st.write(df.query(f'b_name in {cmd_out}').b_name.add(', ').sum()[:-2])
        block_to_show = st.multiselect('show specific blocks', options = df.sv_name)
        if len(block_to_show):
            st.write(df.query(f'sv_name in {block_to_show}').T)
        else:
            st.write(df)
        st.write('\nyou can run meld to compare the diff files:')
        st.markdown(get_table_download_link(df), unsafe_allow_html=True)
        st.code('meld '+df.query(f'b_name in {cmd_out}').apply(lambda r:f'--diff {r.all_options_virtuoso_nfs_path} {local_folder}/{r.b_name}.*v', axis=1).add(' ').sum()[:-1])
    st.write()
    st.warning(f'''{df.query(f'b_name in {cmd_out}').shape[0]} differ files out of {df.shape[0]}''')
    st.write('note that files that doesnt exist will not count as differ ones')

df=df[df.local_file_differ_from_db]
if df.empty:
    st.subheader('No diff block found') 
    st.stop()
splited_p4_file_path=df.p4_path.add(' ').sum().replace('  ',' ')[:-1]
with st.beta_expander('update'):
    st.code(df.p4_update.add('\n').sum())

with st.beta_expander('co'):
    st.code(df.p4_co.add('\n').sum())
with st.beta_expander('undo co to all unchanged files'):
    st.code("p4 revert -a //barak2/...")
with st.beta_expander('list of co sv views'):
    st.code('''p4 opened -a //barak2/... | grep $USER | grep -w verilog | awk '{print $1}' | sort -u | awk -F '/' '{printf $(NF-2)","}' ''')

with st.beta_expander('chmod'):
    st.code("chmod u+w "+df.virtuoso_nfs_path.add(' ').sum())

with st.beta_expander('check and save at virtuoso terminal'):
    st.info('but first change default check in/out to be automatically. you can run it by saving those lines into file, then load("<file>") at virtuoso terminal')
    st.code(df.check_and_save.add('\n').sum())

with st.beta_expander('ci'):
    st.code(df.p4_ci.add('\n').sum())
# command='p4 submit -d "SCH_WIP" '
# st.write(command+splited_p4_file_path.replace(' ','\n'+command))


with st.beta_expander('gvim'):
    # st.write("gvim -p "+df.virtuoso_nfs_path.add(' \\\n').sum())
    st.code("gvim -p "+df.virtuoso_nfs_path.add(' ').sum())
with st.beta_expander('compile virtuoso sv files'):
    vcs_command = "vcs -sverilog -lca -timescale=1ns/1ns +error+1000 /p/hdk/cad/vcsmx/P-2019.06-SP2-3/etc/snps_msv/snps_msv_nettype_pkg.svp /nfs/iil/disks/ams_regruns/dkl/users/lisrael1/msv/temp_del/verilog_helper/extra_verilogs/importing_wrealsum.v "
    st.code(vcs_command+df.virtuoso_nfs_path.add(' ').sum())
    st.code((vcs_command+df.virtuoso_nfs_path).add('\n').sum())

with st.beta_expander('extra'):
    st.write('\nyou can get the list of checked out files:')
    st.code('''p4 opened -a | grep -i verilog.sv | grep $USER | awk -F '/' '{print $9" @ "$8}' | sort -u''')



