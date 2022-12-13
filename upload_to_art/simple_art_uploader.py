#!/nfs/iil/proj/cto/dav/py3.6.3/bin/python3.6
# for debug, run this script in pycharm
from sys import platform
if "win" in platform:
        import os
        os.environ['USER'] = 'lisrael1'
        print('this script should not run on windows...\nfor debug run this from pycharm at linux using python /nfs/iil/proj/cto/dav/py3.6.3/bin/python3.6')


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


def simple_art_dict(user, dct, session_name='my_session', hidden_dict={}, CornerData={}, project_name='BRK_GEN1', project_step='TC3'):
    if type(dct) is not dict: 
        print('warning - dct should be dict type, you currently have '+str(type(dct))+'. dct content:')
        print(dct)
    all_data_dict = dict()
    
    # init dict
    all_data_dict['initExecusionSession']=dict(host_name='linux_upload_script',
                                                   project_name=project_name,
                                                   user_name=user,
                                                   project_step=project_step)
    all_data_dict['initExecusionSession']['constantRecordDic']=dict(ProductName=all_data_dict['initExecusionSession']['project_name'],
                                                                    SessionDescription=session_name,
                                                                    ProductPhase=all_data_dict['initExecusionSession']['project_step'],
                                                                    User=user,
                                                                    #HostName=all_data_dict['initExecusionSession']['host_name'],
                                                                    #Station=all_data_dict['initExecusionSession']['host_name'],
                                                                   )
    
    # test dict
    all_data_dict['fnWriteToOgre_New']=dict(group='Anal', test='misc')
    ''' at fnWriteToOgre_New we have few arguments:
            string arguments:
                group Anal 
                test misc 
            all dataX arguments are dictionaries
                dataA ConfigData configurations
                dataB CornerData temperature
                dataC testData1 test results, raw data, test name
                dataD TestData2 hidden test results
                dataE AddtionalTestData - extra data like analysis indicators
        '''
    all_data_dict['fnWriteToOgre_New']['dataA'] = dict()
    all_data_dict['fnWriteToOgre_New']['dataB'] = CornerData
    all_data_dict['fnWriteToOgre_New']['dataC'] = dct
    all_data_dict['fnWriteToOgre_New']['dataD'] = hidden_dict
    all_data_dict['fnWriteToOgre_New']['dataE'] = dict()
    #print(all_data_dict.values())
    return all_data_dict


# TODO - maybe need: from collections import OrderedDict
def upload_to_ogre(all_data_dict_list, close_art_session=True):
    if not len(all_data_dict_list):
        return 
    import sys
    sys.path.append('/nfs/iil/disks/hip_ana_sim_01/dgottesm/analysis_and_tools/jupyter_notebooks/upload_to_ART/')
    sys.path.append('/nfs/iil/disks/hip_ana_sim_01/dgottesm/analysis_and_tools/jupyter_notebooks/upload_to_ART/OgreInterface/')

    from OgreInterface import OgreControl
    import importlib
    from tqdm import tqdm
    
    ARTHelper = OgreControl.clsOgreControl()
    ARTHelper.initExecusionSession(**all_data_dict_list[0]['initExecusionSession'])  # connection setup
    # all next uploads at this for loop will be at the same table, in different rows
    for data_dict in tqdm(all_data_dict_list):
        ARTHelper.fnWriteToOgre_New(**data_dict['fnWriteToOgre_New'])  # test parameters

    header('done uploading to ART!!')
    print('http://iapp257.iil.intel.com:4887/art')
    if close_art_session:
        '''next lines for clearing ogre object so next upload will be new test'''
        print('closing art session')
        importlib.reload(OgreControl)
        del ARTHelper


if __name__ == '__main__':
        from optparse import OptionParser
        from sys import platform
        import os
        if "win" in platform:
               print('this script is for linux, because you have linux commands inside')
        script_path=os.path.realpath(__file__)
        help_text = """
        you can use this script for uploading brk simulations output into ART
        example:
            /nfs/iil/proj/cto/dav/py3.6.3/bin/python3.6 {script_path} --first_dict "{{'number_of_octs':16,'number_of_sars':4,'rawdata':[1,2,3,4,3,2,1,2]}}" --user $USER 
        if you want to import it from your script:
                import sys
                sys.path.append('full path where the %prog is, unless your script is next to this script')
                import %prog
                d=%prog.simple_art_dict(user=user, dct=first_dict, session_name=session_name , project_name=project_name)
                %prog.upload_to_ogre([d])

        """.format(script_path=script_path)
        parser = OptionParser(usage=help_text, version="%prog 1.01 beta", epilog="good luck!") # you will see version when adding --version
        parser.add_option("--session_name", dest="session_name", type="str", help="session name [default:%default]", default="session_name")
        parser.add_option("--project_name", dest="project_name", type="str", help="project name [default:%default]", default="BRK_GEN1")
        parser.add_option("--close_art_session", dest="close_art_session", action="store_false", help="close ART session at the end of the upload. if not, the next upload will also be inside the last session [default:%default]", default=True)
        parser.add_option("--first_dict", dest="first_dict", type="str", help='''you can write for example "{'freq_GHz':1.5, 'train_freq_GHz':1.7}" [default:%default]''', default='''{}''')
        parser.add_option("--hidden_dict", dest="hidden_dict", type="str", help='''you can write for example "{'freq_GHz':1.5, 'train_freq_GHz':1.7}" [default:%default]''', default='''{}''')
        parser.add_option("--user", dest="user", type="str", help='''your windows username [default:%default]''', default=os.environ["USER"])

        (option, args) = parser.parse_args()

        #first_dict=dict(number_of_octs=8, rawdata='sar,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63\r\n0,0,0,0,0,0,0,75,5528,16521,2687,17,0,0,0,0,0,0,0,0,0,0,0,290,9767,14012,969,1,0,0,0,0,0,0,0,0,0,0,2,1039,14034,9751,265,0,0,0,0,0,0,0,0,0,0,0,17,2622,16674,5653,76,0,0,0,0,0,0\r\n1,1,14,64,304,754,1744,3329,4468,4941,4115,2883,1499,655,194,49,16,5,24,103,343,1022,2036,3665,4609,4836,3906,2454,1229,454,132,37,9,6,40,135,493,1209,2478,3919,4908,4804,3582,2183,989,335,102,19,4,10,55,189,598,1576,2755,4265,4824,4429,3205,1799,836,266,71,18,4\r\n2,0,0,0,0,0,0,84,5806,16769,2641,15,0,0,0,0,0,0,0,0,0,0,0,297,9589,13798,1036,0,0,0,0,0,0,0,0,0,0,0,2,1002,13917,9572,289,0,0,0,0,0,0,0,0,0,0,0,17,2672,16827,5595,72,0,0,0,0,0,0\r\n3,0,0,0,0,0,0,72,5625,16573,2759,11,0,0,0,0,0,0,0,0,0,0,0,311,9812,13919,963,2,0,0,0,0,0,0,0,0,0,0,4,958,14133,9695,275,0,0,0,0,0,0,0,0,0,0,0,15,2663,16534,5607,69,0,0,0,0,0,0\r\n4,0,0,0,0,0,0,0,0,0,0,0,78,5622,16740,2618,13,0,0,0,0,0,0,0,0,0,0,0,296,9530,13912,1029,2,0,0,0,0,0,0,0,0,0,0,3,971,13941,9830,299,0,0,0,0,0,0,0,0,0,0,0,11,2672,16749,5610,74,0\r\n5,0,0,0,0,0,0,60,5542,16609,2543,13,0,0,0,0,0,0,0,0,0,0,0,326,9734,13919,1011,2,0,0,0,0,0,0,0,0,0,0,0,977,14052,9740,314,0,0,0,0,0,0,0,0,0,0,0,14,2661,16840,5568,75,0,0,0,0,0,0\r\n6,0,0,0,0,0,0,68,5551,16685,2621,9,0,0,0,0,0,0,0,0,0,0,0,283,9706,13953,990,3,0,0,0,0,0,0,0,0,0,0,1,1022,13982,9740,292,0,0,0,0,0,0,0,0,0,0,0,10,2611,16711,5684,78,0,0,0,0,0,0\r\n7,0,0,0,0,0,0,85,5588,16772,2588,13,0,0,0,0,0,0,0,0,0,0,0,325,9779,13924,972,1,0,0,0,0,0,0,0,0,0,0,2,1041,13847,9699,304,0,0,0,0,0,0,0,0,0,0,0,17,2643,16756,5559,85,0,0,0,0,0,0\r\n8,0,0,0,0,0,0,78,5578,16575,2632,9,0,0,0,0,0,0,0,0,0,0,0,314,9633,14050,970,2,0,0,0,0,0,0,0,0,0,0,4,1051,14113,9717,306,0,0,0,0,0,0,0,0,0,0,0,19,2671,16627,5573,78,0,0,0,0,0,0\r\n9,0,0,0,0,0,0,82,5639,16708,2648,18,0,0,0,0,0,0,0,0,0,0,0,294,9548,13959,948,1,0,0,0,0,0,0,0,0,0,0,1,1015,14034,9672,286,0,0,0,0,0,0,0,0,0,0,0,16,2694,16661,5682,94,0,0,0,0,0,0\r\n10,0,0,0,0,0,0,60,5556,17010,2541,12,0,0,0,0,0,0,0,0,0,0,1,309,9761,13919,983,1,0,0,0,0,0,0,0,0,0,0,2,975,13816,9724,300,0,0,0,0,0,0,0,0,0,0,0,17,2736,16532,5680,65,0,0,0,0,0,0\r\n11,0,0,0,0,0,0,83,5571,16781,2657,19,0,0,0,0,0,0,0,0,0,0,0,306,9644,13961,995,2,0,0,0,0,0,0,0,0,0,0,1,991,13934,9788,313,0,0,0,0,0,0,0,0,0,0,0,19,2540,16744,5593,58,0,0,0,0,0,0\r\n12,0,0,0,0,0,0,88,5486,16722,2571,12,0,0,0,0,0,0,0,0,0,0,0,277,9899,13843,1054,3,0,0,0,0,0,0,0,0,0,0,4,1013,13935,9682,326,0,0,0,0,0,0,0,0,0,0,0,15,2733,16700,5542,95,0,0,0,0,0,0\r\n13,0,0,0,0,0,0,70,5511,16744,2635,13,0,0,0,0,0,0,0,0,0,0,1,294,9622,14045,1041,0,0,0,0,0,0,0,0,0,0,0,2,973,14011,9875,284,0,0,0,0,0,0,0,0,0,0,0,12,2568,16661,5560,78,0,0,0,0,0,0\r\n14,0,0,0,0,0,0,69,5532,16714,2585,8,0,0,0,0,0,0,0,0,0,0,0,316,9483,14121,1023,5,0,0,0,0,0,0,0,0,0,0,3,977,14120,9745,306,0,0,0,0,0,0,0,0,0,0,0,21,2579,16669,5643,81,0,0,0,0,0,0\r\n15,0,0,0,0,0,0,71,5580,16484,2568,16,0,0,0,0,0,0,0,0,0,0,0,295,9870,13889,1017,2,0,0,0,0,0,0,0,0,0,0,2,986,13948,9591,322,0,0,0,0,0,0,0,0,0,0,0,11,2680,16895,5696,77,0,0,0,0,0,0\r\n')
        #first_dict=dict(number_of_octs=2, number_of_sars=2, rawdata='31,36,41,45,49,53,56,58,60,61,61,60,59,56,53,50,46,41,36,31,27,22,17,13,9,6,4,2,1,1,2,3,5,8,12,16,20,25,30,35,40,44,49,52,55,58,60,61,61,60,59,57,54,50,46,42,37,32,28,23,18,14,10,7,4,2,1,1,2,3,5,8,11,15,19,24,29,34,39,43,48,52,55,58,59,61,61,61,59,57,55,51,47,43,38,33,29,24,19,15,11,7,5,3,1,1,1,3,4,7,10,14,19,23,28,33,38,43,47,51,54,57,59,60,61,61,60,58,55,52,48,44,39,34,30,25,20,16,12,8,5,3,2,1,1,2,4,7,10,13,18,22,27,32,37,42,46,50,54,57,59,60,61,61,60,58,56,53,49,45,40,35,31,26,21,16,12,9,6,3,2,1,1,2,4,6,9,13,17,21,26,31')
        #first_dict=dict(number_of_octs=2, number_of_sars=2, rawdata=[31,36,41,45,49,53,56,58,60,61,61,60,59,56,53,50,46,41,36,31,27,22,17,13,9,6,4,2,1,1,2,3,5,8,12,16,20,25,30,35,40,44,49,52,55,58,60,61,61,60,59,57,54,50,46,42,37,32,28,23,18,14,10,7,4,2,1,1,2,3,5,8,11,15,19,24,29,34,39,43,48,52,55,58,59,61,61,61,59,57,55,51,47,43,38,33,29,24,19,15,11,7,5,3,1,1,1,3,4,7,10,14,19,23,28,33,38,43,47,51,54,57,59,60,61,61,60,58,55,52,48,44,39,34,30,25,20,16,12,8,5,3,2,1,1,2,4,7,10,13,18,22,27,32,37,42,46,50,54,57,59,60,61,61,60,58,56,53,49,45,40,35,31,26,21,16,12,9,6,3,2,1,1,2,4,6,9,13,17,21,26,31])

        user=option.user
        session_name=option.session_name
        project_name=option.project_name

        hidden_dict=eval(option.hidden_dict)
        first_dict=eval(option.first_dict)

        art_dict_1=simple_art_dict(user=user, dct=first_dict, session_name=session_name , project_name=project_name)
        art_dict_2=simple_art_dict(user=user, dct=first_dict, session_name='no one will read this string...', project_name=project_name)  # you have only 1 session at single table, so it will take the first session name and ignore this one
        upload_to_ogre([art_dict_1, art_dict_2])


