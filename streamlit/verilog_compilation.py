import os, subprocess
from glob import glob
import streamlit as st
import datetime
import re
from time import sleep
import sys, os
repo_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class timer:
    def __init__(self):
        import time
        self.time=time
        self.start = time.time()  # you can also use time.perf_counter() instead, might be more accurate. return float seconds
    def current(self):
        return f"{self.time.time() - self.start:.2f} sec"



st.header('check if bmods compiles')
st.sidebar.markdown('**verilog compilation**')
st.sidebar.image(repo_path + '/streamlit/verilog_compilation.jpg', use_column_width=True)
simulate = st.sidebar.checkbox('also simulate')

verilog_std_folder = glob('/nfs/iil/disks/ams_regruns/dkl/users/lisrael1/msv/temp_del/verilog_helper/std/*')
verilog_std_folder = st.sidebar.selectbox('choose std folder', [i.rsplit('/', 1)[-1] for i in verilog_std_folder])
verilog_std = glob(f'/nfs/iil/disks/ams_regruns/dkl/users/lisrael1/msv/temp_del/verilog_helper/std/{verilog_std_folder}/*')
verilog_std = '-v ' + ' \\\n-v '.join(verilog_std)




def paths():
    p = []
    st.success(f'enter full path of a verilog folder or verilog file')
    i=0
    while True:
        i+=1
        user_input = st.text_area(f'verilog file/folder full path {i}' , key=i).replace('\n','')
        if user_input=="":
            break
        if os.path.isdir(user_input) or os.path.isfile(user_input):
            p.append(user_input)
        else:
            st.error(f'cannot find path')
    return p

verilog_folders = set(paths())
extra_compilation_content = st.text_input('extra vcs flags like pvalue and defines:')

if not len(verilog_folders):
    st.error('no valid input folder')
    st.stop()
    
verilog_files=[]
for f in verilog_folders:
    verilog_files+=glob(f'{f}/*.sv')+glob(f'{f}/*.v')
    if f.endswith('.sv') or f.endswith('.v'):
        verilog_files+=glob(f)
if 0:  # no need, we override the $system with c function that doesnt do anything
    for v in verilog_files:
        if os.path.isfile(v):
            if re.search('\$system',open(v,'r').read()):
                assert False, f'cannot compile this verilog! {v}'
verilog_files=' \\\n'.join(verilog_files)


current_date = datetime.datetime.now().strftime('%d-%m-%Y-%H.%M.%S')
working_directory = f'/nfs/iil/disks/ams_regruns/dkl/users/lisrael1/msv/temp_del/verilog_helper/compilation_output/sim_{current_date}/'
os.makedirs(working_directory,exist_ok=True)
os.chmod(working_directory, 0o770)


with open(f'{working_directory}/user_selections.txt', 'w') as f:
    f.write('verilog folder:\n')
    f.write('\n'.join(verilog_folders))
    f.write('\n\nstd folder name:\n')
    f.write(verilog_std_folder)
    f.write('\n\nverilog files:\n')
    f.write(verilog_files+'\n')
    
with open(f'{working_directory}/v_files.txt', 'w') as f:
    f.write(verilog_files.replace(' \\\n','\n'))
elaboration_content=f'''-sverilog -lca -timescale=1fs/1fs \\
+error+10000 +lint=PCWM +lint=TFIPC-L \\
/p/hdk/cad/vcsmx/P-2019.06-SP2-3/etc/snps_msv/snps_msv_nettype_pkg.svp \\
/nfs/iil/disks/ams_regruns/dkl/users/lisrael1/msv/temp_del/verilog_helper/importing_wrealsum.v \\
/nfs/iil/disks/ams_regruns/dkl/users/lisrael1/msv/temp_del/verilog_helper/no_system.c \\
/nfs/iil/disks/ams_regruns/dkl/users/lisrael1/msv/temp_del/verilog_helper/no_system.sv \\
-P /nfs/iil/disks/ams_regruns/dkl/users/lisrael1/msv/temp_del/verilog_helper/no_system.tab \\
-f {working_directory}/v_files.txt \\
{verilog_std} \\
'''

vcs_command = f'''
# setting vcs setup
setenv SNPSLMD_LICENSE_FILE 26586@synopsys11p.elic.intel.com:26586@synopsys09p.elic.intel.com:26586@synopsys01p.elic.intel.com:26586@synopsys03p.elic.intel.com:26586@synopsys21p.elic.intel.com:26586@synopsys22p.elic.intel.com:26586@synopsys23p.elic.intel.com:26586@synopsys11p.elic.intel.com:26586@synopsys09p.elic.intel.com:26586@synopsys01p.elic.intel.com:26586@synopsys03p.elic.intel.com:26586@synopsys21p.elic.intel.com:26586@synopsys22p.elic.intel.com:26586@synopsys23p.elic.intel.com

setenv VCS_HOME /p/hdk/cad/vcsmx/O-2018.09-SP2-5
setenv VCS_HOME /p/hdk/cad/vcsmx/P-2019.06-SP2-3
setenv SYNOPSYS_SIM_SETUP /p/hdk/cad/vcsmx/O-2018.09-SP2-5/bin/synopsys_sim.setup
unsetenv SYNOPSYS_SIM_SETUP
setenv XA_64 1

setenv PATH "$VCS_HOME/bin:$PATH"

# creating running directory
cd {working_directory}
echo 'staring vcs' > {working_directory}/log.txt
chmod og+rx {working_directory}/log.txt

# running vcs
vcs {elaboration_content} \\
{"-R -debug_all" if simulate else ""}\\
{extra_compilation_content} \\
>>&{working_directory}/log.txt
grep -P 'Error|Warning|Lint' {working_directory}/log.txt| sort | uniq -c |sort -rn >& {working_directory}/errors_summary.txt
cd -
'''

# here we run vlogan twice. vlogan itself takes about 8 seconds as it reads a lot of std files. if you want to run vcs after vlogan, you have to add -top and you dont know what's the top name, so you cannot use this
splitted_vlogan_vcs='''
# running vcs
(banner vlogan && vlogan {elaboration_content} && \
banner vcs && vcs {elaboration_content} \\
{"-R -debug_all" if simulate else ""}\\
)>>&{working_directory}/log.txt
'''

command_file = open(f'{working_directory}/run_me.sh','w')
command_file.write(vcs_command)
command_file.close()
st.write(f'saving shell command file to ')
st.write(f'{working_directory}/run_me.sh')
st.write('log at')
st.write(f'{working_directory}/log.txt')
st.sidebar.code(vcs_command)

# no need - i override the $system with empty c function. cmd = f'''echo 'msv_scripts_pw' | su msv_scripts -c 'tcsh {working_directory}/run_me.sh' '''
cmd = f'''tcsh {working_directory}/run_me.sh'''
process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
st.write(f'running... for reading status run')
st.code(f'less +F {working_directory}/log.txt')

timer_widget = st.empty()
t = timer()
# st.write(f'done with exit code {process.wait()}')
while process.poll() is None:
    sleep(0.1)
    timer_widget.info(f'compilation time {t.current()}')


st.subheader('errors summary')
errors = f'''grep -P 'Error|Warning|Lint' {working_directory}/log.txt| sort | uniq -c |sort -rn'''
st.code(errors)
st.code(open(f'{working_directory}/errors_summary.txt', 'r').read())
missing_blocks_cmd=f'''grep URMI -A 2 {working_directory}/log.txt | grep -Pv 'Error|--' | tr -d ',"' | awk '{{print $1}}' | paste - - | grep -oP '/[^/]+\s\S+$' | uniq -c | sort -nr | column -t'''
missing_blocks = subprocess.Popen(missing_blocks_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).stdout.read()
if len(missing_blocks):
    st.write('missing blocks')
    st.code(missing_blocks_cmd)
    st.code(missing_blocks.decode())
# st.warning('if you have permissions error you need to move the netlister output folder from n5 to non n5')
