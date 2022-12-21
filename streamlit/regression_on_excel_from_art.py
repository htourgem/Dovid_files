import pandas as pd
import io
import numpy as np
import streamlit as st
# from tqdm import tqdm
# tqdm.pandas()
import plotly.express as px
from sklearn.ensemble import RandomForestRegressor
import datetime
from sys import platform
import cufflinks
from glob import glob
st.set_page_config(layout="wide")
import sys, os
repo_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

debug_from_win=False
plot_width=1000
if "win" in platform:
    debug_from_win=True


def convert_si(si):
    import si_prefix  #pip install si-prefix
    si_prefix.SI_PREFIX_UNITS='yzafpnum kMGTPEZY' # to replace µ with u
    if str(type(si))=="<class 'pandas.core.series.Series'>":
        si=si.to_list()
    try:
        if type(si)==list:
            return list(map(si_prefix.si_parse,si))
        else:
            return si_prefix.si_parse(si)
    except:
        return si


def plotme(df, x, y):
    return df.set_index(x)[y].figure(xTitle=x, title=f'{", ".join(y)} vs {x}')


def fix_subplots(fig, also_to_y=True):
    fig=fig.update_traces(mode='lines+markers')
    fig=fig.update_xaxes(matches=None)
    if also_to_y:
        fig=fig.update_yaxes(matches=None)
    fig=fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    fig=fig.update_yaxes(showticklabels=True, title=dict(text=''))
    fig=fig.update_annotations(font=dict(size=24, family='Calibri', color='darkblue'))
    return fig


def get_signal_fft(sr): # input sr with value vs time. return magnitude and phase in radians
    x=sr.index.values
    y=sr.values
    #col_name=str(sr.name)
    N = len(x)//2*2
    T=round((x[-1]-x[0])/(N-1),13)  # assume uniform spacing, but doing average. round for avoiding floating point precision

#     '''y - energy:'''
    yf = np.fft.fft(y)  # or better use np.fft.rfft and save next line
    yf = 2.0 / N * yf[0:1+N // 2]
    magnitude=np.abs(yf)
    #if you get 0, you will have error at log10… so you can add this.. 
    #magnitude[magnitude==0]=magnitude[magnitude!=0].min()
    magnitude_db=20*np.log10(magnitude)
    angle=(np.angle(yf)+np.pi/2)%(2*np.pi)
#     '''x - frequencies:'''
    max_freq = 1.0 / (2.0 * T)
    xf = np.linspace(0, max_freq, len(yf),endpoint=True) # BTW, you have np.fft.fftfreq
    res=pd.DataFrame([xf,magnitude_db,magnitude,angle],index=['freq',"mag_db",'mag_voltage',"phase_rad"]).T.set_index('freq')
    return res


st.sidebar.markdown('**_SODA_** - Second Order Displayed Analysis')
if not debug_from_win:
    st.sidebar.image(repo_path + '/streamlit/regression_on_excel_from_art.jpg', use_column_width=True)

current_date=datetime.datetime.now().strftime('%d-%m-%Y-%H_%M_%S')

if not debug_from_win:
    with open(f'{os.path.dirname(os.path.abspath(__file__))}/demo_data/regression_on_excel_from_art/regression_on_excel_from_art_usage_log.txt','a') as f:
        f.write(current_date+'\n')


st.header('---plots from multi tests---')
st.subheader('this app is parsing downloaded excel with multiple tests from ART and plotting cross tests')
is_under_development=st.sidebar.checkbox('development code')

demo_excel=st.sidebar.selectbox('or load demo data', ['']+[i.split('/')[-1] for i in glob(repo_path + 'streamlit/demo_data/regression_on_excel_from_art/demo_*.xlsx')])
if demo_excel!='':
    st.error('loading demo data!')
    st.sidebar.error('loading demo data!')
    uploaded_file=repo_path + f'/streamlit/demo_data/regression_on_excel_from_art/{demo_excel}'
else:
    uploaded_file=st.sidebar.file_uploader('upload xlsx/csv file that you downloaded from ART (at csv remove intel confidential first row)', type=['xlsx', 'csv'])

if uploaded_file is None:
    st.error('please upload file')
    st.stop()
try:
    df=pd.read_csv(uploaded_file)
except:
    old_format_header = st.sidebar.checkbox('old ART format with "intel confidential" at first row')
    sheets=pd.read_excel(uploaded_file, None, header=[int(old_format_header)])
    sheet=st.sidebar.selectbox('choose sheet to run on', list(sheets.keys())) if len(list(sheets.keys()))>1 else list(sheets.keys())[0]
    df=sheets[sheet]

    
if 'had_indicator_update' not in df.columns or df.had_indicator_update.isna().sum():
    st.write(f'all data ({df.shape[0]} rows, {df.shape[1]} columns)')
    st.write(df)
    st.write('first row:')
    st.write(df.iloc[0])
    if 'had_indicator_update' not in df.columns:
        st.error('please run "update indicators" before using this tool')
        st.stop()
    if df.had_indicator_update.isna().sum()!=0:
        st.error('some of the rows at the excel did had "update indicators". please run "update indicators" and download again the excel')
        st.stop()
# if not df.query('analysis_type==None').empty:
#     st.write('you have rows with analysis types of None, so droppign thsoe lines')
#     df=df.query('analysis_type==None')
if df.analysis_type.unique().shape[0]!=1:
    st.error(f'you have mixture of analysis in you table -  {df.analysis_type.unique().tolist()}')
    st.stop()

# input_type=st.sidebar.radio('select input type',['raw sine','raw prbs', '128 UI'])
input_type=df.analysis_type.iloc[0]
st.sidebar.subheader(f'detecting analysis as ***_{input_type}_*** by analysis_type column')

if 0:
    df.to_csv(f'{os.path.dirname(os.path.abspath(__file__))}/demo_data/regression_on_excel_from_art/input_excel_{current_date}.csv')
corner='tttt,acff_hot_hc,acff_cold_hc,acff_lc,acff_hot_lc,acss_cold_lc,acss_hot_lc,acss_cold_lowr_hc,acss_hot_lowr_hc,acss_hc,acss_cold_hc,affs_cold_lc,affs_hot_lc_hv,affs_cold_hc,afsf_hot_lc_lv,afsf_cold_lc_hv,asfs_hot_hc_lv,asfs_cold_hc_lv,assf_hot_hc_hv,assf_cold_lc_lv,aslow_hot_hc,aslow_cold_hc,aslow_hot_lc,aslow_cold_lc,afast_cold_hc,afast_hot_hc,afast_cold_lc,afast_hot_lc,acff_hot_lc333'.split(',')

if 'corner' not in df.columns and 'corner_num' in df.columns:
    st.write('*** no corner column at the excel*** using some enumerated list of corners from falcon instead')
    ## commenting out this line for now, this corner list is not up to date, and should not be fixed
    #df['corner']=df.corner_num.apply(lambda x: corner[x-1])
    df['corner']=df.corner_num
df=df.apply(convert_si)

with st.beta_expander('original table'):
    st.write(df)
    columns_in_simple_view = st.multiselect('select specific columns to view', df.columns.tolist())
    st.write(df.loc[:, columns_in_simple_view])


with st.beta_expander('some boring tables'):
    st.header('fixing table and stat on columns')
    boring_columns=df.nunique().to_frame('number_of_unique').query('number_of_unique<2').index.tolist()
    st.write(f'dropping those {len(boring_columns)} boring columns:')
    st.write(df[boring_columns].iloc[0].to_frame('single value for this column'))
    tmp=df.drop(columns=boring_columns)
    boring_columns=list(set(boring_columns)-set(['amp_by_fft', 'enob_by_fft', 'thd', 'error_std_mv_by_cf','sfdr','enob_by_sar', 'enob_by_interleave', 'max_ps_offset', 'sar_max_min_dc_range','sar_max_min_amp_range', 'max_sar_error','sampling_rate_ghz', 'number_of_sars_in_use']))
    df=df.drop(columns=boring_columns)

    tmp=df.describe()
    st.write(f'{df.shape[1]} numeric columns:')
    st.write(tmp)
    tmp=df.describe(include=np.object)
    st.write(f'{tmp.shape[1]} non numric columns:')
    st.write(tmp)
    st.write(f'after drop, data has ({df.shape[0]} rows, {df.shape[1]} columns)')
    st.write(df)
    st.write('left columns:')
    st.write(df.columns.sort_values())



if 'sessiondescription' in df.columns and df.sessiondescription.unique().shape[0]>1:
    with st.beta_expander('sessions that we have at this excel'):
        sessions=df.sessiondescription.value_counts().rename('rows per session')
        st.write(sessions)
        session=st.sidebar.multiselect('select sessions that you want to run on', sessions.index.tolist(), default=sessions.index[0])
        df=df.query('sessiondescription==@session')

with st.beta_expander('dynamic plot'):
    unique_key=0
    while True:
        col1, col2 = st.beta_columns(2)
        all_columns=df.columns.tolist()
        x=col1.selectbox('choose x for plot', [None]+all_columns, key=unique_key)
        y=col2.multiselect('choose y for plot', all_columns, None, key=unique_key)
        if x is None or not len(y):
            st.header('='*40)
            break
        fig=plotme(df=df.sort_values(x), x=x, y=y)
        st.write(fig)
        unique_key+=1
                                     
                                     
                                     
if is_under_development:
    pass

st.sidebar.info('filtering out some data:')
# relevant_columns=df[df.dtypes.loc[df.dtypes=='object'].index.values].nunique().to_frame('count').query(f'{df.shape[0]}>count>1')
relevant_columns=df.nunique().to_frame('count').query('100>count>1') # .query(f'{df.shape[0]}>=count>1')
if is_under_development:
    st.header('relevant_columns')
    st.write(relevant_columns)
    st.write(df[df.dtypes.loc[df.dtypes=='object'].index.values].nunique().to_frame('count'))
if relevant_columns.empty:
#     relevant_columns=df[df.dtypes.loc[df.dtypes=='object'].index.values].nunique().to_frame('count')
    relevant_columns=df.nunique().to_frame('count')

columns=st.sidebar.multiselect(f'pick columns to filter' , relevant_columns.index.values)
column_content=dict()
for column in columns:
    column_content[column] = st.sidebar.multiselect(f'choose values to display at {column}', df[column].unique())
for column in columns:
    if len(column_content[column]):
        df=df.query(f'{column} in {column_content[column]}')






optional_x_axis=df.drop(columns=['amp_by_fft', 'enob_by_fft', 'thd', 'error_std_mv_by_cf','sfdr'], errors='ignore').select_dtypes('number').columns.tolist()
default_x=list(set(['freq_ghz_by_cf', 'freq_ghz']) & set(optional_x_axis))
if not len(default_x):
    default_x=0
else:
    default_x=optional_x_axis.index(default_x[0])
with st.beta_expander('set x and pivot column for next plots'):
    col1, col2 = st.beta_columns(2)
    x_axis_first_plots = col1.selectbox('choose column that will be the x axis for the next bunch of plots (usually take freq)', optional_x_axis, default_x)

    col1.subheader('next columns will not be an option at pivot as they have only 1 option or more than 100 options:')
    col1.write(df.drop(columns=relevant_columns, errors='ignore').nunique().to_frame('count').sort_values('count'))
    pivot_columns=col2.multiselect(f'pick columns for pivot' , relevant_columns.sort_index().index.tolist())
    if len(pivot_columns):
        df['pivot_columns']=df[pivot_columns].astype(str).add('_:_').sum(1).str[:-3]
        if df.pivot_columns.str.len().max()<30:
            df['pivot_columns_number']=df.pivot_columns
        else:
            df['pivot_columns_number']='group '+df.groupby('pivot_columns').ngroup(ascending=True).astype(str)
            st.write(f'pivot name too long - maximum of {df.pivot_columns.str.len().max()} characters, so replacing pivot with this table:')
            st.write(df[pivot_columns+['pivot_columns','pivot_columns_number']].groupby('pivot_columns_number').first().sort_index())
        # df.pivot_columns_number=df.corner
        if df.pivot_columns_number.value_counts().max()>1:
            col2.warning(' warning - you have more than 1 match at some of you pivots, taking only first one and dropping the others')
            col2.write(df.pivot_columns_number.value_counts().rename('number of rows per pivot'))
            if col2.checkbox('do you want to drop duplicates at the pivot?'):
                df=df.groupby('pivot_columns_number', as_index=False).first()
            st.write(df)
        df=df.sort_values('pivot_columns_number')

    else:
        df=df.assign(pivot_columns_number='-')
sorted_pivot_columns_number = sorted(df.pivot_columns_number.unique())
target_indicator=None                        
                                     
                                     
                        
                                     
                                     
                                     
                                     
                                     
                                     
                                     
                                     
                                     
                                     
                                     
                                     
                                     
                                     
                                     
                                     
                                     
                                     
                                     
                                     
if input_type=='sine_parts':
    df.rawdata=df.rawdata.apply(eval)
    target_indicator='enob_by_interleave'
        
        
    with st.beta_expander(f'indicators vs {x_axis_first_plots}'):
        df_plot=df.melt(id_vars=[x_axis_first_plots, 'pivot_columns_number'], value_vars=['interleave_amp', 'enob_by_interleave', 'rmse_by_interleave'], value_name='val', var_name='indicator').sort_values(x_axis_first_plots)
        fig = px.line(df_plot, x=x_axis_first_plots, y='val', facet_col='indicator', facet_col_wrap=2, 
                      color='pivot_columns_number', text='indicator', title='general indicators', height=700, width=plot_width,
                      category_orders=dict(pivot_columns_number=sorted_pivot_columns_number))
        fig=fix_subplots(fig)
        st.write(fig)

    with st.beta_expander('more indicators'):
        df_plot=df.melt(id_vars=[x_axis_first_plots, 'pivot_columns_number'], value_vars=['enob_by_sar', 'enob_by_interleave', 'max_ps_offset', 'sar_max_min_dc_range','sar_max_min_amp_range', 'max_sar_error'], value_name='val', var_name='indicator').sort_values(x_axis_first_plots)  #enob_wo_spurs_by_fft
        fig = px.line(df_plot, x=x_axis_first_plots, y='val', facet_col='indicator', facet_col_wrap=2, color='pivot_columns_number', text='indicator',
                      title='more indicators', height=700, width=plot_width,
                      category_orders=dict(indicator=['enob_by_sar', 'enob_by_interleave', 'max_ps_offset', 'sar_max_min_dc_range','sar_max_min_amp_range', 'max_sar_error'], pivot_columns_number=sorted_pivot_columns_number))
        fig=fix_subplots(fig)
        fig.update_yaxes(range=[0, 6], showticklabels=True, row=3, col=1)
        fig.update_yaxes(range=[0, 6], showticklabels=True, row=3, col=2)
        st.write(fig)



    with st.beta_expander('specific frequency'):
        freq=st.selectbox('pick frequency that you want to see the raw data of it', df.freq_ghz.sort_values().round(1).unique())
        a=df.query('freq_ghz.round(1)==@freq')[['sampling_rate_ghz','pivot_columns_number','rawdata']].explode('rawdata')
        a['time_ns']=a.groupby('pivot_columns_number').cumcount()/a.sampling_rate_ghz
        st.write(px.scatter(a, x='time_ns', y='rawdata', color='pivot_columns_number', title=f'raw data at {freq} GHz', marginal_y="histogram", width=plot_width))
        st.write(px.histogram(a, x='rawdata', color='pivot_columns_number', nbins=64, histnorm='probability density', marginal="rug", barmode='group', title=f'code/voltage histogram at {freq} GHz', width=plot_width))

    

    
    
                                     
                                     
if input_type=='dc_noise':
    st.write('dc noise - under construction')
    with st.beta_expander(f'indicators per sar'):
        dc_noise_df_sar = pd.DataFrame()
#         color_names = st.selectbox('choose column to be color for the next plot', df.columns.tolist())
        for col in 'sar_data_mv_std,sar_data_mv_min,sar_data_mv_max,sar_data_mv_avg,sar_mv_p2p'.split(','):
            if col in df.columns:
                tmp=df[[col, 'pivot_columns_number']].copy().rename(columns={col:'value'})
                tmp.value = tmp.value.apply(eval)
                tmp = tmp.explode('value')
                tmp['sar']=np.arange(tmp.shape[0])%64
                tmp['value_type'] = col
                dc_noise_df_sar = dc_noise_df_sar.append(tmp)
            else:
                st.warning(f'expecting to find columns {col} at dc_noise analysis output, but cannot find it. skipping it')
        fig = px.line(dc_noise_df_sar.sort_values('sar'), x='sar', y='value', facet_row='value_type', color='pivot_columns_number', height = 1000, width = plot_width, title='indicators per sar per pivot')
        fig=fix_subplots(fig)
        st.write(fig)
    with st.beta_expander(f'indicators per oct'):
        dc_noise_df_oct = pd.DataFrame()
#         color_names = st.selectbox('choose column to be color for the next plot', df.columns.tolist())
        for col in 'oct_data_mv_std,oct_data_mv_min,oct_data_mv_max,oct_data_mv_avg,oct_mv_p2p'.split(','):
            if col in df.columns:
                tmp=df[[col, 'pivot_columns_number']].copy().rename(columns={col:'value'})
                tmp.value = tmp.value.apply(eval)
                tmp = tmp.explode('value')
                tmp['oct']=np.arange(tmp.shape[0])%16
                tmp['value_type'] = col
                dc_noise_df_oct = dc_noise_df_oct.append(tmp)
            else:
                st.warning(f'expecting to find columns {col} at dc_noise analysis output, but cannot find it. skipping it')
        fig = px.line(dc_noise_df_oct.sort_values('oct'), x='oct', y='value', facet_row='value_type', color='pivot_columns_number', height = 1000, width = plot_width, title='indicators per oct per pivot')
        fig=fix_subplots(fig)
        st.write(fig)
    
    
    
    
if input_type=='sine':
    df.rawdata=df.rawdata.apply(eval)
    target_indicator='enob_by_fft'
        
        
    with st.beta_expander(f'indicators vs {x_axis_first_plots}'):
        df_plot=df.melt(id_vars=[x_axis_first_plots, 'pivot_columns_number'], value_vars=['amp_by_fft', 'enob_by_fft', 'thd', 'error_std_mv_by_cf','sfdr','sar_gain_mismatch_percentages'], value_name='val', var_name='indicator').sort_values(x_axis_first_plots)
        fig = px.line(df_plot, x=x_axis_first_plots, y='val', facet_col='indicator', facet_col_wrap=2, color='pivot_columns_number', text='indicator', title='general indicators', height=700, width=plot_width, category_orders=dict(indicator=['amp_by_fft', 'enob_by_fft', 'thd', 'sfdr', 'error_std_mv_by_cf','sar_gain_mismatch_percentages'], pivot_columns_number=sorted_pivot_columns_number))
        fig=fix_subplots(fig)
        st.write(fig)

    with st.beta_expander('enob indicators'):
        df_plot=df.melt(id_vars=[x_axis_first_plots, 'pivot_columns_number'], value_vars=['enob_by_cf_per_oct', 'enob_by_fft', 'enob_by_cf_per_sar', 'enobi_by_fft_ignore'], value_name='val', var_name='indicator').sort_values(x_axis_first_plots)  #enob_wo_spurs_by_fft
        fig = px.line(df_plot, x=x_axis_first_plots, y='val', facet_col='indicator', facet_col_wrap=2, 
                      color='pivot_columns_number', text='indicator',
                      title='enob indicators', height=700, width=plot_width, 
                      category_orders=dict(pivot_columns_number=sorted_pivot_columns_number))
        fig=fix_subplots(fig)
        fig.update_yaxes(range=[0, 6], showticklabels=True)
        st.write(fig)
                 
    with st.beta_expander('more plots by given x'):
        more_y = st.multiselect('if you want more plots, by the given x axis and groups, please select additional y axis:', optional_x_axis)
        if len(more_y):
            df_plot=df.melt(id_vars=[x_axis_first_plots, 'pivot_columns_number'], value_vars=more_y, value_name='val', var_name='indicator').sort_values(x_axis_first_plots)  #enob_wo_spurs_by_fft
            fig = px.line(df_plot, x=x_axis_first_plots, y='val', facet_col='indicator', facet_col_wrap=2, 
                          color='pivot_columns_number', text='indicator',
                          title='more indicators', height=700, width=plot_width, 
                          category_orders=dict(pivot_columns_number=sorted_pivot_columns_number))
            fig=fix_subplots(fig)
            st.write(fig)



    with st.beta_expander('specific frequency'):
        freq=st.selectbox('pick frequency that you want to see the raw data of it', df.freq_ghz_by_cf.sort_values().round(1).unique())
        a=df.query(f'freq_ghz_by_cf.round(1)=={freq}',engine="python")[['sampling_rate_ghz','number_of_sars_in_use','pivot_columns_number','rawdata']].explode('rawdata')
        a['time_ns']=a.groupby('pivot_columns_number').cumcount()/a.sampling_rate_ghz
        st.write(px.scatter(a, x='time_ns', y='rawdata', color='pivot_columns_number', title=f'raw data at {freq} GHz', marginal_y="histogram", width=plot_width))
        st.write(px.histogram(a, x='rawdata', color='pivot_columns_number', nbins=64, histnorm='probability density', marginal="rug", barmode='group', title=f'code/voltage histogram at {freq} GHz', width=plot_width))
        if 1:
            st.header('fft')
            fft=[]
            for name, g in a.groupby('pivot_columns_number'):
                fft.append(get_signal_fft(pd.Series(g.rawdata.values*1.816*np.blackman(g.shape[0]), index=np.arange(g.rawdata.shape[0])*g.time_ns.iloc[1])).assign(pivot=name))
            fft=pd.concat(fft).sort_index()
            st.write(px.line(fft, y='mag_db', color='pivot', width=plot_width))
    #         fft=a.groupby('pivot_columns_number', as_index=False).apply(lambda g: get_signal_fft(pd.Series(g.rawdata, index=np.arange(len(g.rawdata))*g.time_ns.iloc[0])))
        else:
            fft=a.groupby('pivot_columns_number').apply(lambda g: pd.Series(np.fft.rfft(g.rawdata), index=np.fft.rfftfreq(n=g.rawdata.shape[0], d=g.time_ns.iloc[1])).abs().apply(np.log10)*20)
            fft=fft.T.rename_axis(index='freq_GHz').reset_index()
            fft=fft.melt(id_vars='freq_GHz', value_name='amp_db', var_name='pivot_columns_number')
        #     st.write(fft.apply(np.real))
            st.write(px.line(fft, x='freq_GHz', y='amp_db', color='pivot_columns_number', title='fft', width=plot_width))
        st.header('raw data per sar:')
        a['sar']='sar '+(a.groupby('pivot_columns_number').cumcount()%a.number_of_sars_in_use).astype(str)
        st.write(px.scatter(a, x='time_ns', y='rawdata', color='sar',facet_col='pivot_columns_number', facet_col_wrap=2, title='raw data per sar', height=700, width=plot_width))
    if 0:
        with st.beta_expander('raw data for each sar at specific test'):
            single_row=st.slider('select index to plot', 0, df.shape[0])
            single_row=df.iloc[single_row]
            st.write(single_row)
            number_of_sars_in_use=single_row.number_of_sars_in_use
            single_row=pd.DataFrame(single_row.rawdata, columns=['code'])
            single_row['sar']='sar '+(single_row.index%number_of_sars_in_use).astype(str)
            st.write(px.scatter(single_row, y='code', color='sar'))
    
    
    
if input_type=='square_wave':
    df.rawdata=df.rawdata.apply(eval)
    target_indicator='tie_std_ps'
#     if is_under_development:
    a=df[['sampling_rate_ghz','pivot_columns_number','rawdata']].explode('rawdata').sort_values('pivot_columns_number').reset_index(drop=True)
    a['time_ns']=a.index/a.sampling_rate_ghz
    with st.beta_expander('raw data'):
        st.write(px.scatter(a, x='time_ns', y='rawdata', color='pivot_columns_number', title=f'raw data', marginal_y="histogram", width=plot_width))
        st.write(a.pivot_columns_number.value_counts().rename('samples at raw data per pivot'))   
    
    
    
    
if input_type=='prbs':
    df.rawdata=df.rawdata.apply(eval)
#     if is_under_development:
    target_indicator='snr_db'
    df.all_taps=df.all_taps.apply(eval)
    a=df[['sampling_rate_ghz','pivot_columns_number','rawdata']].explode('rawdata').sort_values('pivot_columns_number').reset_index(drop=True)
    a['time_ns']=a.index/a.sampling_rate_ghz
    with st.beta_expander('raw data'):
        st.write(px.scatter(a, x='time_ns', y='rawdata', color='pivot_columns_number', title=f'raw data', marginal_y="histogram", width=plot_width))
        st.write(a.pivot_columns_number.value_counts().rename('samples at raw data per pivot'))
    with st.beta_expander('histogram'):
        st.write(px.histogram(a, x='rawdata', color='pivot_columns_number', histnorm='probability density', marginal="rug", barmode='group', title=f'code/voltage histogram', width=plot_width))
    with st.beta_expander('pulse respond'):
        a=df[['sampling_rate_ghz','pivot_columns_number','all_taps']].explode('all_taps').reset_index()
        a.all_taps=a.all_taps.astype(float)
        a['tap_place']=a.groupby('pivot_columns_number').cumcount()
        def ab(g):
            return g.loc[g.all_taps.idxmax()].tap_place
        a['main_tap']=a.groupby('pivot_columns_number', group_keys=False).apply(lambda g: g.assign(m=ab(g))).m
        a['tap_number']=a.tap_place-a.main_tap
    #     st.write(a)
    #     st.write(a.groupby('pivot_columns_number').all_taps.count())
    #     st.write(df.all_taps)
        st.write(px.line(a, x='tap_number', y='all_taps', color='pivot_columns_number', title=f'pulse response', width=plot_width))
    
    
    with st.beta_expander('some indicators'):
        df_plot=df.melt(id_vars=['pivot_columns_number'], value_vars=['non_linear_snr_db', 'snr_db', 'eye_height_div_by_amp'], value_name='val', var_name='indicator')  #enob_wo_spurs_by_fft
        fig = px.line(df_plot, x='pivot_columns_number', y='val', facet_col='indicator', facet_col_wrap=1, text='indicator', 
                      title='some indicators', height=700, width=plot_width,
                      category_orders=dict(pivot_columns_number=sorted_pivot_columns_number))
        fig=fix_subplots(fig)
        st.write(fig)
    with st.beta_expander('transfer function'):
        st.write("in development in my spare time")
        def fft_on_signal(signal, time_between_samples=None):
            ''' if time_between_samples is None, the freq will be the number of full cycle,
                for example, if you have single ton sine, with 11 full cycles, you will get argmax to be 11 (0 is DC)
                radians will be from -pi to +pi
            '''
            import pandas as pd
            import numpy as np
        
            fft = pd.DataFrame()
            n = len(signal)
            fft['fft'] = np.fft.fft(signal)## * 2  # don’t know why this function divides output by 2…
            #fft['radians'] = np.unwrap(np.angle(fft.fft))%(np.pi)
            #fft["amp"] = fft.fft.abs()## / n
            # fft.loc[fft.amp<1e-10, 'amp]=1e-10  # if you do db on amb, log on 0 is inf, so replacing with -200 db
            # fft['mag_db'] = 20 * fft.amp.apply(np.log10)
            #fft['freq'] = np.fft.rfftfreq(n=n, d=1 / n if time_between_samples is None else time_between_samples)
            return fft

        def getTF(df, inputx, outputx):
            output_data = df.query("log_path.str.contains(@outputx)",engine='python').rawdata.iloc[0]
            input_data = df.query("log_path.str.contains(@inputx)", engine='python').rawdata.iloc[0]
            tf= fft_on_signal(output_data).fft / fft_on_signal(input_data).fft
            tf = tf.to_numpy().tolist()
            pulse_response = np.real(np.fft.ifft(tf))
            pulse_response=pulse_response/max(pulse_response)
            return pulse_response

        #st.write(pivot_columns)
        #st.write(df)
        if len(pivot_columns):
            choice = st.selectbox('Do you want to run experimental code?', ["No way","Go for it"])
            if choice == "Go for it":
                columnWithTf=st.selectbox('pick pivot column with inputs and outputs', pivot_columns)
                inputX=st.selectbox('select input', [None]+df[columnWithTf].unique().tolist())
                outputX=st.selectbox('select output', [None]+df[columnWithTf].unique().tolist())
                if inputX and outputX:
                    new_pivot_columns = pivot_columns
                    new_pivot_columns.remove(columnWithTf)
                                             
                    tf = df.groupby(new_pivot_columns).apply(getTF, inputx=inputX, outputx=outputX).reset_index()
                    tf.rename(columns={0:"pulse_response"},inplace=True)
                    #st.write(tf.head())                                     
                    #st.write(df[new_pivot_columns])                                     
                    tf['new_pivot_columns']=tf[new_pivot_columns].astype(str).add('_:_').sum(1).str[:-3]
                    if tf.new_pivot_columns.str.len().max()<30:
                        tf['new_pivot_columns_number']=tf.new_pivot_columns
                    else:
                        tf['new_pivot_columns_number']='group '+tf.groupby('new_pivot_columns').ngroup(ascending=True).astype(str)

                    #st.write(tf.new_pivot_columns_number)                                     
                    a=tf[['new_pivot_columns_number','pulse_response']].explode('pulse_response').reset_index(drop=True)
                    a['tap_place']=a.groupby('new_pivot_columns_number').cumcount()
                    #st.write(a.head())                                     
                    #st.write(a.tail())                                     
                    fig = px.line(a, x='tap_place', y='pulse_response', color='new_pivot_columns_number', title=f'pulse response')
                    st.write(fig)
                                     
                                     
                                     
                                     
                                     
                                     
                                     
                                     
if input_type=='sine_histogram':
#     df.rawdata=df.rawdata.apply(pd.read_csv)
    target_indicator='sine_amp_by_std_mean'
    with st.beta_expander(f'indicators vs {x_axis_first_plots}'):
        df_plot=df.melt(id_vars=[x_axis_first_plots, 'pivot_columns_number'], value_vars=['offset_mean', 'offset_mismatch', 'sine_amp_by_std_mean', 'sine_amp_mismatch'], value_name='val', var_name='indicator').sort_values(x_axis_first_plots)
        fig = px.line(df_plot, x=x_axis_first_plots, y='val', facet_col='indicator', facet_col_wrap=2, 
                      color='pivot_columns_number', text='indicator', title='general indicators', height=700, width=plot_width, 
                      category_orders=dict(indicator=['offset_mean', 'offset_mismatch', 'sine_amp_by_std_mean', 'sine_amp_mismatch'], pivot_columns_number=sorted_pivot_columns_number))
        fig=fix_subplots(fig)
        st.write(fig)
    with st.beta_expander('hist edges'):
        all_hists=pd.DataFrame()
        for inx,row in df.iterrows():
            tmp=pd.read_csv(io.StringIO(row.rawdata))
            tmp=tmp.set_index('sar').stack().rename('hits').reset_index(drop=False).rename(columns=dict(level_1='code')).astype(int)
            tmp=tmp.query('hits!=0').assign(row_number=inx)
            tmp=tmp.groupby('sar').code.agg(max_code='max', min_code='min', p2p=np.ptp).reset_index(drop=False)
            all_hists=all_hists.append(tmp.assign(row_number=inx)).reset_index(drop=True)
        all_hists=all_hists.melt(id_vars=['sar', 'row_number'], value_vars=['min_code','max_code','p2p'], value_name='val', var_name='indicator').sort_values(['sar','row_number'])
        fig=px.line(all_hists, x='sar', color='row_number', y='val', facet_col='indicator', facet_col_wrap=2, title='hist edges', height=700, width=plot_width, category_orders=dict(indicator=['min_code','max_code','p2p']))
        fig=fix_subplots(fig)
        st.write(fig)
    if 0:
        with st.beta_expander('hist edges'):
            col1, col2 = st.beta_columns(2)
            line=col1.selectbox('select row to plot', range(df.shape[0]))
            st.write('presenting this row:')
            row_to_show=df.iloc[line]
            st.write(row_to_show)
            row_to_show=pd.read_csv(io.StringIO(df.iloc[line].rawdata))
            row_to_show=row_to_show.set_index('sar').stack().rename('hits').reset_index(drop=False).rename(columns=dict(level_1='code'))
            row_to_show=row_to_show.astype(int).query('hits!=0').groupby('sar').code.agg(max_code='max', min_code='min', p2p=np.ptp)
            st.write(px.line(row_to_show, width=plot_width))
                       
                                     
                          
                                     
                                     
                                     
                                     
                                     
                                     
if input_type=='prbs_histogram':
#     df.rawdata=df.rawdata.apply(pd.read_csv)
    target_indicator='ber_in_gb_prbs_mean'
    st.header(f'indicators vs {x_axis_first_plots}')
    df_plot=df.melt(id_vars=[x_axis_first_plots, 'pivot_columns_number'], value_vars=['ber_in_gb_prbs_mean'], value_name='val', var_name='indicator').sort_values(x_axis_first_plots)
    fig = px.line(df_plot, x=x_axis_first_plots, y='val', facet_col='indicator', facet_col_wrap=2, 
                  color='pivot_columns_number', text='indicator', title='general indicators', height=700, width=plot_width,
                  category_orders=dict(pivot_columns_number=sorted_pivot_columns_number))
    fig=fix_subplots(fig)
    st.write(fig)
                                     
                                     
                                     
                                     
            
                                     
                                     
                                     
                                     
                                     
                                     
                                     
                                     
                                     
                                     
if target_indicator is None:
    st.error('didnt find supported analysis at the excel')
    st.stop()

x=df.select_dtypes('number').dropna(axis=1).drop(columns=target_indicator)
y=df[target_indicator]            
model = RandomForestRegressor(max_depth = 5, max_features=15, min_samples_leaf=2, n_estimators=100 ,random_state=0)
model.fit(x, y)
best_features=pd.DataFrame(model.feature_importances_, index=x.columns, columns=['feature_score']).sort_values('feature_score', ascending=False)
if best_features.feature_score.sum():
    with st.beta_expander(f'features that most impacts {target_indicator}, running on {df.shape[0]} rows'):
        st.write(best_features)
