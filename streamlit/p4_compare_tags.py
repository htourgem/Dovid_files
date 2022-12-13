import pandas as pd
pd.options.display.max_rows=200
import streamlit as st
import subprocess
import marshal
import base64

st.header('compare block versions in different tags')

# /nfs/iil/proj/mig_pde/cheetah/mig_n5_compare_labels.sh
output_folder='/nfs/iil/disks/ams_regruns/dkl/users/lisrael1/msv/temp_del/verilog_tmp/p4_compare_tags/list_of_blocks/'
client='iil:lisrael1:e039b3fb9db4738ff81a240e2564dbdbaec65b22:amsbase_A:gen2_tc'
port='ssl:p4brk2idce.sync.intel.com:7070'
list_of_relevant_blocks = output_folder+'/brk2_cell_list.txt'
list_of_relevant_blocks = output_folder+'/flc_cell_list.txt'
# the script that generates this list_of_relevant_blocks is /nfs/iil/disks/ams_regruns/dkl/users/lisrael1/msv/temp_del/verilog_tmp/p4_compare_tags/list_of_blocks/get_list_of_blocks_from_latest.sh

st.write('showing only blocks that are at the list at '+list_of_relevant_blocks.replace("verilog_tmp"," ->\nverilog_tmp"))


file_type=['sch.oa','symbol.oa']
cells=pd.Series(open(list_of_relevant_blocks).read().split('\n'))  # list of blocks ipn5adcrefgenshr_mux\nipn5adcrefgenshr_plus_one\n...

f=open(f'{output_folder}/p4_tags_compare_dates.txt','a')
f.write(pd.datetime.now().strftime('%d-%m-%Y-%H:%M:%S\n'))
f.close()

def running_timer(p, text):
    class timer:
        def __init__(self):
            import time
            self.time=time
            self.start = time.time()  # you can also use time.perf_counter() instead, might be more accurate. return float seconds
        def current(self):
            return f"{self.time.time() - self.start:.2f} sec"

    from time import sleep
    timer_widget = st.empty()
    t = timer()
    # st.write(f'done with exit code {process.wait()}')
    while p.poll() is None:
        sleep(0.1)
        timer_widget.info(f'{text} {t.current()} {p.poll()}')

        
def p4_output_to_df(p4_G_output):
    output_text = st.empty()
    output_text.text('reading marshal files')
    marshal_bin=[b'{s'+i for i in p4_G_output.split(b'{s')[1:]] # first one is empty
    out=[]
    for o in marshal_bin:
        try:
            out+=[marshal.loads(o)]
        except:
            st.write('cannot read %s'%o)
    df=pd.DataFrame(out)
    output_text.text('casting to utf')
    if df.shape[0]<5:
        st.error('df is empty!!')
        st.write(df.head(10))
        st.write(first_label_p4_output)
        return df
    df=df.stack().str.decode('utf-8').unstack()
    df.columns=df.columns.astype(str)
    output_text.text('removing 0 suffix from columns ater filelog -m1 command')
    df.columns=df.columns.to_series().apply(lambda c:c[:-1] if c.endswith('0') else c)  # if we ran filelog -m 1 we will get most columns with 0 suffix (this number says the output line)
    output_text.text('fixing types')
    df.time=pd.to_datetime(df.time, unit='s')
    df[['rev','change','fileSize']]=df[['rev','change','fileSize']].fillna(-1).astype(int)
    output_text.text('extracting block name')
    df[['library','block','block_type','file_name']]=df.depotFile.str.rsplit('/',4, expand=True).drop(0, axis=1)
    df['library_name_from_block_name']=df.block.str.split('_').str[0]
    df=df.query('library==library_name_from_block_name')  # we have a lot of duplications of the same block at some different libraries, but this one is the right one
    output_text.text('dropping and renaming')
    df=df.drop(['action','change','client','code','digest','fileSize','type','library'], axis=1)
    df=df.drop(df.columns[df.columns.str.contains(',')].values, axis=1)
    df=df.rename(columns=dict(desc='comment',depotFile='p4_path', rev='version'))
    if df.empty:
        st.error('df is empty!')
    output_text.text('')
    return df


def get_table_download_link(df):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}" download="abc.csv">Download csv file</a>'
    return href


list_of_labels=subprocess.Popen(f'p4 -p {port} labels'.split(' '),stdout=subprocess.PIPE, stderr=subprocess.PIPE)
error=list_of_labels.stderr.read()
if len(error):
    st.write(error)
list_of_labels=list_of_labels.stdout.read().decode('utf8').split('\n')
list_of_labels=['head','latest']+[i.split(' ')[1] for i in list_of_labels if len(i.split(' '))>1]
# st.write(list_of_labels)

# second_label='@IPN5_BRK2_SCH1.0'
# first_label='@ipn5brk2_SCH_0P8'
st.sidebar.info('type part of the tag name for greping relevant values')
first_label='@'+st.sidebar.selectbox('choose first  tag', list_of_labels)
second_label='@'+st.sidebar.selectbox('choose second tag', list_of_labels)
if first_label=='@head' or first_label=='@latest':
    first_label='#head'
if second_label=='@head' or second_label=='@latest':
    second_label='#head'
st.sidebar.image('/nfs/iil/disks/hip_ana_sim_01/dgottesm/analysis_and_tools/jupyter_notebooks/streamlit/p4_compare.jpg', use_column_width=True)
# st.sidebar.image('/nfs/iil/disks/hip_ana_sim_01/dgottesm/analysis_and_tools/jupyter_notebooks/streamlit/p4_compare.jpg')

if first_label==second_label:
    st.write('first and second labels are the same - please enter differnet tags at the slidebar')
else:
    stam='n5shared/A/ipn5adcsarshr/cdn/ipn5adcsarshr/ipn5adcsarshr_dac_rnor/'
    stam=''
    blocks='barak_gen2,falcon,n5shared'.split(',')
    blocks=' '.join([f"""//barak2/{block}/{stam}...which_label""" for block in blocks])
    ver1=f"""p4 -G -c {client} -p {port} filelog -m 1 -l -t """+blocks.replace('which_label',first_label)
    ver2=f"""p4 -G -c {client} -p {port} filelog -m 1 -l -t """+blocks.replace('which_label',second_label)
    
    replacing = f""" -G -c {client} -p {port}"""
    st.code(f'running p4\n{ver1.replace(replacing,"")}\n{ver2.replace(replacing,"")}')

    first_label_p4_output =subprocess.Popen(ver1.split(' '),stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#     running_timer(first_label_p4_output, 'first_label_p4_output')
    first_label_p4_output=first_label_p4_output.stdout.read()
    second_label_p4_output=subprocess.Popen(ver2.split(' '),stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read()

    st.write('parsing p4 output')
    first_label_p4_output=p4_output_to_df(first_label_p4_output)
    second_label_p4_output=p4_output_to_df(second_label_p4_output)
    
    st.write(f'dropping cells that are not at block list file')
    first_label_p4_output=first_label_p4_output.query(f'block.isin({cells.values.tolist()}) and p4_path.str.contains("/A/ipn5")')
    second_label_p4_output=second_label_p4_output.query(f'block.isin({cells.values.tolist()}) and p4_path.str.contains("/A/ipn5")')

    # st.write(first_label_p4_output.head(1000))
    # st.write(second_label_p4_output.head(1000))



    first_label=first_label.replace('@','').replace('#','')
    second_label=second_label.replace('@','').replace('#','')

    st.write(f'{first_label_p4_output.shape[0]} files in {first_label}')
    st.write(f'{second_label_p4_output.shape[0]} files in {second_label}') 
            
#     st.write('hi')
#     st.write(first_label_p4_output.query('block.str.contains("ipn5brk2ffe_res_p_analog6_vref_inv_v3")'))
#     st.write(second_label_p4_output.query('block.str.contains("ipn5brk2ffe_res_p_analog6_vref_inv_v3")'))
#     first_label_p4_output.to_csv('/nfs/iil/disks/hip_ana_sim_01/dgottesm/analysis_and_tools/jupyter_notebooks/streamlit/a.csv')
#     second_label_p4_output.to_csv('/nfs/iil/disks/hip_ana_sim_01/dgottesm/analysis_and_tools/jupyter_notebooks/streamlit/b.csv')

    # dropping common columns, and taking them from second_label_p4_output
    merge=pd.merge(first_label_p4_output, second_label_p4_output, how='outer', on=['block','block_type','file_name'], suffixes=[f'_{first_label}', f'_{second_label}'])
#     st.write(merge.query('block.str.contains("ipn5brk2ffe_res_p_analog6_vref_inv_v3")==True'))
    merge=merge.query(f'file_name.isin({file_type})')

    merge=merge[merge[f'version_{first_label}']!=merge[f'version_{second_label}']]  #.query(f'`version_{first_label}`!=`version_{second_label}`')
    # sorting values and columns
    merge=merge.sort_values(['file_name','block']).reset_index(drop=True)#.fillna('')
#     merge.filter(regex='^(?!version_)').fillna('', inplace=True)
#     merge[[f'version_{first_label}',f'version_{second_label}']]=merge[[f'version_{first_label}',f'version_{second_label}']].replace('\.0','', regex=True)
    merge=merge[merge.columns.to_series().sort_index().values.tolist()]

    csv_name=f'/nfs/iil/disks/ams_regruns/dkl/users/lisrael1/msv/temp_del/verilog_tmp/p4_compare_first_label_p4_outputs_{first_label}_{second_label}.csv'
    merge.to_csv(csv_name)
    st.write(f'found {merge.shape[0]} diff files at shcematice and symbol')
    block_to_show = st.selectbox('you can show only specific block',['all']+merge.block.unique().tolist())
#     st.write(merge.query('block=="ipn5adcsarshr_slicer"'))
    if block_to_show=='all':
        st.write(merge.head(1000))
    else:
        st.write(merge.query(f'block=="{block_to_show}"').head(1000))
    st.markdown(get_table_download_link(merge), unsafe_allow_html=True)
    st.code('you can also take this table from here:\n'+r'\\isamba.iil.intel.com'+f'{csv_name}'.replace('/','\\'))
    st.balloons()
