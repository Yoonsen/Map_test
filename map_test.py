import streamlit as st
import pandas as pd
import numpy as np
import leafmap.foliumap as leafmap
from folium.plugins import MarkerCluster
import folium

def dataframe_with_selections(df, key_prefix):
    df_with_selections = df.copy()
    df_with_selections.insert(0, "Select", False)
    edited_df = st.data_editor(
        df_with_selections,
        hide_index=True,
        column_config={"Select": st.column_config.CheckboxColumn(required=True)},
        disabled=df.columns,
        key=f"editor_{key_prefix}"
    )
    selected_indices = list(np.where(edited_df['Select'])[0])
    return selected_indices, edited_df

def hex_to_folium_color(hex_color):
    # Convert hex to RGB
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    # Define basic Folium colors and their RGB values
    folium_colors = {
        'red': (255, 0, 0),
        'blue': (0, 0, 255),
        'green': (0, 128, 0),
        'purple': (128, 0, 128),
        'orange': (255, 165, 0),
        'darkred': (139, 0, 0),
        'lightred': (255, 128, 128),
        'darkblue': (0, 0, 139),
        'darkgreen': (0, 100, 0),
        'cadetblue': (95, 158, 160),
        'darkpurple': (148, 0, 211),
        'pink': (255, 192, 203),
        'lightblue': (173, 216, 230),
        'lightgreen': (144, 238, 144)
    }
    
    # Find closest color using Euclidean distance
    min_distance = float('inf')
    closest_color = 'blue'  # default
    
    for name, rgb in folium_colors.items():
        distance = sum((c1 - c2) ** 2 for c1, c2 in zip((r, g, b), rgb))
        if distance < min_distance:
            min_distance = distance
            closest_color = name
    
    return closest_color
@st.cache_data()
def sheet_display(df):
    term_counts = df[['Term']].groupby('Term').size().reset_index(name='Count')
    return term_counts

# Define available basemaps
BASEMAP_OPTIONS = [
    "OpenStreetMap.Mapnik",
    "CartoDB.Positron",
    "CartoDB.DarkMatter",
    "Stadia.StamenTerrain",
    "Esri.WorldImagery",
    "Esri.WorldStreetMap",
    "Esri.WorldTopoMap"
]

color_mapping = {
    '#1E88E5': 'blue',
    '#FFC107': 'orange',
    '#4CAF50': 'green',
    '#9C27B0': 'purple'
}

st.set_page_config(layout="wide")
st.title("Geolocation Compare")

# Load Excel file

excel_file = "Diverse geolokasjoner.xlsx"

xl = pd.ExcelFile(excel_file)

sheet_names = xl.sheet_names

col1, col_map = st.columns([1, 3])
# Sidebar for global settings
with col1:
    st.header("Global Settings")
    # book selection (allow up to 4 books)
    num_books = 2 #st.radio("Number of books to compare", [2, 3, 4], horizontal=True)
    selected_books = []
    book_colors = []
    
    for i in range(num_books):
        col1, col1b = st.columns([2, 2])
        with col1:
            book = st.selectbox(
                f"Book {i+1}",
                sheet_names,
                key=f"book_{i}"
            )
            selected_books.append(book)
        with col1b:
            color = st.color_picker(
                "Color",
                ['#1E88E5', '#FFC107'][i],
                key=f"color_{i}"
            )
            book_colors.append(color)
    

        book_data = {}
        
        for book, color in zip(selected_books, book_colors):
            df = xl.parse(book)
            if 'Latitude' in df.columns and 'Longitude' in df.columns:
                df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
                df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
                df = df.dropna(subset=['Latitude', 'Longitude'])
                book_data[book] = {'df': df, 'color': hex_to_folium_color(color)}
                
                # Calculate overall center
                all_lats = []
                all_lons = []
                for data in book_data.values():
                    all_lats.extend(data['df']['Latitude'])
                    all_lons.extend(data['df']['Longitude'])
                center_lat = np.mean(all_lats)
                center_lon = np.mean(all_lons)
        
                cluster_radius =  10 #st.slider("Cluster Radius", 10, 100, 50)
                cluster_max_zoom = 18 # st.slider("Max Zoom for Clustering", 1, 18, 12)
    

    basemap = st.selectbox("Basemap", BASEMAP_OPTIONS, key='single_map')
    st.write("Toggle layers using the layer control in the map")

with col_map:
    m = leafmap.Map(
        center=(center_lat, center_lon),
        zoom=5
    )
    
    # Apply the selected basemap
    if basemap.startswith("Stamen"):
        m.add_tile_layer(
            url=f"https://stamen-tiles-{{s}}.a.ssl.fastly.net/{basemap.split('.')[1].lower()}/{{z}}/{{x}}/{{y}}.png",
            name=basemap,
            attr='Map tiles by <a href="http://stamen.com">Stamen Design</a>'
        )
    else:
        m.add_basemap(basemap)
    
    # Add each book as a separate layer
    for book in selected_books:
        data = book_data[book]
        cluster = MarkerCluster(
            name=f"{book}",
            maxClusterRadius=cluster_radius,
            disableClusteringAtZoom=cluster_max_zoom
        ).add_to(m)
        
        for _, row in data['df'].iterrows():
            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                popup=folium.Popup(f"{book}: {row['Term']}", parse_html=True),
                icon=folium.Icon(color=data['color'].lstrip('#')),
                tooltip=f"{row['Term']}"
            ).add_to(cluster)

    folium.LayerControl().add_to(m)
    m.to_streamlit(height=600)
    
    # Add book counts below map
    st.write("book Counts:")
    for book in selected_books:
        st.write(f"- {book}: {len(book_data[book]['df'])} locations")



    # Add comparison statistics
    
    # Basic stats
    stats_df = pd.DataFrame({
        'book': selected_books,
        'Total Locations': [len(book_data[m]['df']) for m in selected_books],
        'Unique Terms': [book_data[m]['df']['Term'].nunique() for m in selected_books]
    })
    st.dataframe(stats_df)
    
    # Term overlap analysis
    if len(selected_books) > 1:
        st.subheader("Term Overlap")
        all_terms = [set(book_data[m]['df']['Term']) for m in selected_books]
        common_terms = set.intersection(*all_terms)
        st.write(f"Terms found in all books: {len(common_terms)}")