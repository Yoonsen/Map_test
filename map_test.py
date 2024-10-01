import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import time

# Set page config to use full screen
st.set_page_config(layout="wide")

st.title("Testing av forskjellig modeller for geolokasjon")
# Hardcode the Excel file
excel_file = "Diverse geolokasjoner.xlsx"

# Read the Excel file and get sheet names
xl = pd.ExcelFile(excel_file)
sheet_names = xl.sheet_names

# Create a dropdown for sheet selection
select_field, _ = st.columns([2,5])
with select_field:
    sheet = st.selectbox(f"Velg bok (ark fra excel-fil)", sheet_names, help= f"henter data fra {excel_file}")

# Read the selected sheet
df = xl.parse(sheet)


# Check for required columns
if 'Latitude' in df.columns and 'Longitude' in df.columns:
    # Ensure Latitude and Longitude are numeric
    df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
    df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')

    # Drop rows with invalid coordinates
    df = df.dropna(subset=['Latitude', 'Longitude'])

    # Initialize the map at an average location
    m = folium.Map(location=[df['Latitude'].mean(), df['Longitude'].mean()], zoom_start=5)

    # Add markers for each place
    for _, row in df.iterrows():
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=folium.Popup(row['Term'], parse_html=True),
            tooltip=row['Term']  # Tooltip for hover
        ).add_to(m)

    time.sleep(0.5)
    # Display the map
    st_folium(m, width=None, height=800)
else:
    st.write("The selected sheet does not contain 'Latitude' and 'Longitude' columns.")

# Display the DataFrame
st.write(df)
