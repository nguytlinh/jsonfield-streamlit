import streamlit as st
from pathlib import Path
import requests
import pandas as pd
from pandas.io.json import json_normalize
import base64

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

st.header("CRIM Project Meta Data Viewer (JSONField)")

st.subheader("These tools assemble metadata for about 5000 observations in Citations: The Renaissance Imitation Mass")
st.write("Visit the [CRIM Project](https://crimproject.org) and its [Members Pages] (https://sites.google.com/haverford.edu/crim-project/home)")
st.write("Also see the [Relationship Metadata Viewer] (https://crim-relationship-data-viewer.herokuapp.com/)")

# st.cache speeds things up by holding data in cache

@st.cache(allow_output_mutation=True)

# get the data function 
def get_data():
    data = requests.get('http://127.0.0.1:8000/data/observations/').json()
    #df = pd.DataFrame(data)
    df = pd.json_normalize(data)
    return df 
df = get_data()


select_data = df[["id", "observer", "musical_type"]]

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
st.header("Filter Views")
st.write('Use the following dialogues to filter for one or more Analyst, Observation, or Musical Type')
st.write('To download a CSV file with the given results, provide a filename as requested, then click the download button')


st.subheader("Select Observations by Analyst")
obs_list = select_data['observer'].unique().tolist()
obs_selected = st.multiselect('', obs_list)

# Mask to filter dataframe:  returns only those "selected" in previous step
masked_obs = select_data['observer'].isin(obs_selected)

select_data_1 = select_data[masked_obs]
st.write(select_data_1)

s1 = st.text_input('Name of Observer file for download (must include ".csv")')
# Button to download CSV of results 
if st.button('Download Observer Results as CSV'):
    #s = st.text_input('Enter text here')
    tmp_download_link = download_link(select_data_1, s1, 'Click here to download your data!')
    st.markdown(tmp_download_link, unsafe_allow_html=True)


st.markdown("---")


st.subheader("Select Observations by Musical Type")
type_list = select_data['musical_type'].unique().tolist()
types_selected = st.multiselect('', type_list)

# # Mask to filter dataframe:  returns only those "selected" in previous step
masked_types = select_data['musical_type'].isin(types_selected )

select_data_3 = select_data[masked_types]
st.write(select_data_3)

## Button to download CSV of results 
s3 = st.text_input('Name of Musical Type file for download (must include ".csv")')
if st.button('Download Musical Type Results as CSV'):
    tmp_download_link = download_link(select_data_3, s3, 'Click here to download your data!')
    st.markdown(tmp_download_link, unsafe_allow_html=True)


st.markdown("---")

# Function to filter by subfields
def filter_by_subfield(SUBFIELD):
    COL_NAME = 'details.' + SUBFIELD

    select_data_sf = df[["id", "observer", "musical_type", COL_NAME]]

    st.subheader("Select Observations by " + SUBFIELD)
    sf_list = df[COL_NAME].unique().tolist()
    sf_selected = st.multiselect('', sf_list)

    # # Mask to filter dataframe:  returns only those "selected" in previous step
    masked_sf = df[COL_NAME].isin(sf_selected)

    select_data_sf = select_data_sf[masked_sf]
    st.write(select_data_sf)

    ## Button to download CSV of results 
    sf_text = st.text_input(SUBFIELD + ' file for download (must include ".csv")')
    if st.button('Download ' + SUBFIELD + ' results as CSV'):
        tmp_download_link = download_link(select_data_sf, sf_text, 'Click here to download your data!')
        st.markdown(tmp_download_link, unsafe_allow_html=True)

    st.markdown("---")



# Testing 
filter_by_subfield('Number of voices')
filter_by_subfield('Flexed')



