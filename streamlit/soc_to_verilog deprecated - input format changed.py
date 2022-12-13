import streamlit as st
from glob import glob
import pandas as pd
pd.options.display.max_colwidth=0
pd.options.display.max_columns=0


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
    href = f'<a href="data:file/csv;base64,{b64}" download="abc.csv">Download csv file</a>'
    return href


def soc_format_to_table(a):
    a=a
    a=a.reset_index(drop=False).rename(columns=lambda c: c.replace(' ','_'))
    a.Reg_Name = a.Reg_Name.str.upper()
    df=pd.DataFrame()
    df['original_add']=a.Reg_Offset
    df=df.join(a[['Reg_Name','Field_Name', 'Field_Width']])
    df['Bits']=(a.Field_Start_Add+a.Field_Width-1).astype(str)+':'+a.Field_Start_Add.astype(str)
    df['field_full_name'] = df.Reg_Name+'__'+df.Field_Name
    df['NVM_value'] = a.apply(lambda r: f"{r.Field_Width}'b{int(r.Field_Default,16):b}", axis=1)
    df=df.query('Reg_Name.str.startswith("RXDCO")==False')
    df['domain']='500' #((df.original_add.apply(lambda x: int(x,16))==0).cumsum()>0).replace([False, True], ['500','500'])
    df['Reg_Soconline_Offset']=df.apply(lambda r:f'{int(r.original_add,16)+int(r.domain,16):x}', axis=1)
    return df

def our_format_to_table(df):
    df=df.rename(columns=lambda c:c.replace(' ','_'))
    df=df.fillna(method='ffill')#[['Reg_Soconline_Offset','']]
    # st.write('table:')
    # st.write(df)
    # now we have all the soc tables in one df



    # extracting regs and filed values and addresses
    fields_address_and_vals=df[['Reg_Name','Reg_Soconline_Offset','Field_Name','Bits','NVM_value', 'Reset_value', 'Description']].dropna(subset=['Field_Name'], axis=0)
    fields_address_and_vals.Reg_Name=fields_address_and_vals.Reg_Name.fillna(method='ffill')
    fields_address_and_vals.Reg_Soconline_Offset=fields_address_and_vals.Reg_Soconline_Offset.fillna(method='ffill')

    # dropping lines that are just headers
    fields_address_and_vals=fields_address_and_vals.query('Field_Name not in ["NVM value","NVM_value"]')
    fields_address_and_vals['field_full_name']=fields_address_and_vals.Reg_Name+"__"+fields_address_and_vals.Field_Name
    return fields_address_and_vals


def upload_interface_return_table():
    st.header('soc files to verilog code')
    st.info('drag xlsm files that contains the registers addresses and content, and create verilog/python content from it')
    st.sidebar.markdown('soc converter')
    st.sidebar.image('/nfs/iil/disks/hip_ana_sim_01/dgottesm/analysis_and_tools/jupyter_notebooks/streamlit/soc_to_verilog.jpg', use_column_width=True)

    our_format_files = st.file_uploader('our format soc online xlsm files', type=None, accept_multiple_files=True, key=['xlsm'])
    soc_files = st.file_uploader('soc online xlsx files', type=None, accept_multiple_files=True, key=['xlsx'])
    if len(soc_files)==0 and len(our_format_files)==0:
        st.error('please upload files')
        st.stop()

    our_format_files_df=pd.DataFrame()
    soc_df=pd.DataFrame()

    if len(our_format_files):
        for xl in our_format_files:
            our_format_files_df=our_format_files_df.append(pd.read_excel(xl).assign(file_name=xl), sort=False)

        our_format_files_df=our_format_to_table(our_format_files_df)
    if len(soc_files):
        for xl in soc_files:
            soc_df=soc_df.append(pd.read_excel(xl, None)['ANA_RX'].assign(file_name=xl), sort=False)
        soc_df=soc_format_to_table(soc_df)
    fields_address_and_vals=our_format_files_df.append(soc_df)
    fields_address_and_vals['field_start_index'] = fields_address_and_vals.Bits.str.split(':').str[-1].astype(int)
    fields_address_and_vals['field_stop_index_including'] = fields_address_and_vals.Bits.str.split(':').str[0].astype(int)
    fields_address_and_vals['field_width'] = fields_address_and_vals.field_stop_index_including - fields_address_and_vals.field_start_index + 1
    return fields_address_and_vals

df = upload_interface_return_table()
st.markdown(get_table_download_link(df), unsafe_allow_html=True)




# printing table
if st.checkbox('show table columns'):
    st.code('\n'.join(df.columns))
    
st.write('fields_address_and_vals:')
st.write(df)

# TODO
st.header('query specific register:')
query_this_reg=st.selectbox('select register to view here:', [''] + df.Reg_Name.unique().tolist())
picked_reg = df.query(f'Reg_Name=="{query_this_reg}"')
st.write(picked_reg)
full_reg_value=['x']*32
for _,row in picked_reg.iterrows():
    full_reg_value[row.field_start_index: row.field_stop_index_including+1] = list(f'''{int(row.NVM_value.split("'b")[-1],2):0{row.field_width}b}''')[::-1]
if 'x' not in full_reg_value:
    full_reg_value=int(''.join(full_reg_value)[::-1],2)
    full_reg_value_bits = add_space_in_string(f'{full_reg_value:032b}')
    st.code(f'reg full value is \n\t0x {full_reg_value:08x} \n\t0b {full_reg_value_bits}')

if query_this_reg!='':
    st.header(f'query specific field at {query_this_reg}:')
    query_this_field=st.selectbox('select register to view here:', ['']+picked_reg.Field_Name.unique().tolist())
    if query_this_field!='':
        specific_field=picked_reg.query(f'Field_Name=="{query_this_field}"').iloc[0]
        st.write(specific_field)
        field_in_reg=['-']*32
        field_in_reg[specific_field.field_start_index: specific_field.field_stop_index_including+1] = list(f'''{int(specific_field.NVM_value.split("'b")[-1],2):0{specific_field.field_width}b}''')[::-1]
        field_in_reg=add_space_in_string(''.join(field_in_reg[::-1]))
        st.code(f'full reg:\n\t{full_reg_value_bits}\nfield in reg\n\t{field_in_reg}')



# checking if we have the same register multiple times
multi_reg_define=df.groupby('field_full_name').apply(len).sort_values().to_frame('times').query('times>1')
if not multi_reg_define.empty:
    st.error('we have those fields multiple times:')
    st.write(multi_reg_define)

    
    
    
    
    
    
    
    
    
# print the verilog codes
field_max_len= df.field_full_name.apply(len).max() + 1
reg_max_len= df.Reg_Name.apply(len).max() + 1
defines='\t// defines:\n'
# first full reg address, if you want to update it all
defines+=df.apply(lambda r: f"""`define {r.Reg_Name: <{field_max_len}} 'h{r.Reg_Soconline_Offset:0>3}""", axis=1).drop_duplicates().add('\n').sum()
# now reg & field names
if 1:
    defines+=df.apply(lambda r: f"""`define {r.field_full_name: <{field_max_len}} `{r.Reg_Name:<{reg_max_len}}][{r.Bits}""", axis=1).add('\n').sum()
else:  # if you want the address instead of reg name when setting fiels
    defines+=df.apply(lambda r: f"""`define {r.field_full_name: <{max_len}} `h{r.Reg_Soconline_Offset:0>3}][{r.Bits}""", axis=1).add('\n').sum()
    
number_of_new_lines=defines.count("\n")
expander_reg_decleration=st.beta_expander(f'show verilog code for registers decleration ({number_of_new_lines} lines)')
expander_reg_decleration.code(defines)
    
    
    
reg_content='//updating registers objects content (before writing registers)\n'
reg_content+='bit [31:0] regs[bit[11:0]];\n'
reg_content+='initial begin\n'
reg_content+=df.apply(lambda r: f'''\tregs[`{r.field_full_name: <{field_max_len}}] = {r.NVM_value};''', axis=1).add('\n').sum()


# you dont need this
# print('\t// some manual fixes of soc ')
# print("\tregs[`SAR_COMMON_REG0]='h01600000;")
# print("\tregs['h240]='h01600000;")
# print("\tregs['h404]='h01000b00;")
# print("\tregs['h408]='h3f020b00;")
# print("\tregs['h414]='h01000b00;")
# print("\tregs['h418]='h3f020b00;")
# print("\tregs['h424]='h01000b00;")
# print("\tregs['h428]='h3f030b00;")
# print("\tregs['h434]='h01000b00;")
# print("\tregs['h438]='h3f010b00;")

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
number_of_new_lines=reg_content.count("\n")
expander_reg_initial_values=st.beta_expander(f'show verilog code for registers initial values ({number_of_new_lines} lines)')
expander_reg_initial_values.code(reg_content)

    
    
expander_reg_table=st.beta_expander(f'register table')
reg_table = pd.DataFrame()
reg_table['reg_name'] = df.Reg_Name
reg_table['address_offset'] = df.Reg_Soconline_Offset
reg_table['domain'] = 'TODO'
reg_table['domain_name'] = 'TODO'
reg_table=reg_table.groupby('reg_name', as_index=False).first()

field_table = pd.DataFrame()
field_table['field_name'] = df.Field_Name
field_table['reg_name'] = df.Reg_Name
field_table['start_bit'] = df.Bits.str.split(':').str[1]
field_table['stop_bit'] = df.Bits.str.split(':').str[0]
field_table['default_value'] = df.Reset_value
field_table['nvm_value'] = df.NVM_value
field_table['description'] = df.Description

expander_reg_table.markdown(get_table_download_link(reg_table), unsafe_allow_html=True)
expander_reg_table.markdown(get_table_download_link(field_table), unsafe_allow_html=True)
expander_reg_table.write(reg_table)
expander_reg_table.write(field_table)



    
    
    
    
if 1:
    def reg_table_to_xml(reg_df):
        reg_header='''<?xml version="1.0" encoding="ISO-8859-1"?>
<BLOCK_DB LAST_ID="1490">
    <REGISTER ACCESS_TYPE="rw" ADDR_OFFSET="0" HDL_PATH="" ID="{r.index}" NAME="{r.Reg_Name}" RESET_VAL="{r.Reset_value}" SHORT_DESCRIPTION="" USER_DEFINED_1="0" WIDTH="{r.field_width}">
        <CONSTRAINTS></CONSTRAINTS>
        <DESCRIPTION></DESCRIPTION>'''
        field_header='''    <FIELD ACCESS_TYPE="rw" NAME="sar0_slc0" ID="2" RESET_VAL="0" START_BIT_OFFSET="24" WIDTH="8">
            <CONSTRAINTS></CONSTRAINTS>
            <DESCRIPTION>8 bit: MSB,sign  ,others , magnitude gray code (0:126) 127 iligeal.</DESCRIPTION>
            <USER_DEFINED_1></USER_DEFINED_1>
            <USER_DEFINED_2></USER_DEFINED_2>
        </FIELD>'''
        reg_end='</REGISTER>'
        # st.write
    
    
    
    
    
    
if 0: # i changed the format    
    # convert to python
    reg_class = '''
    class regs_class:
    \tdef __init__(self):\n\t\t'''
    reg_class+=df.groupby('Reg_Name', as_index=False).first().apply(lambda r: f'self.{r.Reg_Name:<30} = self.reg_class({r.Reg_Soconline_Offset})', axis='columns').add('\n\t\t').sum()
    reg_class+='\n\n\t\t# fields:\n\t\t'
    reg_class+=df.apply(lambda r: f'self.{r.Reg_Name + "." + r.Field_Name:<50} = self.field_class(slice({r.Bits.split(":")[1]}, {int(r.Bits.split(":")[0]) + 1}))', axis='columns').add('\n\t\t').sum()
    number_of_new_lines=reg_class.count("\n")
    expander_python=st.beta_expander(f'show python code for registers ({number_of_new_lines} lines)')
    expander_python.code(reg_class)

