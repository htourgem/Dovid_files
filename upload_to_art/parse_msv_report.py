#!/nfs/iil/proj/cto/dav/py3.6.3/bin/python3.6
# for debug, run this script in pycharm
# import sys
# sys.path.append('/nfs/iil/disks/hip_ana_sim_01/dgottesm/analysis_and_tools/analysisPP/brk_gen1/Automation/PostProcess/upload_to_art/')
# from parse_msv_report import msv_report_lines_to_df, parse_oct_sar_place, msv_sniffers_time_ns_cursur_in_log

# coloring print
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
col=dict(wrn=bcolors.WARNING, norm=bcolors.ENDC, ok=bcolors.OKGREEN, hd=bcolors.HEADER, bld=bcolors.BOLD, ul=bcolors.UNDERLINE, blue=bcolors.OKBLUE)


def header(text):
    print("{blue}{bld}{ul}{txt}{norm}".format(**col,txt=text))

def msv_report_lines_to_df(log_path, max_lines_from_tail='1M'):
    ''' looking for lines like <MSV_REPORT_HASH>{'printer':'MSV_REPORT_DATA_PATH_MONITOR','data_type':'align_output','place':'tb.top.adctop_bmod_sniffer.MSV_REPORT_HASH.unnamed$$_0.MSV_REPORT_HASH_0','pos_neg_dif':'d','value':5,'time_ns':1681.778970,'read_number':4736}</MSV_REPORT_HASH>
    and also th1_output, registers values or whatever wrapped with MSV_REPORT_HASH
    returning content as df
    '''
    import json
    import pandas as pd
    from tqdm import tqdm
    import os
    import re
    
    pd.set_option("display.max_columns",1000) # don’t put … instead of multi columns
    pd.set_option('expand_frame_repr',False) # for not wrapping columns if you have many
    pd.set_option("display.max_rows",100)
    pd.set_option('display.max_colwidth',1000)
    '''
    # if you're sure you dont have bad json lines, you can run this and you will not get exceptions:
    
    # if you get this error:
    # JSONDecodeError: Expecting value: line 1 column 102752 (char 102751)
    # it's because you have non dictionary conctent, and you can see it by:
    #      c=102751
    #      addition=10
    #      table[0][:-1][c-addition:c+addition]
    # if you get:
    # JSONDecodeError: Unterminated string starting at: line 1 column 13956729 (char 13956728)
    # it probably says that the simulation is stil running and you read a line in the middle of writing

    table=!cat $sim_log|grep MSV_REPORT_|sed 's@<MSV_REPORT_HASH>@@'|sed 's@</MSV_REPORT_HASH>@,@'|tr -d '\n'
    js="["+table[0][:-1].replace("'", '"')+"]"
    j = json.loads(js)
    df_all=pd.DataFrame(j)
    print(df_all.data_type.unique())
    df_all.head()
    '''
    l=[]
    # this command will cast the msv log into list of dictionaries
    # the -o is for taking specific pattern from inside the row, becuase sometimes we get some extra strings in this row
    log_path=re.sub('[;&:=$()%!^~`\n]','',log_path)
    file_size_gb=os.path.getsize(log_path)*1e-9
    if file_size_gb>1:
        print('file is too big (about %f GB), taking only last %s lines'%(file_size_gb,max_lines_from_tail))
        command='''tac {}|head -n {}|tac'''.format(log_path,max_lines_from_tail)
        command='''tail -n {} {}'''.format(max_lines_from_tail, log_path)
    else:
        command='''grep MSV_REPORT_ "{}"'''.format(log_path)
    command+='''|grep -o '<MSV_REPORT_HASH>.*</MSV_REPORT_HASH>'|sed 's@<MSV_REPORT_HASH>@@;s@</MSV_REPORT_HASH>@,@' '''
    print('reading file, grepping MSV_REPORT. running '+command)
    table = os.popen(command).read().split(',\n')
    if table[-1]=='':  # last split can be empty because the last line might end with ,\n
        table=table[:-1]
    print('found %d lines'%len(table))
    print('parsing relevant lines into python dictionary')
    for js in tqdm(table):
        try:
            js_replace = js.replace("'", '"')
        except:
            print('cannot replace %s'%js)
        try:
            l+=[json.loads(js_replace)]
        except:
            print('cannot read %s'%js_replace)
    df=pd.DataFrame(l)
    print('taking %d lines'%df.shape[0])
    return df


def parse_oct_sar_place(sr_place):
    '''
    getting series of sniffer place, like
        tb.top.adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.unnamed$$_0.MSV_REPORT_HASH_sar_02_
        tb.top.sar_array.sararray_ch_all_sars.q3_qrts.octet0.qrt1.sar3.isniffer.unnamed$$_0
        tb.top.adc_fe.qrt1.bmod_sniffer.th1_sniffer_0
        tb.top.sar_array.sararray_ch_all_sars.q2_qrts.octet1.qrt1.sar3.isniffer
    you can run df=df.join(parse_oct_sar_place(df.place))
    '''
    import pandas as pd
    if not type(sr_place) is pd.Series:
        print('sr_place should be pd.Series. exit()')
        return
    sar_path=path_parsing_dictionary()
    sr_place=sr_place.copy()
    sr_place_original=sr_place.copy()
    df=sr_place.drop_duplicates(keep='first').to_frame('place')
    df['sar_number'],df['oct_number']=-1,-1
    df['parsed_place']=df.place.str.lower().replace(sar_path, regex=True)
    df.update(df.parsed_place.str.extract('sar_(?P<sar_number>[\d-]+)_oct_(?P<oct_number>[\d-]+);').dropna().astype(int))
    df[['sar_number','oct_number']]=df[['sar_number','oct_number']].astype(int)
    # now return df to the original size, and remove the place column that we got
    df=df.set_index('place').reindex(sr_place_original.values).reset_index(drop=False).drop('place', axis=1)
    df.index=sr_place_original.index
    return df # then you can run df=df.join(parse_oct_sar_place(df.place))



def path_parsing_dictionary():
    import pandas as pd
    import io
    sar_path='''dve_path,sar_number
sar output,
*sararray_ch_all_sars.q0_qrts.octet0.qrt0.sar0*,sar_00_oct_00;
*sararray_ch_all_sars.q1_qrts.octet0.qrt0.sar0*,sar_01_oct_01;
*sararray_ch_all_sars.q2_qrts.octet0.qrt0.sar0*,sar_02_oct_02;
*sararray_ch_all_sars.q3_qrts.octet0.qrt0.sar0*,sar_03_oct_03;
*sararray_ch_all_sars.q0_qrts.octet1.qrt0.sar0*,sar_04_oct_04;
*sararray_ch_all_sars.q1_qrts.octet1.qrt0.sar0*,sar_05_oct_05;
*sararray_ch_all_sars.q2_qrts.octet1.qrt0.sar0*,sar_06_oct_06;
*sararray_ch_all_sars.q3_qrts.octet1.qrt0.sar0*,sar_07_oct_07;
*sararray_ch_all_sars.q0_qrts.octet1.qrt1.sar0*,sar_08_oct_08;
*sararray_ch_all_sars.q1_qrts.octet1.qrt1.sar0*,sar_09_oct_09;
*sararray_ch_all_sars.q2_qrts.octet1.qrt1.sar0*,sar_10_oct_10;
*sararray_ch_all_sars.q3_qrts.octet1.qrt1.sar0*,sar_11_oct_11;
*sararray_ch_all_sars.q0_qrts.octet0.qrt1.sar0*,sar_12_oct_12;
*sararray_ch_all_sars.q1_qrts.octet0.qrt1.sar0*,sar_13_oct_13;
*sararray_ch_all_sars.q2_qrts.octet0.qrt1.sar0*,sar_14_oct_14;
*sararray_ch_all_sars.q3_qrts.octet0.qrt1.sar0*,sar_15_oct_15;
*sararray_ch_all_sars.q0_qrts.octet0.qrt0.sar1*,sar_16_oct_00;
*sararray_ch_all_sars.q1_qrts.octet0.qrt0.sar1*,sar_17_oct_01;
*sararray_ch_all_sars.q2_qrts.octet0.qrt0.sar1*,sar_18_oct_02;
*sararray_ch_all_sars.q3_qrts.octet0.qrt0.sar1*,sar_19_oct_03;
*sararray_ch_all_sars.q0_qrts.octet1.qrt0.sar1*,sar_20_oct_04;
*sararray_ch_all_sars.q1_qrts.octet1.qrt0.sar1*,sar_21_oct_05;
*sararray_ch_all_sars.q2_qrts.octet1.qrt0.sar1*,sar_22_oct_06;
*sararray_ch_all_sars.q3_qrts.octet1.qrt0.sar1*,sar_23_oct_07;
*sararray_ch_all_sars.q0_qrts.octet1.qrt1.sar1*,sar_24_oct_08;
*sararray_ch_all_sars.q1_qrts.octet1.qrt1.sar1*,sar_25_oct_09;
*sararray_ch_all_sars.q2_qrts.octet1.qrt1.sar1*,sar_26_oct_10;
*sararray_ch_all_sars.q3_qrts.octet1.qrt1.sar1*,sar_27_oct_11;
*sararray_ch_all_sars.q0_qrts.octet0.qrt1.sar1*,sar_28_oct_12;
*sararray_ch_all_sars.q1_qrts.octet0.qrt1.sar1*,sar_29_oct_13;
*sararray_ch_all_sars.q2_qrts.octet0.qrt1.sar1*,sar_30_oct_14;
*sararray_ch_all_sars.q3_qrts.octet0.qrt1.sar1*,sar_31_oct_15;
*sararray_ch_all_sars.q0_qrts.octet0.qrt0.sar2*,sar_32_oct_00;
*sararray_ch_all_sars.q1_qrts.octet0.qrt0.sar2*,sar_33_oct_01;
*sararray_ch_all_sars.q2_qrts.octet0.qrt0.sar2*,sar_34_oct_02;
*sararray_ch_all_sars.q3_qrts.octet0.qrt0.sar2*,sar_35_oct_03;
*sararray_ch_all_sars.q0_qrts.octet1.qrt0.sar2*,sar_36_oct_04;
*sararray_ch_all_sars.q1_qrts.octet1.qrt0.sar2*,sar_37_oct_05;
*sararray_ch_all_sars.q2_qrts.octet1.qrt0.sar2*,sar_38_oct_06;
*sararray_ch_all_sars.q3_qrts.octet1.qrt0.sar2*,sar_39_oct_07;
*sararray_ch_all_sars.q0_qrts.octet1.qrt1.sar2*,sar_40_oct_08;
*sararray_ch_all_sars.q1_qrts.octet1.qrt1.sar2*,sar_41_oct_09;
*sararray_ch_all_sars.q2_qrts.octet1.qrt1.sar2*,sar_42_oct_10;
*sararray_ch_all_sars.q3_qrts.octet1.qrt1.sar2*,sar_43_oct_11;
*sararray_ch_all_sars.q0_qrts.octet0.qrt1.sar2*,sar_44_oct_12;
*sararray_ch_all_sars.q1_qrts.octet0.qrt1.sar2*,sar_45_oct_13;
*sararray_ch_all_sars.q2_qrts.octet0.qrt1.sar2*,sar_46_oct_14;
*sararray_ch_all_sars.q3_qrts.octet0.qrt1.sar2*,sar_47_oct_15;
*sararray_ch_all_sars.q0_qrts.octet0.qrt0.sar3*,sar_48_oct_00;
*sararray_ch_all_sars.q1_qrts.octet0.qrt0.sar3*,sar_49_oct_01;
*sararray_ch_all_sars.q2_qrts.octet0.qrt0.sar3*,sar_50_oct_02;
*sararray_ch_all_sars.q3_qrts.octet0.qrt0.sar3*,sar_51_oct_03;
*sararray_ch_all_sars.q0_qrts.octet1.qrt0.sar3*,sar_52_oct_04;
*sararray_ch_all_sars.q1_qrts.octet1.qrt0.sar3*,sar_53_oct_05;
*sararray_ch_all_sars.q2_qrts.octet1.qrt0.sar3*,sar_54_oct_06;
*sararray_ch_all_sars.q3_qrts.octet1.qrt0.sar3*,sar_55_oct_07;
*sararray_ch_all_sars.q0_qrts.octet1.qrt1.sar3*,sar_56_oct_08;
*sararray_ch_all_sars.q1_qrts.octet1.qrt1.sar3*,sar_57_oct_09;
*sararray_ch_all_sars.q2_qrts.octet1.qrt1.sar3*,sar_58_oct_10;
*sararray_ch_all_sars.q3_qrts.octet1.qrt1.sar3*,sar_59_oct_11;
*sararray_ch_all_sars.q0_qrts.octet0.qrt1.sar3*,sar_60_oct_12;
*sararray_ch_all_sars.q1_qrts.octet0.qrt1.sar3*,sar_61_oct_13;
*sararray_ch_all_sars.q2_qrts.octet0.qrt1.sar3*,sar_62_oct_14;
*sararray_ch_all_sars.q3_qrts.octet0.qrt1.sar3*,sar_63_oct_15;
adc top sniffer reading global align output, 
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_00_*,sar_00_oct_00;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_01_*,sar_01_oct_01;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_02_*,sar_02_oct_02;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_03_*,sar_03_oct_03;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_04_*,sar_04_oct_04;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_05_*,sar_05_oct_05;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_06_*,sar_06_oct_06;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_07_*,sar_07_oct_07;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_08_*,sar_08_oct_08;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_09_*,sar_09_oct_09;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_10_*,sar_10_oct_10;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_11_*,sar_11_oct_11;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_12_*,sar_12_oct_12;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_13_*,sar_13_oct_13;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_14_*,sar_14_oct_14;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_15_*,sar_15_oct_15;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_16_*,sar_16_oct_00;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_17_*,sar_17_oct_01;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_18_*,sar_18_oct_02;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_19_*,sar_19_oct_03;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_20_*,sar_20_oct_04;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_21_*,sar_21_oct_05;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_22_*,sar_22_oct_06;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_23_*,sar_23_oct_07;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_24_*,sar_24_oct_08;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_25_*,sar_25_oct_09;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_26_*,sar_26_oct_10;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_27_*,sar_27_oct_11;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_28_*,sar_28_oct_12;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_29_*,sar_29_oct_13;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_30_*,sar_30_oct_14;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_31_*,sar_31_oct_15;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_32_*,sar_32_oct_00;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_33_*,sar_33_oct_01;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_34_*,sar_34_oct_02;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_35_*,sar_35_oct_03;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_36_*,sar_36_oct_04;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_37_*,sar_37_oct_05;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_38_*,sar_38_oct_06;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_39_*,sar_39_oct_07;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_40_*,sar_40_oct_08;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_41_*,sar_41_oct_09;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_42_*,sar_42_oct_10;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_43_*,sar_43_oct_11;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_44_*,sar_44_oct_12;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_45_*,sar_45_oct_13;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_46_*,sar_46_oct_14;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_47_*,sar_47_oct_15;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_48_*,sar_48_oct_00;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_49_*,sar_49_oct_01;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_50_*,sar_50_oct_02;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_51_*,sar_51_oct_03;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_52_*,sar_52_oct_04;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_53_*,sar_53_oct_05;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_54_*,sar_54_oct_06;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_55_*,sar_55_oct_07;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_56_*,sar_56_oct_08;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_57_*,sar_57_oct_09;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_58_*,sar_58_oct_10;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_59_*,sar_59_oct_11;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_60_*,sar_60_oct_12;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_61_*,sar_61_oct_13;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_62_*,sar_62_oct_14;
*adctop_bmod_sniffer.serializer.MSV_REPORT_HASH.*.MSV_REPORT_HASH_sar_63_*,sar_63_oct_15;
th1 old format, 
*ADC_FE.qrt0.pi_th1_ffe_0_.th1_ffe*,sar_-1_oct_00;
*ADC_FE.qrt1.pi_th1_ffe_0_.th1_ffe*,sar_-1_oct_01;
*ADC_FE.qrt2.pi_th1_ffe_0_.th1_ffe*,sar_-1_oct_02;
*ADC_FE.qrt3.pi_th1_ffe_0_.th1_ffe*,sar_-1_oct_03;
*ADC_FE.qrt0.pi_th1_ffe_1_.th1_ffe*,sar_-1_oct_04;
*ADC_FE.qrt1.pi_th1_ffe_1_.th1_ffe*,sar_-1_oct_05;
*ADC_FE.qrt2.pi_th1_ffe_1_.th1_ffe*,sar_-1_oct_06;
*ADC_FE.qrt3.pi_th1_ffe_1_.th1_ffe*,sar_-1_oct_07;
*ADC_FE.qrt0.pi_th1_ffe_2_.th1_ffe*,sar_-1_oct_08;
*ADC_FE.qrt1.pi_th1_ffe_2_.th1_ffe*,sar_-1_oct_09;
*ADC_FE.qrt2.pi_th1_ffe_2_.th1_ffe*,sar_-1_oct_10;
*ADC_FE.qrt3.pi_th1_ffe_2_.th1_ffe*,sar_-1_oct_11;
*ADC_FE.qrt0.pi_th1_ffe_3_.th1_ffe*,sar_-1_oct_12;
*ADC_FE.qrt1.pi_th1_ffe_3_.th1_ffe*,sar_-1_oct_13;
*ADC_FE.qrt2.pi_th1_ffe_3_.th1_ffe*,sar_-1_oct_14;
*ADC_FE.qrt3.pi_th1_ffe_3_.th1_ffe*,sar_-1_oct_15;
th1 new format, 
*ADC_FE.qrt0.bmod_sniffer.th1_sniffer_0*,sar_-1_oct_00;
*ADC_FE.qrt1.bmod_sniffer.th1_sniffer_0*,sar_-1_oct_01;
*ADC_FE.qrt2.bmod_sniffer.th1_sniffer_0*,sar_-1_oct_02;
*ADC_FE.qrt3.bmod_sniffer.th1_sniffer_0*,sar_-1_oct_03;
*ADC_FE.qrt0.bmod_sniffer.th1_sniffer_1*,sar_-1_oct_04;
*ADC_FE.qrt1.bmod_sniffer.th1_sniffer_1*,sar_-1_oct_05;
*ADC_FE.qrt2.bmod_sniffer.th1_sniffer_1*,sar_-1_oct_06;
*ADC_FE.qrt3.bmod_sniffer.th1_sniffer_1*,sar_-1_oct_07;
*ADC_FE.qrt0.bmod_sniffer.th1_sniffer_2*,sar_-1_oct_08;
*ADC_FE.qrt1.bmod_sniffer.th1_sniffer_2*,sar_-1_oct_09;
*ADC_FE.qrt2.bmod_sniffer.th1_sniffer_2*,sar_-1_oct_10;
*ADC_FE.qrt3.bmod_sniffer.th1_sniffer_2*,sar_-1_oct_11;
*ADC_FE.qrt0.bmod_sniffer.th1_sniffer_3*,sar_-1_oct_12;
*ADC_FE.qrt1.bmod_sniffer.th1_sniffer_3*,sar_-1_oct_13;
*ADC_FE.qrt2.bmod_sniffer.th1_sniffer_3*,sar_-1_oct_14;
*ADC_FE.qrt3.bmod_sniffer.th1_sniffer_3*,sar_-1_oct_15;'''.lower().replace('.','\.').replace('*','.*')
    sar_path=pd.read_csv(io.StringIO(sar_path)).set_index('dve_path').sar_number.to_dict()
    #     sar_path={re.compile(k): v for k, v in sar_path.items()}  # not helping! it making it run slower by 30% !!
    return sar_path


def last_time_ns_timestamp(log_path, line_max_size=20000, characters_from_the_end=0):
    import re
    with open(log_path, 'rb') as f:
        f.seek(-characters_from_the_end,2)
        for i in range(100):
            line_max_size = min(line_max_size, f.tell())  # if you want to jump 100 character, but the cursor is at 80, so jump just 80
            # now jump back, read those characters that you jumped back, and look for the pattern
            f.seek(-line_max_size,1)  # if you don’t put 'rb' you cannot put non 0 with second arg with 2 or with 1
            content=f.read(line_max_size).decode('utf-8')
            content = re.findall(r''''time_ns':(?P<time_ns>[\d\.]+)[,}]''', content)
            if len(content):
                return float(content[-1])
            else:
                f.seek(-line_max_size,1)  # jump back the lines that you read
            if f.tell() == 0 :  # got to the beginning and didnt find
                return None

            
def msv_sniffers_time_ns_cursur_in_log(log_path, starting_time_ns, ending_time_ns, starting_character = 0):
    '''
        all time_ns are sorted, this will scan the file for begining ending cursors that contains the time_ns between starting_time_ns and ending_time_ns
        run like this
        log = '/nfs/iil/disks/ams_regruns/dkl/users/lisrael1/msv/temp_del/log_from_ariel_del.log'
        outputs = msv_sniffers_time_ns_cursur_in_log(log, starting_time_ns = 45000, ending_time_ns = 46000)
        print(outputs['tail_head_command'])
    '''
    import pandas as pd
    import numpy as np
    
    log_size=open(log_path).seek(0,2)
    log_splits=1000
    df=pd.DataFrame(np.linspace(0, log_size-starting_character, log_splits, endpoint=True)[::-1], columns=['last_characters']).astype(int)
    df['characters_from_beginning'] = log_size - df.last_characters
    df['time_ns'] = df.last_characters.apply(lambda c: last_time_ns_timestamp(log_path, characters_from_the_end=c)).fillna(0)
    df['characters_in_current_interval'] = df.characters_from_beginning.transform(lambda c:c.shift(-1) - c)
    df.characters_in_current_interval = df.characters_in_current_interval.fillna(0).astype(int)
    df['time_ns_interval'] = df.time_ns.shift(-1) - df.time_ns
    df['taken'] = pd.cut(df.time_ns, bins=[-np.inf,starting_time_ns,ending_time_ns,np.inf], labels=[0,1,4]).replace(4,0).astype(bool)
    df.taken=(df.taken | df.taken.shift().fillna(False) | df.taken.shift(-1).fillna(False)).astype(bool)  # taking one row before and one after
    simulations_in_log = df.query('time_ns_interval<0').shape[0]+1
    r = df.query('taken==1')
    if not r.empty:
        tail_head_command = f'tail -c {r.last_characters.iloc[0]:.0f} {log_path}|head -c {r.characters_from_beginning.iloc[-1]-r.characters_from_beginning.iloc[0]:.0f}'
    else:
        tail_head_command = f'cat {log_path}'
    return dict(df = df, simulations_in_log = simulations_in_log, log_size = log_size, tail_head_command= tail_head_command)


if __name__ == '__main__':
        from optparse import OptionParser
        import os
        script_path=os.path.realpath(__file__)
        import sys
        sys.path.append('/nfs/iil/disks/hip_ana_sim_01/dgottesm/analysis_and_tools/analysisPP/brk_gen1/Automation/PostProcess/upload_to_art/')
        from parse_msv_report import *
        help_text = """
        you can use this script for uploading brk simulations output into ART
        example:
            /nfs/iil/proj/cto/dav/py3.6.3/bin/python3.6 {script_path} 
        if you want to import it from your script:
                import sys
                sys.path.append('full path where the %prog is, unless your script is next to this script')
                import %prog
                %prog.msv_report_lines_to_df(log_path='./log')

        """.format(script_path=script_path)
        parser = OptionParser(usage=help_text, version="%prog 1.01 beta", epilog="good luck!") # you will see version when adding --version
        parser.add_option("-l", "--log_path", dest="log_path", type="str", help="unix log path [default:%default]", default="??")

        (option, args) = parser.parse_args()
        df=msv_report_lines_to_df(option.log_path)
        print(df.sample(100))
        print(df.shape)


