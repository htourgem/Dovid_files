# if you have raw data that you want to upload, not link to file, you can use simple_art_uploader.py

def raw_data_from_logs_to_art(logs_path_with_asterisk, user, dct, session_name='my_session', hidden_dict={}, project_name='Falcon', project_step='TC2', log_type='msv', how_many_samples_to_upload=0, how_many_samples_to_drop=0, take_from_begining_of_log=True, which_place_at_msv_report=None):
    from glob import glob
    from natsort import natsorted
    from tqdm import tqdm
    import pandas as pd
    from copy import deepcopy
    import sys
    sys.path.append('/nfs/iil/disks/hip_ana_sim_01/dgottesm/analysis_and_tools/analysisPP/brk_gen1/Automation/PostProcess/upload_to_art')
    from simple_art_uploader import simple_art_dict, upload_to_ogre
    from parse_msv_report import msv_report_lines_to_df
    import parse_virtuoso_csv_scs

    list_of_art_dicts_to_upload = []
    list_of_files = logs_path_with_asterisk.replace(' ','').replace('\t','')
    print(list_of_files)
    list_of_files = glob(list_of_files)
    print(list_of_files)
    list_of_files = natsorted(list_of_files)
    print(list_of_files)
    if not len(list_of_files):
        print('didnt find files by %s. exit' % logs_path_with_asterisk)
        return
    else:
        if log_type == 'msv log' and which_place_at_msv_report == 'raw':
            print('if you choose msv log type, you should set which_place_at_msv_report not to raw')
            return
        for f in tqdm(list_of_files):
            CornerData=dict()
            test_input_dct = deepcopy(dct)
            
            print('now at file %s' % f)
            try:
                if log_type == 'msv log':
                    df = msv_report_lines_to_df(f)
                    if 'data_type' not in df.columns:
                        print('didnt find rows at the log with data_type value. exit')
                        return
                    if type(which_place_at_msv_report) is str:
                        if "pos_neg_diff" in df.columns:
                            df = df.query('data_type==@which_place_at_msv_report and pos_neg_dif=="d"')
                        else:
                            df = df.query('data_type==@which_place_at_msv_report')
                    df = df.value.to_frame()  # we take only value data, we dont care about the sar/oct number
                if log_type == 'raw data':
                    df = pd.read_csv(f, sep='[\s,]+', engine='python')
                if log_type == 'virtuoso csv':
                    df = pd.read_csv(f, sep='[\s,]+', engine='python')
                    CornerData.update(parse_virtuoso_csv_scs.get_params_from_scs(input_scs_path=f.replace('\\','/').rsplit('/', 1)[0]+'/input.scs'))

                try:
                    print('found %d relevant lines at file %s' % (df.shape[0], f))
                except:
                    print('no df found, talk with lisrael1. log_type=%s'%log_type)
                if take_from_begining_of_log:
                    df = df[how_many_samples_to_drop:]
                    if how_many_samples_to_upload:
                        df = df[:how_many_samples_to_upload - 1]
                else:
                    if how_many_samples_to_drop:
                        df = df[:-how_many_samples_to_drop]
                    if how_many_samples_to_upload:
                        df = df[-how_many_samples_to_upload:]
                print(df)
                print(df.shape)
                if df.shape[1]==1:
                    df.columns=["voltage"]
                else:
                    df.columns=["time","voltage"]
                    hidden_dict["time_vector_hidden"] = df.time.tolist()
                dct_x = dict(rawdata=df.voltage.tolist(), log_path=f)
                if df.shape[1]==2:
                    dct_x["time_vector"] = df.time.tolist()
                print('taking %d lines from file %s' % (df.shape[0], f))
                x_split = logs_path_with_asterisk.split("*")
                prev_len = 0
                card = 0
                ## find wildcard charachters
                for split in x_split:
                    index = f.find(split,prev_len)
                    caught = f[prev_len:index]
                    if caught:
                        dct_x[f"wildcard_var{card}"] = caught
                        if dct_x[f"wildcard_var{card}"].isdigit():
                            dct_x[f"wildcard_var{card}"]=float(dct_x[f"wildcard_var{card}"])
                        card+=1
                    prev_len = prev_len+len(split)+len(caught)
                
                tmp_dct = dict(dct=dct_x, user=user, session_name=session_name, project_name=project_name, hidden_dict=hidden_dict, project_step=project_step)
                tmp_dct['dct'].update(test_input_dct)
                tmp_dct['CornerData'] = CornerData
                list_of_art_dicts_to_upload += [simple_art_dict(**tmp_dct)]
            except Exception as e:
                print('  ***** error - failed to process file %s *****' % (f))
                print(e)
    upload_to_ogre(list_of_art_dicts_to_upload)


if __name__ == '__main__':
    from optparse import OptionParser
    import os
    from sys import platform

    if "win" in platform:
        os.environ["USER"]='lisrael1'

    script_path = os.path.realpath(__file__)
    help_text = """
        you can use this script for uploading brk simulations output into ART
        example:
            /nfs/iil/proj/cto/dav/py3.6.3/bin/python3.6 {script_path} 
        if you want to import it from your script:
                import sys
                sys.path.append('full path where the %prog is, unless your script is next to this script')
                import %prog
                %prog.raw_data_from_logs_to_art(log_path='./log', ...)

        """.format(script_path=script_path)
    parser = OptionParser(usage=help_text, version="%prog 1.01 beta", epilog="good luck!")  # you will see version when adding --version
    parser.add_option("-l", "--log_path", dest="log_path", type="str", help="unix log path [default:%default]", default='/nfs/iil/disks/hdk_ws/ckt/lisrael1/lior_dir/jupyter/upload_to_ART/log_examples/bmods_sine.log')
    parser.add_option("--session_name", dest="session_name", type="str", help="session name [default:%default]", default="session_name")
    parser.add_option("--project_name", dest="project_name", type="str", help="project name [default:%default]", default="BRK_GEN1")
    parser.add_option("--user", dest="user", type="str", help='''your windows username [default:%default]''', default=os.environ["USER"])
    parser.add_option("--first_dict", dest="first_dict", type="str", help='''extra columns at ART. you can write for example "{'freq_GHz':1.5, 'train_freq_GHz':1.7}" [default:%default]''', default='''{}''')
    parser.add_option("--hidden_dict", dest="hidden_dict", type="str", help='''extra hidden columns at ART [default:%default]''', default='{}')
    parser.add_option("--log_type", dest="log_type", type="str", help='''can be 'msv log', 'raw data' 'virtuoso csv' [default:%default]''', default='raw data')
    parser.add_option("--how_many_samples_to_upload", dest="how_many_samples_to_upload", type="int", help=''' [default:%default]''', default=0)
    parser.add_option("--how_many_samples_to_drop", dest="how_many_samples_to_drop", type="int", help=''' [default:%default]''', default=0)
    parser.add_option("--take_from_begining_of_log", dest="take_from_begining_of_log", action="store_false", help=" [default:%default]", default=True)
    parser.add_option("--which_place_at_msv_report", dest="which_place_at_msv_report", type="str", help='''if using msv report you should enter sampling place [default:%default]''', default='align_output')

    (option, args) = parser.parse_args()
    option.first_dict = eval(option.first_dict)
    option.hidden_dict = eval(option.hidden_dict)
    if 0:
        option.log_path='/nfs/iil/disks/hip_ana_sim_01/yehudabe/barak_gen2_n5/ipn5brk2adctopnonprod/brk2_megabench/maestro/results/maestro/Interactive.357/28/brk2_megabench_sin_sweep/netlist/th2_out_data.csv'
        option.log_type='msv log'
    raw_data_from_logs_to_art(logs_path_with_asterisk=option.log_path, user=option.user, dct=option.first_dict, session_name=option.session_name, project_name=option.project_name,
                              hidden_dict=option.hidden_dict, log_type=option.log_type, how_many_samples_to_upload=option.how_many_samples_to_upload, how_many_samples_to_drop=option.how_many_samples_to_drop, take_from_begining_of_log=option.take_from_begining_of_log, which_place_at_msv_report=option.which_place_at_msv_report)
