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
    This interactive map uses historical data to visualize their legacy in the form of historical markers that can be found throughout the state. You can filter specific historical markers using the tab on the left.  
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
    
    # Category Filter
    categories = ["All", "Dance Hall", "School", "Church", "Cemetery", "Verein", "Saloon", "Store"]
    selected_category = st.selectbox("Select Category", categories)
    
    # Search Filter
    search_query = st.text_input("Search by Name", placeholder="e.g., Schmidt, Krause...")
    
    st.markdown("---")
    st.markdown("### About")
    st.info("Built with Python & Streamlit. Data courtesy of the Texas Historical Commission.")

# TIME TRAVEL SLIDER
    min_year = 1800
    max_year = 2024
    
    year_range = st.sidebar.slider("Year Established", min_year, max_year, (1850, 1900))

# MANUAL REFRESH BUTTON
if st.sidebar.button("🔄 Reload Map"):
    st.rerun()

# 6. FILTERING LOGIC
filtered_df = df.copy()

if selected_category != "All":
    filtered_df = filtered_df[
        filtered_df['Title'].str.contains(selected_category, case=False, na=False) | 
        filtered_df['MarkerText'].str.contains(selected_category, case=False, na=False)
    ]

if search_query:
    filtered_df = filtered_df[filtered_df['Title'].str.contains(search_query, case=False, na=False)]

# 7. DASHBOARD METRICS (The "Pro" Touch)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Sites Found", len(filtered_df))
with col2:
    # Try to find the most common city in the filtered results
    if not filtered_df.empty and 'City' in filtered_df.columns:
        top_city = filtered_df['City'].mode()[0]
        st.metric("Top Hub", top_city)
    else:
        st.metric("Top Hub", "N/A")
with col3:
    st.metric("Category", selected_category)

# Filter by Year (Keep sites within range OR sites with unknown years)
    filtered_df = filtered_df[
        (filtered_df['Year'].between(year_range[0], year_range[1])) | 
        (filtered_df['Year'].isna())
    ]

# 8. THE MAP
# We use 'CartoDB positron' for a clean, professional look that makes data pop
m = folium.Map(location=[30.27, -98.87], zoom_start=7, tiles="CartoDB positron")
marker_cluster = MarkerCluster().add_to(m)

# Limit markers to prevent crashing on huge datasets
for idx, row in filtered_df.head(2000).iterrows():
    folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=f"<b>{row['Title']}</b><br>{row.get('City', 'Texas')}",
        tooltip=row['Title'],
        icon=folium.Icon(color="darkblue", icon="info-sign")
    ).add_to(marker_cluster)

st_folium(m, width=None, height=600)

# 9. DATA TABLE
with st.expander("📂 View Raw Data Record"):
    st.dataframe(filtered_df)
