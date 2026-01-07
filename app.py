import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

# 1. PAGE CONFIGURATION (Browser Tab Title & Icon)
st.set_page_config(
    page_title="German Texas Heritage",
    page_icon="🇩🇪",
    layout="wide"
)

# 2. CUSTOM CSS (To make it look polished)
st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    div.stMetric {
        background-color: #808080;
        border: 1px solid #e6e6e6;
        padding: 10px;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. TITLE SECTION
st.title("🇩🇪 The German Belt Navigator")
st.markdown("""
    Between 1830 and 1900, thousands of German immigrants settled in Texas, with the majority settling in Central Texas. This region is also known as the Texas Hill Country.
    This interactive map uses historical data to visualize their legacy in the form of historical markers that can be found throughout the state. You can filter specific historical markers, as well as specific year ranges using the tab on the left.  
""")

# 4. LOAD DATA
@st.cache_data
def load_data():
    df = pd.read_csv("german_sites_cleaned.csv")
    # We assume there is a 'year' or similar column. If not, we skip date metrics.
    # Force the Year column to be numbers (turns "1850?" into NaN)
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    return df

try:
    df = load_data()
except:
    st.error("⚠️ Data file not found. Please upload 'german_sites_cleaned.csv' to your repository.")
    st.stop()

# 5. SIDEBAR FILTERS
with st.sidebar:
    st.header("🔍 Explore the History")

    # --- START OF MISSING CODE ---

# 1. The Refresh Button
if st.sidebar.button("🔄 Force Reload"):
    st.rerun()

# 2. The Slider Definition
# We MUST create 'year_range' here so the code below can use it!
min_year = 1800
max_year = 2024
year_range = st.sidebar.slider("Year Established", min_year, max_year, (1840, 1900))

# --- END OF MISSING CODE ---
    # Category Filter
categories = ["All", "Dance Hall", "School", "Church", "Cemetery", "Verein", "Saloon", "Store"]
    selected_category = st.selectbox("Select Category", categories)
    
    # Search Filter
    search_query = st.text_input("Search by Name", placeholder="e.g., Schmidt, Krause...")
    
  # --- PASTE THIS BELOW 'search_query = ...' ---

# 4. THE BIG SPINNER WRAPPER
with st.spinner('Filtering data and redrawing map...'):
    
    # A. FILTER THE DATA
    filtered_df = df.copy()

    # Filter by Year (Keep sites in range OR sites with unknown years)
    filtered_df = filtered_df[
        (filtered_df['Year'].between(year_range[0], year_range[1])) | 
        (filtered_df['Year'].isna())
    ]

    # Filter by Category
    if selected_category != "All":
        filtered_df = filtered_df[
            filtered_df['Title'].str.contains(selected_category, case=False, na=False) | 
            filtered_df['MarkerText'].str.contains(selected_category, case=False, na=False)
        ]

    # Filter by Search
    if search_query:
        filtered_df = filtered_df[filtered_df['Title'].str.contains(search_query, case=False, na=False)]

    # B. UPDATE COUNTER (Now accurate!)
    st.sidebar.markdown(f"### Found {len(filtered_df)} Sites")

    # C. DRAW MAP
    m = folium.Map(location=[30.27, -98.87], zoom_start=7, tiles="CartoDB positron")
    
    # Faster clustering options
    marker_cluster = MarkerCluster(options={'spiderfyOnMaxZoom': False}).add_to(m)

    for idx, row in filtered_df.head(2000).iterrows():
        color = 'blue'
        text = str(row['Title']) + str(row.get('MarkerText', ''))
        
        if 'Dance' in text: color = 'red'
        elif 'Church' in text: color = 'purple'
        elif 'School' in text: color = 'green'
        
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=f"<b>{row['Title']}</b><br>{row.get('City','')}",
            icon=folium.Icon(color=color, icon="info-sign")
        ).add_to(marker_cluster)

    # Display Map
    st_folium(m, width=None, height=600)
