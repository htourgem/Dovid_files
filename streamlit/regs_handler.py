import streamlit as st
import pandas as pd
import numpy as np
pd.options.display.max_colwidth=0
pd.options.display.max_columns=0
st.set_page_config(layout="wide")

def add_space_in_string(string_input, delimiter=' ', delimiter_every=4):
    return delimiter.join(string_input[i:i + delimiter_every] for i in range(0, len(string_input), delimiter_every))

def get_table_download_link(df):
    """Generates a link allowing the data in a given pandas dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    import base64
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}" download="regs_{pd.datetime.now()}.csv">Download csv file</a>'
    return href

def get_xml_download_link(xml_content, file_type='xml'):
    """Generates a link allowing the data in a given pandas dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    import base64
    b64 = base64.b64encode(xml_content.encode()).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}" download="regs_{pd.datetime.now()}.{file_type}">Download {file_type} file</a>'
    return href

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


def value_to_int_value(val):
    import re
    try:
        val=int(val)
        if val<0:
            return -1
        return val
    except: pass
    if type(val)!=str:
        return 0 # yehudabe - was (-1) but it stucked me. now the empty reset values will get 0 and empty NVM will get reset   
    if re.match("\s*\d+'b[01]+",val): 
#         print('binary')
        return int(val.split('b')[1],2)
    if re.match("\s*\d+'h[0-9a-fA-F]+",val): 
#         print('hex')
        return int(val.split('h')[1],16)
    st.write(f'problem casting {val}, type={type(val)}')

class xml_format:
    global_header='''<?xml version="1.0" encoding="ISO-8859-1"?>
    <BLOCK_DB LAST_ID="{global_index}">'''
    reg_header='''
    <REGISTER ACCESS_TYPE="rw" ADDR_OFFSET="{r.address_offset}" HDL_PATH="{r.HDL_PATH}" ID="{global_index}" NAME="{r.reg_name}" RESET_VAL="{r.reg_default_int:08X}" SHORT_DESCRIPTION="" USER_DEFINED_1="{r.USER_DEFINED_1}" WIDTH="32">
            <CONSTRAINTS></CONSTRAINTS>
            <DESCRIPTION></DESCRIPTION>'''
    field_header='''    
        <FIELD ACCESS_TYPE="rw" NAME="{r.field_name}" ID="{global_index}" RESET_VAL="{r.field_default_value_in_int:X}" NVM_VAL="{r.field_nvm_value_in_int:X}" NVM_MODE="{r.nvm_mode}" START_BIT_OFFSET="{r.start_bit}" WIDTH="{r.width}">
            <CONSTRAINTS></CONSTRAINTS>
            <DESCRIPTION>{r.description}</DESCRIPTION>
            <USER_DEFINED_1></USER_DEFINED_1>
            <USER_DEFINED_2></USER_DEFINED_2>
        </FIELD>'''
        ## dgottesm copied above string and removed NVM_VAL and NVM_MODE
    field_header=''' 
        <FIELD ACCESS_TYPE="rw" NAME="{r.field_name}" ID="{global_index}" RESET_VAL="{r.field_default_value_in_int:X}" START_BIT_OFFSET="{r.start_bit}" WIDTH="{r.width}">
            <CONSTRAINTS></CONSTRAINTS>
            <DESCRIPTION>{r.description}</DESCRIPTION>
            <USER_DEFINED_1></USER_DEFINED_1>
            <USER_DEFINED_2></USER_DEFINED_2>
        </FIELD>'''
    reg_end='''
    </REGISTER>'''
    global_end='''
    </BLOCK_DB>
    '''
    global_index=0
    def reg_group_to_xml_format(reg_group):
        output_string=''
        xml_format.global_index+=1
        try:
            output_string+=xml_format.reg_header.format(r=reg_group.iloc[0], global_index=xml_format.global_index)
        except:
            st.write("cannot run add this register")
            st.write(reg_group)
            return ''  # TODO
        for _,row in reg_group.iterrows():
            xml_format.global_index+=1
            output_string+=xml_format.field_header.format(r=row, global_index=xml_format.global_index)
        output_string+=xml_format.reg_end
        return output_string





def create_regs_py(fields_df):
    block_name_string='block_name'
    reg_name_string='reg_name'
    filed_name_string='field_name'
    address_offset_string='address_offset'
    reset_value_string='field_default_value_in_int' 
    nvm_value_string='field_nvm_value_in_int'
    stop_bit_string='stop_bit'
    start_bit_string='start_bit'

    reg=''
    reg_groups=fields_df[block_name_string].unique()
    # loop over all blocks in xls i.e. ana_adc, ana_rx ....
    st.write(reg_groups)
    for reg_name  in reg_groups:  
        region_addr = 0 #int(block.get('START_ADDR'), 16)
        reg+= "class "+reg_name.lower()+":\n"
        reg+="\tdef __init__(self, flc_ll):\n"
        reg+="\t\tself.addr = "+str(region_addr)+"\n"
        wrote_register = False
        reg_df=fields_df.loc[fields_df[block_name_string]==reg_name]
        for block in reg_df[reg_name_string].unique():
            if block is not np.nan:
                reg += "\t\tself."+block.lower()+" = self.cls_"+block.lower()+"(self.addr, flc_ll)\n"
        new_block = False
        new_idx = 0
        # loop over all regs in block  in xls i.e. ana_adc.vofc_dom0_quad0_quad2_sar0_slc0.....
        for running_block in reg_df[reg_name_string].unique():
            #running_block = xls['Reg Name'][field]
            fileds_df=reg_df.loc[reg_df[reg_name_string]==running_block]
            if type(running_block) == str:
                current_block = running_block.lower()
                new_block = True                                 
            else:
                new_block = False
            # print(current_block, new_block)
            if new_block:
                # print(current_block, field)
                reg+="\tclass cls_"+current_block+":\n"
                reg+="\t\tdef __init__(self, offset, flc_ll):\n"
                reg+="\t\t\tself.addr_offset = "+str(int(str(fileds_df[address_offset_string].values[0]),16))+'\n'  
                for filed in fileds_df[filed_name_string].unique():            
                    reg += "\t\t\tself.cfg_"+filed.lower()+" = self.cls_"+filed.lower()+"(offset+self.addr_offset, flc_ll)\n"
                reg+="\t\t\tself.addr = self.addr_offset + offset\n"
                reg+="\t\t\tself.flc_ll = flc_ll\n"
                reg+="\t\t\tself.value_stub = 0\n"
                reg+="\t\tdef r(self, msb = 31, lsb = 0):\n"
                reg+="\t\t\tif self.flc_ll.stub: return self.value_stub\n"
                reg+="\t\t\treturn self.flc_ll.reg(self.addr, msb, lsb, 'read')\n"
                reg+="\t\tdef w(self, value, msb = 31, lsb = 0):\n"
                reg+="\t\t\tif self.flc_ll.stub: self.value_stub = value\n"
                reg+="\t\t\tself.flc_ll.reg(self.addr, msb, lsb, value)\n"
                # loop over all filedsreg i.e. ana_adc.vofc_dom0_quad0_quad2_sar0_slc0.sar0_slc0......
                for filed in fileds_df[filed_name_string].unique(): # for fi in range(field_idx, field):
                    if type(filed)!=str:
                        print(filed)
                        break
                     
                    field_name =filed.lower()
                    field_line=fileds_df.loc[fileds_df[filed_name_string]==filed]
                    if(len(field_line)>1):
                        st.error(f'We have reg with two identical fileds reg: {running_block} , field: {filed}')
                    reg+="\t\tclass cls_"+field_name+":\n"
                    reg+="\t\t\tdef __init__(self, offset, flc_ll):\n"
                    reg+="\t\t\t\tself.flc_ll"+" = flc_ll\n"
                    reg+="\t\t\t\tself.reg_addr"+" = "+"offset\n"  #"0x"+field.get('RESET_VAL')+'\n'
                    #st.write(field_name)
                    #st.write(field_line)
                    try:
                        reg+="\t\t\t\tself.reset_val"+" = "+str(field_line[reset_value_string].item())+'\n'
                        reg+="\t\t\t\tself.nvm_val"+" = "+str(field_line[nvm_value_string].item())+'\n'
                    except:
                       st.warning("Issue with either NVM or reset value: ")
                       st.write(field_name)
                       st.write(field_line)
 
                    reg+="\t\t\t\tself.lsb = "+str(field_line[start_bit_string].item())+'\n'
                    reg+="\t\t\t\tself.width = "+str(int(field_line[stop_bit_string])-int(field_line[start_bit_string])+1)+'\n'
                    reg+="\t\t\tdef r(self):\n"
                    #reg+="\t\t\t\tprint(self.reg_addr, self.lsb + self.width - 1, self.lsb)\n"
                    reg+="\t\t\t\tif self.flc_ll.stub: return self.nvm_val\n" 
                    reg+="\t\t\t\treturn self.flc_ll.reg(self.reg_addr, self.lsb + self.width - 1, self.lsb, 'read')\n"            
                    reg+="\t\t\tdef w(self, value):\n"
                    reg+="\t\t\t\tif self.flc_ll.stub: self.nvm_val = value\n"
                    #reg+="\t\t\t\tprint(self.reg_addr, self.lsb + self.width - 1, self.lsb, value)\n"    
                    reg+="\t\t\t\tself.flc_ll.reg(self.reg_addr, self.lsb + self.width - 1, self.lsb, value)\n"            
        reg+="\n\n\n\n\n"

    return reg 


class ral_format:
    field_name_length=40
    reg_name_length_for_field_write=40
    reg_name_length_for_reg_write=36
    
    field='''`ral_set_field_v($psprintf("Barak_Quad_quad%0d_Lane_lane%0d_ANA_ADC",serdes_id, lane_id),"ANA_ADC_{reg_name:<{reg_name_length}}","{field_name:<{field_name_length}}",{width:>2}'b{field_nvm_value_in_int:<32b})\n'''
    reg='''`ral_wr_with_get_bfm($psprintf("Barak_Quad_quad%0d_Lane_lane%0d_ANA_ADC",serdes_id, lane_id),"ANA_ADC_{r.reg_name:<{reg_name_length}}", ana_reg_frontdoor)\n'''
    def reg_group_to_ral_format(reg_group):
        import re
        output_string=''
        for _,row in reg_group.iterrows():
            output_string+=ral_format.field.format(reg_name_length=ral_format.reg_name_length_for_field_write, 
                                                   field_name_length=ral_format.field_name_length, **row.to_dict())
#             row.field_nvm_value.split('b')[1]
        output_string+=ral_format.reg.format(r=reg_group.iloc[0], 
                                             reg_name_length=ral_format.reg_name_length_for_reg_write, 
                                             field_name_length=ral_format.field_name_length)
        output_string = re.sub('(\s+)"','"\g<1>', output_string)
        return output_string

def verilog_stand_alone_format(df, project):
    field_max_len= df.reg_field_name.apply(len).max() + 1
    reg_max_len= df.reg_name.apply(len).max() + 1
    
    # defines
    defines='\t// defines:\n'
    # first full reg address, if you want to update it all
    defines+=df.apply(lambda r: f"""`define {r.reg_name: <{field_max_len}} 'h{r.address_offset:0>3}""", axis=1).drop_duplicates().add('\n').sum()
    # now reg & field names
    defines+=df.apply(lambda r: f"""`define {r.reg_field_name: <{field_max_len}} `{r.reg_name:<{reg_max_len}}][{r.stop_bit}:{r.start_bit}""", axis=1).add('\n').sum()
    
    # now set values
    reg_content='//updating registers objects content (before writing registers)\n'
    reg_content+='bit [31:0] regs[bit[11:0]];\n'
    reg_content+='initial begin\n'
    if (project=='falcon_tc2'):
        nvm_xor_default_regs_list=df.query(f'nvm_config_bmod!=field_default_value').reg_name.unique()
        if nvm_xor_default_regs_list.size!=0:
            reg_content+=df[df.reg_name.isin(nvm_xor_default_regs_list)].apply(lambda r: f'''\tregs[`{r.reg_field_name: <{field_max_len}}] = {r.nvm_config_bmod};''', axis=1).add('\n').sum() 
    elif(project=='barak_a0'):
        nvm_xor_default_regs_list=df.query(f'field_bmodsim_value!=field_default_value').reg_name.unique()
        if nvm_xor_default_regs_list.size!=0:
            reg_content+=df[df.reg_name.isin(nvm_xor_default_regs_list)].apply(lambda r: f'''\tregs[`{r.reg_field_name: <{field_max_len}}] = {r.field_bmodsim_value};''', axis=1).add('\n').sum()
    else:        
        nvm_xor_default_regs_list=df.query(f'field_bmodsim_value!=field_default_value').reg_name.unique()
        if nvm_xor_default_regs_list.size!=0:
            reg_content+=df[df.reg_name.isin(nvm_xor_default_regs_list)].apply(lambda r: f'''\tregs[`{r.reg_field_name: <{field_max_len}}] = {r.field_nvm_value};''', axis=1).add('\n').sum()
    reg_content+='''
    \t// examples for writing regs:
    \t//regs[`SAR_COMMON_REG0__o_quartet_nob_fw] = 2'b11;
    \t//regs[`SAR_COMMON_REG0]='h01600000;
    \t//write_reg(`CHANNEL_CTRL, regs[`CHANNEL_CTRL]);
    \t//regs['h240]='h01600000;
    \t//write_reg('h240, regs['h240]);
    '''

    reg_content+='\t//writing registers\n'
    reg_content+="\tforeach (regs[address]) begin\n"
    reg_content+='''\t\t$display("writing address 'h %03x value is 'h %08x at %g[ns]",address, regs[address], $realtime/1ns);\n'''
    reg_content+="\t\twrite_reg(address, regs[address]);\n"
    reg_content+='\tend\n'

    reg_content+='end'
    
    default_value='\t// reset values! this is not nvm values!\n'
    default_value+=df.apply(lambda r: f'''\tregs[`{r.reg_field_name: <{field_max_len}}] = {r.field_default_value};''', axis=1).add('\n').sum()
    
    return dict(defines=defines, reg_nvm_values=reg_content, reg_default_value=default_value)


def reg_group_full_value(reg_group):
    bits_nvm=['0']*32  # not putting here x as you cannot convert it to hex
    bits_reset=['0']*32
    for _,row in reg_group.iterrows():
        if(type(row.field_nvm_value_in_int) == float):
            st.write(f'Float- {row.reg_name} , {row.field_name}, {row.field_nvm_value_in_int}')
            row.field_nvm_value_in_int=int(row.field_nvm_value_in_int)
        bits_nvm[row.start_bit:row.stop_bit+1]=f'{row.field_nvm_value_in_int:0{int(row.width)}b}'[::-1]
        bits_reset[row.start_bit:row.stop_bit+1]=f'{row.field_default_value_in_int:0{int(row.width)}b}'[::-1]
        return_dict = dict(reg_name=reg_group.reg_name.iloc[0], reg_nvm_int=int(''.join(bits_nvm[::-1]), 2), reg_default_int=int(''.join(bits_reset[::-1]), 2))
    return pd.Series(return_dict)

def field_in_reg(field_default_value, field_nvm_value, start_bit, stop_bit):
    field_in_reg=f'{"reg default":<25}'
    field_in_reg+=add_space_in_string(f'''{field_default_value:032b}''')
    field_in_reg+=f'\n{"reg nvm":<25}'
    field_in_reg+=add_space_in_string(f'''{field_nvm_value:032b}''')
    tmp=['-']*32
    tmp[start_bit:stop_bit+1] = '+'*query_this_field.width
    field_in_reg+=f'\n{"field place":<25}'
    field_in_reg+=add_space_in_string(''.join(tmp[::-1]))
    field_in_reg+=f'\n{"default and nvm diff":<25}'
    field_in_reg+=add_space_in_string(f'''{field_nvm_value^field_default_value:032b}''').replace('0','-').replace('1','+')
    return field_in_reg

def bad_characters(s):
    try:
        return not all(ord(c) < 128 for c in s)                                                 
    except: return 0
                                                    
                                 
                                                    
                                                    
                                                    
                                                    
                                                    
                                                    
                                                    
                                                    
                                                    
                                                    
                                                    
                                                    
                                                    
                                                    
                                                    
                                                    
                                                    
                                                    
st.header('reg excels to different formats')
st.sidebar.markdown('regs handler')
st.sidebar.image('/nfs/iil/disks/hip_ana_sim_01/dgottesm/analysis_and_tools/streamlit/regs_handler.jpg', use_column_width=True)
st.sidebar.info('drag xlsx file that contains the registers addresses and content, and create verilog/python/xml content from it')
# loading data
demo_table = st.sidebar.checkbox('take demo data')
if demo_table:
    st.warning('demo data')
    uploaded = '/nfs/iil/disks/hip_ana_sim_01/dgottesm/analysis_and_tools/streamlit/demo_data/regs_handler_demo_data.xlsx'
else:
    st.sidebar.markdown('First - Choose a Project!')
    uploaded = st.sidebar.file_uploader('our format soc online xlsm files', type=None, accept_multiple_files=False, key=['xlsx'])
    project=   st.sidebar.selectbox("Choose Project", ('Others', 'falcon_tc2', 'barak_a0' ))     
if not uploaded: st.stop()
uploaded=pd.read_excel(uploaded, sheet_name=None)
if not set(['fields','regs']).issubset(set(uploaded.keys())):
    st.error(f'you need to have fields and regs tabs at your excels, but found {uploaded.keys()} instead')
fields_df = uploaded['fields']
if 'field_nvm_value' not in fields_df.columns and project!='falcon_tc2' and project!='barak_a0' : 
    st.error(f'You may need to choose correct project. "field_nvm_value" is not in columns {fields_df.columns}')
     
regs_df = uploaded['regs']
                                                    
# replacing weird windows characters to normal ones
fields_df=fields_df.replace(['‘','’','—','–','…','\n','\xa0'],["'","'",'-','-','...',' ',' '], regex=True)
regs_df=regs_df.replace(['‘','’','—','–','…','\n','\xa0'],["'","'",'-','-','...',' ',' '], regex=True)


# optional - load SA log file and find diff between nvm or reset to the log
if not demo_table:
    sa_log = st.sidebar.file_uploader('optional - SA log file to compare SA values to default/nvm values', type=None, accept_multiple_files=False)



# general fixes
regs_df.address_offset=regs_df.address_offset.astype(str).replace("\d+'h",'', regex=True)
if (project=='falcon_tc2'): fields_df['nvm_config_bmod']= np.where(fields_df.nvm_config_bmod.isnull(), fields_df['field_default_value'], fields_df['nvm_config_bmod']  )
elif(project=='barak_a0'): fields_df['nvm_config_bmod']= np.where(fields_df.field_bmodsim_value.isnull(), fields_df['field_default_value'], fields_df['field_bmodsim_value']  )
else:  fields_df['field_nvm_value']= np.where(fields_df.field_nvm_value.isnull(), fields_df['field_default_value'], fields_df['field_nvm_value']  )
def chack_stop_bit(x):
    if (x.stop_bit<x.start_bit): 
        st.error(f'Stop bit most be greater the Start bit or equal')
        st.error(f'{x}')
fields_df.apply(chack_stop_bit, axis=1)
fields_df['width']=fields_df.stop_bit-fields_df.start_bit+1
fields_df['field_default_value_in_int']=fields_df.field_default_value.apply(value_to_int_value)
if  (project=='falcon_tc2') : 
    nvm_filed='nvm_config_bmod'
elif (project=='barak_a0'):
    nvm_filed='field_bmodsim_value'
else:
    nvm_filed='field_nvm_value'

fields_df['field_nvm_value_in_int']=fields_df[nvm_filed].apply(value_to_int_value)
fields_df['field_nvm_value_in_int']=fields_df['field_nvm_value_in_int'].fillna(0)
fields_df['field_nvm_value_in_int']=fields_df['field_nvm_value_in_int'].astype(int)

#cahcking value validity 
def check_nvm_value_validity(row):
    if row.field_nvm_value_in_int<0 or row.field_nvm_value_in_int>(2**row.width)-1:
        st.error(f'NVM value {row.field_nvm_value_in_int} out of range for {row.width} bit filed {row.reg_name}:{row.field_name}')
def check_default_value_validity(row):
    if row.field_default_value_in_int<0 or row.field_default_value_in_int>(2**row.width)-1:
        st.error(f'Default value {row.field_default_value_in_int} out of range for {row.width} bit filed {row.reg_name}:{row.field_name}')
fields_df.apply(check_nvm_value_validity, axis=1)
fields_df.apply(check_default_value_validity, axis=1)

tmp=fields_df.groupby('reg_name', as_index=False).apply(reg_group_full_value)
fields_df=fields_df.merge(tmp, on='reg_name', how='left')
st.warning('bit 0 is the LSB!')
fields_df['reg_field_name']=fields_df.reg_name+'__'+fields_df.field_name
regs_df=regs_df.merge(fields_df.groupby('reg_name').reg_nvm_int.first(), on='reg_name', how='left')
regs_df['reg_nvm_binary']=regs_df.reg_nvm_int.apply(lambda n:f"32'b{n:032b}")
if 'nvm_mode' not in fields_df.columns:
    fields_df['nvm_mode']=None


# finding non ascii characters that we didnt replace above
non_ascii_content = fields_df.loc[fields_df.applymap(bad_characters).sum(1).values==1]
if not non_ascii_content.empty:
    st.error('you have non acsii content at the next lines! it will corrupt the xml uplaod!')
    st.write('those are the non ascii characters and their encoding value:')
    non_ascii_set=set([c for c in non_ascii_content.select_dtypes('object').sum().sum() if ord(c) >= 128])
    non_ascii_set=[[i, ord(i)] for i in non_ascii_set]
    st.code(non_ascii_set)
    st.write('those are the rows that contains the bad characters:')
    st.write(non_ascii_content)
    st.write('the cells that contains the bad characters are marked with 1:')
    st.write(fields_df.applymap(bad_characters).loc[fields_df.applymap(bad_characters).sum(1).values==1])



# checking overlap and missing bits
my_placeholder = st.empty()
my_placeholder2 = st.empty()
my_placeholder.info('checking fileds overlap')
my_placeholder2.write('copy content')
fields_df['bit_number']=fields_df.apply(lambda r: list(range(r.start_bit, r.stop_bit+1)), axis=1)
tmp=pd.DataFrame(fields_df.reg_name.unique(), columns=['reg_name'])
tmp['bit_number']=[list(range(32))]*tmp.shape[0]
tmp=tmp.append(fields_df.copy())
my_placeholder2.write('explode')
check_bits_at_regs = tmp.explode('bit_number').reset_index(drop=True)
my_placeholder2.write('groupby')
check_bits_at_regs=check_bits_at_regs.groupby(['reg_name','bit_number'], group_keys=False)
my_placeholder2.write('counting')
check_bits_at_regs=check_bits_at_regs.bit_number.count().rename('number_of_fields_on_bit').reset_index(drop=False)
check_bits_at_regs.number_of_fields_on_bit-=1
check_bits_at_regs=check_bits_at_regs.query('number_of_fields_on_bit!=1')
# check_bits_at_regs['fields_overlap']=tmp.apply(lambda g: g.assign(fields_overlap=g.shape[0])).fields_overlap
# check_bits_at_regs['fields_overlap']=tmp.reg_name.count()
my_placeholder2.write('checking overlap')
if not check_bits_at_regs.empty:
    st.error('*** error - we have fields overlap! ***')
    st.write(check_bits_at_regs.sort_values(['reg_name','bit_number']))
else:
    st.info('all regs has all bits with fields, with no overlap')
my_placeholder.empty()
my_placeholder2.empty()




# xml content
xml=fields_df.merge(regs_df, on='reg_name', how='left').assign(HDL_PATH='').assign(USER_DEFINED_1=1).groupby('reg_name', as_index=True).apply(xml_format.reg_group_to_xml_format)
xml=xml_format.global_header.format(global_index=xml_format.global_index)+xml.sum() + xml_format.global_end

                                                    

                                                    
# ral
ral_format.field_name_length = fields_df.field_name.apply(len).max()
ral_format.reg_name_length_for_field_write = regs_df.reg_name.apply(len).max()
ral_format.reg_name_length_for_reg_write=ral_format.reg_name_length_for_field_write-4
ral=fields_df.merge(regs_df, on='reg_name', how='left')
ral_with_default_equal_nvm=ral.groupby('reg_name', as_index=True).apply(ral_format.reg_group_to_ral_format)
ral_with_default_equal_nvm=ral_with_default_equal_nvm.add('\n').sum()
if(project=='falcon_tc2'):
    ral_without_default=ral.query('nvm_config_bmod!=field_default_value').groupby('reg_name', as_index=True).apply(ral_format.reg_group_to_ral_format)
elif (project=='barak_a0'):
    ral_without_default=ral.query('field_bmodsim_value!=field_default_value').groupby('reg_name', as_index=True).apply(ral_format.reg_group_to_ral_format) 
else:
    ral_without_default=ral.query('field_nvm_value!=field_default_value').groupby('reg_name', as_index=True).apply(ral_format.reg_group_to_ral_format)

ral_without_default=ral_without_default.add('\n').sum()

#python content
py_content=create_regs_py(fields_df.merge(regs_df, on='reg_name', how='left'))

# prints
with st.beta_expander(f'register table'):
    st.markdown(get_table_download_link(regs_df), unsafe_allow_html=True)
    st.write(regs_df)
with st.beta_expander(f'fields table'):
    st.markdown(get_table_download_link(fields_df), unsafe_allow_html=True)
    st.write(fields_df)


# query specific reg
with st.beta_expander(f'query sepcific reg'):
    query_this_reg=st.selectbox('select register to view here:', [''] + regs_df.reg_name.unique().tolist())
    st.write(fields_df.query('reg_name==@query_this_reg'))
    query_this_field=''
    if query_this_reg!='':
        query_this_field = st.selectbox('select field to view here:', [''] +fields_df.query('reg_name==@query_this_reg').field_name.to_list())
    if query_this_field!='':
        query_this_field=fields_df.query('reg_name==@query_this_reg and field_name==@query_this_field').iloc[0]
        st.write(query_this_field)
        field_in_reg=field_in_reg(query_this_field.reg_default_int, query_this_field.reg_nvm_int, query_this_field.start_bit, query_this_field.stop_bit)
        st.code(field_in_reg)


# reset value in scheme syntax
with st.beta_expander(f'default value in scheme syntax'):
    col1, col2 =st.beta_columns(2)
    value_0 = col1.text_input('enter vss net name', 'vssx')+','
    value_1 = col2.text_input('enter vcc net name', 'vcc')+','
    query_this_reg=st.selectbox('select register to view default input:', [''] + regs_df.reg_name.unique().tolist())
    if query_this_reg!='':
        st.write(fields_df.query('reg_name==@query_this_reg'))
        reg_value=''
        reg_value+=add_space_in_string(f"{fields_df.query('reg_name==@query_this_reg').reg_default_int.iloc[0]:032b}")
        reg_value+='\n\npreset:'
        tmp_val=f"\n{fields_df.query('reg_name==@query_this_reg').reg_default_int.iloc[0]:032b}".\
        replace("0","*0*").replace("1","*1*")
        reg_value+=tmp_val.\
        replace("*0*",value_0).replace("*1*",value_1)[:-1]
        reg_value+='\n\nreset:'
        reg_value+=tmp_val.\
        replace("*1*",value_0).replace("*0*",value_1)[:-1]
        st.code(reg_value)
        

                                                    
                                                    
                                                    
# default and nvm diff fields:
with st.beta_expander(f'fields that has differnet reset and nvm values'):
    if(project=='falcon_tc2'):
        st.write(fields_df.query('nvm_config_bmod!=field_default_value').reset_index(drop=False))
    elif (project=='barak_a0'):
        st.write(fields_df.query('field_bmodsim_value!=field_default_value').reset_index(drop=False))
    else:
        st.write(fields_df.query('field_nvm_value!=field_default_value').reset_index(drop=False))


                                                    
# xml
with st.beta_expander(f'xml content'):
    st.code(xml)
with st.beta_expander(f'download xml'):
    st.markdown(get_xml_download_link(xml,'xml'), unsafe_allow_html=True)
                                                    
# ral
#with st.beta_expander(f'ral content where defaults!=nvm'):
#    st.markdown(get_xml_download_link(ral_without_default,'v'), unsafe_allow_html=True)
#    st.code(ral_without_default)
#with st.beta_expander(f'ral content with defaults==nvm'):
#    st.markdown(get_xml_download_link(ral_without_default,'v'), unsafe_allow_html=True)
#    st.code(ral_with_default_equal_nvm)
                                                    
# SA format
sa_content=verilog_stand_alone_format(fields_df.merge(regs_df, on='reg_name', how='left'), project)
with st.beta_expander(f'SA format - defines'):
    st.code(sa_content['defines'])
with st.beta_expander(f'SA format - nvm values(when it not equals defaults)'):
    st.code(sa_content['reg_nvm_values'])
with st.beta_expander(f'SA format - default values - not nvm!'):
    st.code(sa_content['reg_default_value'])

#Python format
with st.beta_expander(f'Python content'):
    st.code(py_content)
with st.beta_expander(f'download Python reg access'):
    st.markdown(get_xml_download_link(py_content,'reg_access_py'), unsafe_allow_html=True)

 
