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

st.set_page_config(layout="wide")
st.title("Geolocation Method Comparison")

# Load Excel file
excel_file = "Diverse geolokasjoner.xlsx"
xl = pd.ExcelFile(excel_file)
sheet_names = xl.sheet_names

# Sidebar for global settings
with st.sidebar:
    st.header("Global Settings")
    # Method selection (allow up to 4 methods)
    num_methods = st.radio("Number of methods to compare", [2, 3, 4], horizontal=True)
    selected_methods = []
    method_colors = []
    
    for i in range(num_methods):
        col1, col2 = st.columns([3, 1])
        with col1:
            method = st.selectbox(
                f"Method {i+1}",
                sheet_names,
                key=f"method_{i}"
            )
            selected_methods.append(method)
        with col2:
            color = st.color_picker(
                "Color",
                ['#1E88E5', '#FFC107', '#4CAF50', '#9C27B0'][i],
                key=f"color_{i}"
            )
            method_colors.append(color)
    
    cluster_radius = st.slider("Cluster Radius", 10, 100, 50)
    cluster_max_zoom = st.slider("Max Zoom for Clustering", 1, 18, 12)

# Load data for all selected methods
method_data = {}
for method, color in zip(selected_methods, method_colors):
    df = xl.parse(method)
    if 'Latitude' in df.columns and 'Longitude' in df.columns:
        df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
        df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
        df = df.dropna(subset=['Latitude', 'Longitude'])
        method_data[method] = {'df': df, 'color': color}

# Calculate overall center
all_lats = []
all_lons = []
for data in method_data.values():
    all_lats.extend(data['df']['Latitude'])
    all_lons.extend(data['df']['Longitude'])
center_lat = np.mean(all_lats)
center_lon = np.mean(all_lons)

# Create tabs for different visualization modes
# Replace the tabs section with:

# Create tabs for different visualization modes
tab1, tab2, tab3 = st.tabs([
    "Single Map (All Methods)", 
    "Grid View (Compare Methods)", 
    "Base Map Comparison"
])

with tab1:
    # Single map with all methods as toggleable layers
    col1, col2 = st.columns([1, 3])
    
    with col1:
        basemap = st.selectbox("Basemap", BASEMAP_OPTIONS, key='single_map')
        st.write("Toggle layers using the layer control in the map")
    
    with col2:
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
        
        # Add each method as a separate layer
        for method in selected_methods:
            data = method_data[method]
            cluster = MarkerCluster(
                name=f"{method}",
                maxClusterRadius=cluster_radius,
                disableClusteringAtZoom=cluster_max_zoom
            ).add_to(m)
            
            for _, row in data['df'].iterrows():
                folium.Marker(
                    location=[row['Latitude'], row['Longitude']],
                    popup=folium.Popup(f"{method}: {row['Term']}", parse_html=True),
                    icon=folium.Icon(color=data['color'].lstrip('#')),
                    tooltip=f"{row['Term']}"
                ).add_to(cluster)
        
        folium.LayerControl().add_to(m)
        m.to_streamlit(height=600)
        
        # Add method counts below map
        st.write("Method Counts:")
        for method in selected_methods:
            st.write(f"- {method}: {len(method_data[method]['df'])} locations")

with tab2:
    # Grid view of multiple maps
    cols = st.columns(2)  # 2x2 grid
    maps = []
    
    for i, (method, data) in enumerate(list(method_data.items())[:4]):  # Max 4 maps
        with cols[i % 2]:
            st.subheader(method)
            m = leafmap.Map(
                center=(center_lat, center_lon),
                zoom=5,
                height=400
            )
            
            cluster = MarkerCluster(
                name=f"{method} Locations",
                maxClusterRadius=cluster_radius,
                disableClusteringAtZoom=cluster_max_zoom
            ).add_to(m)
            
            for _, row in data['df'].iterrows():
                folium.Marker(
                    location=[row['Latitude'], row['Longitude']],
                    popup=folium.Popup(f"{method}: {row['Term']}", parse_html=True),
                    icon=folium.Icon(color=data['color'].lstrip('#')),
                    tooltip=f"{row['Term']}"
                ).add_to(cluster)
            
            m.to_streamlit(height=400)
            st.write(f"Total locations: {len(data['df'])}")

with tab3:
    # Base map comparison (split view)
    if len(selected_methods) >= 2:
        col1, col2, col3 = st.columns([1, 2, 2])
        
        with col1:
            st.write("Compare different base maps:")
            left_basemap = st.selectbox("Left Base Map", BASEMAP_OPTIONS, key='split_left')
            right_basemap = st.selectbox("Right Base Map", BASEMAP_OPTIONS, key='split_right')
            method = st.selectbox("Select Method to Display", selected_methods, key='split_method')
        
        # Left map
        with col2:
            st.subheader(f"{left_basemap}")
            data = method_data[method]
            
            m_left = leafmap.Map(
                center=(center_lat, center_lon),
                zoom=5
            )
            
            if left_basemap.startswith("Stamen"):
                m_left.add_tile_layer(
                    url=f"https://stamen-tiles-{{s}}.a.ssl.fastly.net/{left_basemap.split('.')[1].lower()}/{{z}}/{{x}}/{{y}}.png",
                    name=left_basemap,
                    attr='Map tiles by <a href="http://stamen.com">Stamen Design</a>'
                )
            else:
                m_left.add_basemap(left_basemap)
            
            # Add markers
            cluster = MarkerCluster(
                name=f"{method} Locations",
                maxClusterRadius=cluster_radius,
                disableClusteringAtZoom=cluster_max_zoom
            ).add_to(m_left)
            
            for _, row in data['df'].iterrows():
                folium.Marker(
                    location=[row['Latitude'], row['Longitude']],
                    popup=folium.Popup(f"{method}: {row['Term']}", parse_html=True),
                    icon=folium.Icon(color=data['color'].lstrip('#')),
                    tooltip=f"{row['Term']}"
                ).add_to(cluster)
            
            m_left.to_streamlit(height=600)
        
        # Right map
        with col3:
            st.subheader(f"{right_basemap}")
            
            m_right = leafmap.Map(
                center=(center_lat, center_lon),
                zoom=5
            )
            
            if right_basemap.startswith("Stamen"):
                m_right.add_tile_layer(
                    url=f"https://stamen-tiles-{{s}}.a.ssl.fastly.net/{right_basemap.split('.')[1].lower()}/{{z}}/{{x}}/{{y}}.png",
                    name=right_basemap,
                    attr='Map tiles by <a href="http://stamen.com">Stamen Design</a>'
                )
            else:
                m_right.add_basemap(right_basemap)
            
            # Add same markers to right map
            cluster = MarkerCluster(
                name=f"{method} Locations",
                maxClusterRadius=cluster_radius,
                disableClusteringAtZoom=cluster_max_zoom
            ).add_to(m_right)
            
            for _, row in data['df'].iterrows():
                folium.Marker(
                    location=[row['Latitude'], row['Longitude']],
                    popup=folium.Popup(f"{method}: {row['Term']}", parse_html=True),
                    icon=folium.Icon(color=data['color'].lstrip('#')),
                    tooltip=f"{row['Term']}"
                ).add_to(cluster)
            
            m_right.to_streamlit(height=600)
# Add comparison statistics
with st.expander("Comparison Statistics"):
    # Basic stats
    stats_df = pd.DataFrame({
        'Method': selected_methods,
        'Total Locations': [len(method_data[m]['df']) for m in selected_methods],
        'Unique Terms': [method_data[m]['df']['Term'].nunique() for m in selected_methods]
    })
    st.dataframe(stats_df)
    
    # Term overlap analysis
    if len(selected_methods) > 1:
        st.subheader("Term Overlap")
        all_terms = [set(method_data[m]['df']['Term']) for m in selected_methods]
        common_terms = set.intersection(*all_terms)
        st.write(f"Terms found in all methods: {len(common_terms)}")