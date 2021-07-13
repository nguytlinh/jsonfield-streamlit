from requests.sessions import DEFAULT_REDIRECT_LIMIT
import streamlit as st
from pathlib import Path
import requests
import pandas as pd
import numpy as np
import altair as alt
from pandas.io.json import json_normalize
import base64
import SessionState

# sets up function to call Markdown File for "about"
def read_markdown_file(markdown_file):
    return Path(markdown_file).read_text()

def download_link(object_to_download, download_filename, download_link_text):
    """
    Generates a link to download the given object_to_download.

    object_to_download (str, pd.DataFrame):  The object to be downloaded.
    download_filename (str): filename and extension of file. e.g. mydata.csv, some_txt_output.txt
    download_link_text (str): Text to display for download link.

    Examples:
    download_link(YOUR_DF, 'YOUR_DF.csv', 'Click here to download data!')
    download_link(YOUR_STRING, 'YOUR_STRING.txt', 'Click here to download your text!')

    """
    if isinstance(object_to_download,pd.DataFrame):
        object_to_download = object_to_download.to_csv(index=False)

    # some strings <-> bytes conversions necessary here
    b64 = base64.b64encode(object_to_download.encode()).decode()

    return f'<a href="data:file/txt;base64,{b64}" download="{download_filename}">{download_link_text}</a>'


#main heading of the resource

st.header("CRIM Project Meta Data Viewer")

st.subheader("These tools assemble metadata for about 5000 observations in Citations: The Renaissance Imitation Mass")
st.write("Visit the [CRIM Project](https://crimproject.org) and its [Members Pages] (https://sites.google.com/haverford.edu/crim-project/home)")
st.write("Also see the [Relationship Metadata Viewer] (https://crim-relationship-data-viewer.herokuapp.com/)")

# st.cache speeds things up by holding data in cache

@st.cache(allow_output_mutation=True)

# get the data function 
def get_data(link):
    data = requests.get(link).json()
    #df = pd.DataFrame(data)
    df = pd.json_normalize(data)
    return df 


df = get_data('http://crimproject.org/data/observations/')
df.rename(columns={'piece.piece_id':'piece_piece_id'}, inplace=True)

df_r = get_data('http://crimproject.org/data/relationships/')
df_r.rename(columns={'piece.piece_id':'piece_piece_id', 
                    'model_observation.piece.piece_id':'model_observation_piece_piece_id',
                    'derivative_observation.piece.piece_id':'derivative_observation_piece_piece_id',}, inplace=True)

select_data = df[["id", "observer.name", "piece_piece_id", "musical_type"]]
select_data_r = df_r[['id', 'observer.name', 'model_observation_piece_piece_id', 'derivative_observation_piece_piece_id', 'relationship_type']]


# Sidebar options for _all_ data of a particular type

st.sidebar.write('Use checkboxes below to see all data of a given category.  Advanced filtering can be performed in the main window.')

if st.sidebar.checkbox('Show All Metadata Fields'):
    st.subheader('All CRIM Observations with All Metadata')
    st.write(df)

if st.sidebar.checkbox('Show Selected Metadata:  Observer, Type'):
    st.subheader('Selected Metadata:  Observer, Type')
    st.write(select_data)

if st.sidebar.checkbox('Show Total Observations per Analyst'):
    st.subheader('Total Observations per Analyst')
    st.write(df['observer'].value_counts())  


if st.sidebar.checkbox('Show Total Observations per Musical Type'):
    st.subheader('Total Observations per Musical Type')
    st.write(df['musical_type'].value_counts())
  

st.subheader("All Data and MEI Views")
sa = st.text_input('Name of file for download (must include ".csv")')
## Button to download CSV of results 
if st.button('Download Complete Dataset as CSV'):
    #s = st.text_input('Enter text here')
    tmp_download_link = download_link(df, sa, 'Click here to download your data!')
    st.markdown(tmp_download_link, unsafe_allow_html=True)



# These are the filters in the main window 
#st.header("Filter Views")
#st.write('Use the following dialogues to filter for one or more Observer, Piece, Observation, or Musical Type')
#st.write('To download a CSV file with the given results, provide a filename as requested, then click the download button')


#st.subheader("Select Observations by Observer")

#s1 = st.text_input('Name of Observer file for download (must include ".csv")')
# Button to download CSV of results 
#if st.button('Download Observer Results as CSV'):
#    #s = st.text_input('Enter text here')
#    tmp_download_link = download_link(select_data_1, s1, 'Click here to download your data!')
#    st.markdown(tmp_download_link, unsafe_allow_html=True)



#st.markdown("---")

def filter_by(filterer, select_data, full_data, key):
    options = select_data[filterer].unique().tolist()
    selected_options = st.multiselect('', options, key = key)
    list_of_selected = list(selected_options)

    if list_of_selected:
        chosen_columns =  select_data[filterer].isin(selected_options)
        subframe = select_data[chosen_columns]
        fullframe = full_data[chosen_columns]
    else:
        subframe = select_data
        fullframe = full_data
    
    return [fullframe, subframe]

def draw_chart(col_name, count_name, origdf):
    chart_data = origdf.copy()
    chart_data[count_name] = chart_data.groupby(by=col_name)[col_name].transform('count')
    #st.write(chart_data)
    #TODO: Format chart for easier view
    chart = alt.Chart(chart_data).mark_bar().encode(
        x = count_name,
        y = col_name,
    )
    st.write(chart) 

def get_subtype_count(origdf, mt, stname):
    subtype = (origdf['mt_' + mt + '_' + stname] == 1)
    subtype_count = origdf[subtype].shape[0]
    return int(subtype_count)

def get_cdtype_count(origdf, stname):
    subtype = (origdf['mt_cad_type'].isin(stname))
    subtype_count = origdf[subtype].shape[0]
    return int(subtype_count)

def get_subtype_charts(selected_type, origdf):
    if selected_type.lower() == "cadence":
        cd_chosen = (origdf['mt_cad'] == 1)
        cd_full = origdf[cd_chosen]
        cd_dict = {'mt_cad_type':['authentic','phrygian','plagal'],
                    'countcdtypes': [ 
                        get_cdtype_count(cd_full, ['authentic', 'Authentic']),
                        get_cdtype_count(cd_full, ['phrygian', 'Phrygian']),
                        get_cdtype_count(cd_full, ['plagal', 'Plagal']),
                    ]}
        df_cd = pd.DataFrame(data=cd_dict)
        chart_cd = alt.Chart(df_cd).mark_bar().encode(
            x = 'countcdtypes',
            y = 'mt_cad_type',
        )
        st.write(chart_cd)
        draw_chart('mt_cad_tone', 'countcdtones', cd_full)

    if selected_type.lower() == "fuga":
        fg_chosen = (origdf['mt_fg'] == 1)
        fg_full = origdf[fg_chosen]
        fg_dict = {'Subtypes':['periodic', 'strict', 'flexed', 'sequential', 'inverted', 'retrograde'],
                    'count': [
                        get_subtype_count(fg_full, 'fg', 'periodic'), 
                        get_subtype_count(fg_full, 'fg', 'strict'), 
                        get_subtype_count(fg_full, 'fg', 'flexed'), 
                        get_subtype_count(fg_full, 'fg', 'sequential'), 
                        get_subtype_count(fg_full, 'fg', 'inverted'), 
                        get_subtype_count(fg_full, 'fg', 'retrograde'),
                    ]}
        df_fg = pd.DataFrame(data=fg_dict)
        chart_fg = alt.Chart(df_fg).mark_bar().encode(
            x = 'count',
            y = 'Subtypes',
        )
        st.write(chart_fg)
    
    if selected_type.lower() == "periodic entry":
        pe_chosen = (origdf['mt_pe'] == 1)
        pe_full = origdf[pe_chosen]

        pe_dict = {'Subtypes':['strict', 'flexed melodic', 'flexed rhythmic', 'sequential', 'added entry', 'invertible'],
                    'count': [ 
                        get_subtype_count(pe_full, 'pe', 'strict'), 
                        get_subtype_count(pe_full, 'pe', 'flexed'), 
                        get_subtype_count(pe_full, 'pe', 'flt'),
                        get_subtype_count(pe_full, 'pe', 'sequential'), 
                        get_subtype_count(pe_full, 'pe', 'added'), 
                        get_subtype_count(pe_full, 'pe', 'invertible'), 
                    ]}
        df_pe = pd.DataFrame(data=pe_dict)
        chart_pe = alt.Chart(df_pe).mark_bar().encode(
            x = 'count',
            y = 'Subtypes',
        )
        st.write(chart_pe)

    if selected_type.lower() == "imitative duo":
        id_chosen = (origdf['mt_id'] == 1)
        id_full = origdf[id_chosen]
    
        id_dict = {'Subtypes':['strict', 'flexed melodic', 'flexed rhythmic', 'invertible'],
                    'count': [ 
                        get_subtype_count(id_full, 'id', 'strict'), 
                        get_subtype_count(id_full, 'id', 'flexed'), 
                        get_subtype_count(id_full, 'id', 'flt'),
                        get_subtype_count(id_full, 'id', 'invertible'), 
                    ]}
        df_id = pd.DataFrame(data=id_dict)
        chart_id = alt.Chart(df_id).mark_bar().encode(
            x = 'count',
            y = 'Subtypes',
        )
        st.write(chart_id)

    if selected_type.lower() == "non-imitative duo":
        nid_chosen = (origdf['mt_nid'] == 1)
        nid_full = origdf[nid_chosen]

        nid_dict = {'Subtypes':['strict', 'flexed melodic', 'flexed rhythmic', 'invertible'],
                    'count': [ 
                        get_subtype_count(nid_full, 'nid', 'strict'), 
                        get_subtype_count(nid_full, 'nid', 'flexed'), 
                        get_subtype_count(nid_full, 'nid', 'flt'),
                        get_subtype_count(nid_full, 'nid', 'invertible'), 
                    ]}
        df_nid = pd.DataFrame(data=nid_dict)
        chart_nid = alt.Chart(df_nid).mark_bar().encode(
            x = 'count',
            y = 'Subtypes',
        )
        st.write(chart_nid)

    if selected_type.lower() == "homorhythm":
        hr_chosen = (origdf['mt_hr'] == 1)
        hr_full = origdf[hr_chosen]

        hr_dict = {'Subtypes':['simple', 'staggered', 'sequential', 'fauxbourdon'],
                    'count': [ 
                        get_subtype_count(hr_full, 'hr', 'simple'), 
                        get_subtype_count(hr_full, 'hr', 'staggered'), 
                        get_subtype_count(hr_full, 'hr', 'sequential'),
                        get_subtype_count(hr_full, 'hr', 'fauxbourdon'), 
                    ]}
        df_hr = pd.DataFrame(data=hr_dict)
        chart_hr = alt.Chart(df_hr).mark_bar().encode(
            x = 'count',
            y = 'Subtypes',
        )
        st.write(chart_hr)



st.markdown("---")
st.header("OBSERVATION VIEWER")

order = st.radio("Select order to filter data: ", ('Piece then Musical Type', 'Musical Type then Piece'))
if (order == 'Piece then Musical Type'):
    #filter by piece
    st.subheader("Piece")
    piece_frames = filter_by("piece_piece_id", select_data, df, 'a')
    piece_full = piece_frames[0]
    piece_sub = piece_frames[1]
    #st.write(piece_full)
    #st.write(piece_sub)

    #filter by type with or without piece
    st.subheader("Musical Type")
    mt_frames = filter_by('musical_type', piece_sub, piece_full, 'b')
    mt_full = mt_frames[0]
    mt_sub = mt_frames[1]
    st.markdown('Resulting observations:')
    #st.write(mt_full)
    st.write(mt_sub)

    st.write("Graphical representation of result")
    draw_chart("musical_type", "counttype", mt_sub)
    draw_chart("piece_piece_id", "countpiece", mt_sub)
    
    st.write('Subtype charts for filtered results') 
    selected_types = mt_sub['musical_type'].unique().tolist()
    for mt in selected_types:
        if str(mt).lower() in ['cadence', 'fuga', 'periodic entry', 'imitative duo', 'non-imitative duo', 'homorythm']:
            st.write('Type: ' + str(mt))
            get_subtype_charts(mt, mt_full)

else:
    #filter by musical type
    st.subheader("Musical Type")
    mt_frames = filter_by('musical_type', select_data, df, 'z')
    mt_full = mt_frames[0]
    mt_sub = mt_frames[1]
    #st.write(mt_full)

    #filter by piece with or without musical type
    st.subheader("Piece")
    piece_frames = filter_by('piece_piece_id', mt_sub, mt_full, 'y')
    piece_full = piece_frames[0]
    piece_sub = piece_frames[1]
    st.markdown('Resulting observations:')
    st.write(piece_sub)

    st.write("Graphical representation of result")
    draw_chart("musical_type", "counttype", piece_sub)
    #debug in progress for piece
    draw_chart("piece_piece_id", "countpiece", piece_sub)

    st.write('Subtype charts for filtered results') 
    selected_types = piece_sub['musical_type'].unique().tolist()
    for mt in selected_types:
        if str(mt).lower() in ['cadence', 'fuga', 'periodic entry', 'imitative duo', 'non-imitative duo', 'homorythm']:
            st.write('Type: ' + str(mt))
            get_subtype_charts(mt, piece_full)


st.markdown("---")
st.header("Subtype Charts All Data")

type_options = ['Cadence', 'Fuga', 'Periodic Entry', 'Imitative Duo', 'Non-Imitative Duo', 'Homorythm']
selected_type = st.radio('', type_options, key = 'g')
get_subtype_charts(selected_type, df)


st.markdown("---")
st.header("RELATIONSHIP VIEWER")

order = st.radio("Select order to filter data: ", ('Pieces then Relationship Type', 'Relationship Type then Pieces'))
if (order == 'Pieces then Relationship Type'):
    #filter by pieces
    st.subheader("Model Piece")
    mpiece_frames = filter_by("model_observation_piece_piece_id", select_data_r, df_r, 'c')
    mpiece_full = mpiece_frames[0]
    mpiece_sub = mpiece_frames[1]

    st.subheader("Derivative Piece")
    dpiece_frames = filter_by("derivative_observation_piece_piece_id", mpiece_sub, mpiece_full, 'd')
    dpiece_full = dpiece_frames[0]
    dpiece_sub = dpiece_frames[1]

    #filter by type with or without pieces
    st.subheader("Relationship Type")
    rt_frames = filter_by('relationship_type', dpiece_sub, dpiece_full, 'e')
    rt_full = rt_frames[0]
    rt_sub = rt_frames[1]
    st.markdown('Resulting relationships:')
    #st.write(rt_full)
    st.write(rt_sub)

    st.write("Graphical representation of result")
    draw_chart("relationship_type", "counttype", rt_sub)
    draw_chart("model_observation_piece_piece_id", "countmpiece", rt_sub)
    draw_chart("derivative_observation_piece_piece_id", "countdpiece", rt_sub)

else:
    #filter by musical type
    st.subheader("Relationship Type")
    rt_frames = filter_by('relationship_type', select_data_r, df_r, 'x')
    rt_full = rt_frames[0]
    rt_sub = rt_frames[1]
    #st.write(rt_full)

    #filter by piece with or without musical type
    st.subheader("Model Piece")
    mpiece_frames = filter_by('model_observation_piece_piece_id', rt_sub, rt_full, 'w')
    mpiece_full = mpiece_frames[0]
    mpiece_sub = mpiece_frames[1]
    #st.write(mpiece_sub)

    st.subheader("Derivative Piece")
    dpiece_frames = filter_by('derivative_observation_piece_piece_id', mpiece_sub, mpiece_full, 'v')
    dpiece_full = dpiece_frames[0]
    dpiece_sub = dpiece_frames[1]
    st.markdown('Resulting relationships:')
    st.write(dpiece_sub)

    st.write("Graphical representation of result")
    draw_chart("model_observation_piece_piece_id", "countmpiece", dpiece_sub)
    draw_chart("derivative_observation_piece_piece_id", "countdpiece", rt_sub)
    draw_chart("relationship_type", "counttype", dpiece_sub)

