import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import time
from folium.plugins import MarkerCluster


#@st.cache_resource
def create_map(data):
    # Initialize the map at an average location
    m = folium.Map(location=[data['Latitude'].mean(), data['Longitude'].mean()], zoom_start=5)
    
    # Create a marker cluster with spiderfy behavior enabled
    marker_cluster = MarkerCluster(
        spiderfyOnMaxZoom=True,  # Allow clusters to expand on click
        disableClusteringAtZoom=8  # Also disable clustering at a closer zoom level
    ).add_to(m)
    
    # Add markers for each place with both pop-up and tooltip
    for _, row in data.iterrows():
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=row['Term'],
            tooltip=row['Term']
        ).add_to(marker_cluster)
    
    return m
    
# Set page config to use full screen
st.set_page_config(layout="wide")

st.title("Testing av forskjellig modeller for geolokasjon")
# Hardcode the Excel file
excel_file = "Diverse geolokasjoner.xlsx"

# Read the Excel file and get sheet names
xl = pd.ExcelFile(excel_file)
sheet_names = xl.sheet_names

# Create a dropdown for sheet selection
select_field, map_field = st.columns([1,6])
with select_field:
    sheet = st.selectbox(f"Velg bok (ark fra excel-fil)", sheet_names, help= f"henter data fra {excel_file}")
    df = xl.parse(sheet)
    display = df[['Term']]
    st.write(display, use_container_with=True)
# Read the selected sheet


with map_field:
    # Check for required columns
    if 'Latitude' in df.columns and 'Longitude' in df.columns:
        # Ensure Latitude and Longitude are numeric
        df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
        df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
    
        # Drop rows with invalid coordinates
        df = df.dropna(subset=['Latitude', 'Longitude'])
    
        # Generate the map and cache it
        map_object = create_map(df)
        
        # Display the map
        # Display the map with return value to enable full interactivity
        st_data = st_folium(map_object, width=None, height=900, key="map_render", returned_objects=[])
    else:
        st.write("The selected sheet does not contain 'Latitude' and 'Longitude' columns.")

# Display the DataFrame

