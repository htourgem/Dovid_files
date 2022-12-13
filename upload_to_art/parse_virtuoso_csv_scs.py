def get_params_from_scs(input_scs_path, debug=False):
    '''

        :param input_scs_path:
        :param debug:
        :return: dict of parameters
        '''
    import re
    input_scs_path = input_scs_path.replace('\\', '/')
    if debug:
        print('now reading file %s' % input_scs_path)
    scs_content = open(input_scs_path).read()
    if not len(scs_content):
        if debug:
            print('file is empty')
        print(f'no content at {input_scs_path}')
        return 'empty file, dropping file %s' % input_scs_path

    parameters = scs_content.replace('parameters \\\n','parameters').partition('parameters ')[-1].replace(' \\\n', ' ').split('\n')[0]
    # pattern = re.compile("(?P<key>[\w.-_]+)=(?P<value>[\w.-_]+)")
    pattern = re.compile("(?P<key>[^= ]+?)=(?P<value>[^ ]+?) ")
    params = pattern.findall(parameters)
    params = {i[0]: i[1] for i in params}
    params['input_file'] = input_scs_path
    print(f'found {len(params.keys())-1} parameters at {input_scs_path}')
    #     params = pd.DataFrame().from_dict(params, orient='index')
    with open(input_scs_path) as outfile:
        text = outfile.readlines()
        for line in text:
            if line.startswith("include") and "section" in line and r"/" not in line:
                x = line.strip().split('"')
                params[x[1]] = x[2].split("=")[1]
            if "temp=" in line:
                x = line.strip().split(" ")
                for word in x:
                    if "temp" in word:
                        params["temp"] = int(word.split("=")[1])

                
    return params







if __name__ == '__main__':
    pass
    example = '''
    simulator lang=spectre
global 0 vss!
parameters \
    result_path="/nfs/iil/disks/hip_ana_sim_wa/yehudabe/barak_gen2_n5/brk2_megabench/dc_solutions/" \
    polo_pre="polo/" extract="rcb" current_mismatch=1 \
    Skew="fastmos_slowrc" Corner_Num_Str="3" Corner_Num=3 \
    v_res_sum_vref_v=10 v_res_sum_vref_o=5 cdr_window_ui=20 \
    dc_solution_path="/nfs/iil/disks/hip_ana_sim_wa/yehudabe/barak_gen2_n5/brk2_megabench/dc_solutions/polo/3/dc_solution" \
    i_c0_in=100u i_taps_in=60u c_dac_par=15f a=0 cdr_en=0 ffe_100u=0 \
    ldo_50u=0 prebuff_100u=100u prebuff_250u=320u summer_100u=0 \
    n_cycle_sample=3 n_smp=256 prbs_delay=0 cmfb_cap=1p cmfb_gain_db=30 \
    summer_pmos_mult=32 tran_mult_cs=32 ldo_vcc_0p7=0.7 ldo_vss_0p6=0.6 \
    th2_boost_0p7=0.7 prebuff_300u=300u prebuff_100u_curr=100u \
    ffe_casc_current=25u ffe_nsf_curr=100u ffe_cmfb_current=25u \
    ffe_current=80u hs_clk_delay=0 hs_clk_period=17.8571428571429e-12 \
    rnor_res=1 sync_rst_time=480p ffe_in_cm=0.6 ffe_out_cm=0.3 \
    i_slc=0.0005 r_load=58 cm_o_target=750m prebuff_vcm_ref=0.75 \
    clk_delay=0 width_th1_clk=0.75 width_th2_clk=0.5 vcc1p05=1.05 \
    CLK_DELAY=0 sim_time=10n ldo_top_o_vss_0p5=0.5 ldo_vcc0p8=0.8 \
    ldo_vcc0p9=0.9 vpark_0p5=0.5 vprt1p0=1 f_dco=14G n_inv=5 p_inv=5 \
    prbs_en=0 sin_en=1 unstub=0 vcc0p9=0.85 VIN_AMP=0.15 VIN_CM=750m \
    c_nbias=10f cm_out=750m dac_cap_half=0.5f indu=1n inductance=1n \
    r_ind=50 vcc0p65_lv=0.65 vcc1p0_lv=1 vcc1p5=1.41 fclk=3.5G ui=1/(56G) \
    tran_time=10p ffe_vcas_bias=0.85 vcc=0.85 \
    summer_gain_gry=v_res_sum_vref_o*32+v_res_sum_vref_v \
    VIN_FREQ=n_cycle_sample/(n_smp*hs_clk_period)
include "$PROJ_SPECTRE_MODEL" section="fastmos_slowrc"
    '''
    another_example = '''
    simulator lang=spectre
global 0 vss!
parameters i_taps_in=50u i_c0_in=100u c_dac_par=12f cdr_en=1 \
    data_en_time=1.8p a=0 \
    summer_gain_gry=v_res_sum_vref_o*32+v_res_sum_vref_v prs_elay_stack=0  \
    ldo_50u ffe_100u summer_100u=100u prebuff_250u prebuff_100u \
    prbs_delay=0  cmfb_cap=1p f0000=983040 fff=65535 cmfb_gain_db=30 \
    summer_pmos_mult=32 tran_mult_cs=32 ldo_vcc_0p7=0.7 ldo_vss_0p6=0.6 \
    th2_boost_0p7=0.7 prebuff_300u=300u prebuff_100u_curr=100u \
    ffe_casc_current=25u ffe_nsf_curr=100u ffe_cmfb_current=25u \
    ffe_current=80u hs_clk_delay=0 hs_clk_period=1/56G rnor_res=1 \
    sync_rst_time=280p ffe_in_cm=0.6 ffe_out_cm=0.3 i_slc=1.25*400u \
    r_load=58 cm_o_target=750m prebuff_vcm_ref=0.6 clk_delay=0 \
    width_th1_clk=0.75 width_th2_clk=0.5 vcc1p05=1.05 CLK_DELAY=0 \
    sim_time=15n ldo_top_o_vss_0p5=0.5 ldo_vcc0p8=0.7 ldo_vcc0p9=0.9 \
    vpark_0p5=0.5 vprt1p0=1 f_dco=14G n_inv=5 p_inv=5 prbs_en=1 sin_en=0 \
    unstub=0 vcc0p9=0.9 VIN_AMP=0.2 VIN_CM=750m VIN_FREQ=2.5G c_nbias=10f \
    cm_out=750m dac_cap_half=0.5 indu=1n inductance=1n r_ind=50 \
    vcc0p65_lv=0.65 vcc1p0_lv=1 vcc1p5=1.5 fclk=3.5G ui=1/(56G) \
    tran_time=5p ffe_vcas_bias=vcc0p9 vcc=vcc0p9
include "$DP_SPECTRE_MODEL" section=nom

    '''
