import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import utm

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="German Texas Heritage",
    page_icon="🇩🇪",
    layout="wide"
)

# --- 2. CUSTOM CSS ---
st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    [data-testid="stSidebar"] {
        min-width: 350px;
        max-width: 500px;
    }
    div.stMetric {
        background-color: #f5f5f5;
        border: 1px solid #e6e6e6;
        padding: 10px;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. TITLE SECTION ---
st.title("🇩🇪 The German Belt Navigator v2")
st.markdown("""
    Between 1830 and 1900, thousands of German immigrants settled in Texas, with the majority settling in Central Texas. 
    This interactive map uses historical data to visualize their legacy.
""")
st.markdown("Note: Data source - Texas Historical Commission (Jan 2026)")

# --- 4. DATA LOADING FUNCTION ---
@st.cache_data
def load_data():
    # Load the Raw File
    df = pd.read_csv("german_sites_full.csv", encoding='latin1')
    
    # Rename Columns
    df = df.rename(columns={'MarkerTex': 'MarkerText', 'marker_text': 'MarkerText'})
    
    # Remove Duplicates
    df = df.drop_duplicates(subset=['Title', 'City'], keep='first')

    # Filter for German Keywords
    keywords = ["German", "Verein", "Prussia", "Deutsch", "Adelsverein", "Liederkranz", "Alsatian"]
    pattern = '|'.join(keywords)
    df = df[
        df['Title'].str.contains(pattern, case=False, na=False) | 
        df['MarkerText'].str.contains(pattern, case=False, na=False)
    ]

    # Convert Coordinates (UTM -> Latitude/Longitude)
    def get_lat_lon(row):
        try:
            if pd.notnull(row.get('latitude')) and pd.notnull(row.get('longitude')):
                return pd.Series([row['latitude'], row['longitude']])
            lat, lon = utm.to_latlon(row['Utm_East'], row['Utm_North'], 14, 'R')
            return pd.Series([lat, lon])
        except:
            return pd.Series([None, None])

    df[['latitude', 'longitude']] = df.apply(get_lat_lon, axis=1)
    
    # Final Cleanup
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df = df.dropna(subset=['latitude', 'longitude'])
    
    return df

# --- 5. LOAD DATA ---
df = load_data()

# --- 6. SIDEBAR SETUP ---
st.sidebar.write("---")
st.sidebar.write(f"📂 Rows Loaded: {len(df)}")
st.sidebar.write(f"📄 File Used: german_sites_full.csv")

with st.sidebar:
    st.header("🔍 Explore the History")
    
    if st.button("🔄 Force Reload"):
        st.rerun()

 #   st.markdown("---")
 #   st.subheader("🕵️ Data Detective")

    # Duplicate Hunter
    # NEW (Smart)
  #  dupes = df[df.duplicated(subset=['Title', 'City'], keep=False)]
  #  if not dupes.empty:
  #      st.error(f"Found {len(dupes)} entries sharing the same name!")
  #      st.dataframe(dupes[['Title', 'City']].sort_values(by='Title'), height=150)
  #  else:
  #         st.success("No duplicates found based on Name.")

    st.markdown("---")
    st.subheader("Filter Options")

    # Slider
    min_year = 1800
    max_year = 2024
    year_range = st.slider("Year Established", min_year, max_year, (1800, 2024))

    # Category Filter
    categories = ["All", "Dance Hall", "School", "Church", "Cemetery", "Verein", "Saloon", "Store"]
    selected_category = st.selectbox("Select Category", categories)
    
    # Search Filter
    search_query = st.text_input("Search by Name", placeholder="e.g., Schmidt...")

# --- 7. MAIN APP LOGIC ---
with st.spinner('Filtering data and redrawing map...'):
    
    # A. FILTER DATA
    filtered_df = df.copy()

    # Year Filter
    filtered_df = filtered_df[
        (filtered_df['Year'].between(year_range[0], year_range[1])) | 
        (filtered_df['Year'].isna())
    ]

    # Category Filter
    if selected_category != "All":
        filtered_df = filtered_df[
            filtered_df['Title'].str.contains(selected_category, case=False, na=False) | 
            filtered_df['MarkerText'].str.contains(selected_category, case=False, na=False)
        ]

    # Search Filter
    if search_query:
        filtered_df = filtered_df[filtered_df['Title'].str.contains(search_query, case=False, na=False)]

    # B. DISPLAY METRICS
    col1, col2 = st.sidebar.columns(2)
    col1.metric("Total Sites", len(filtered_df))
    
    if not filtered_df.empty and 'County' in filtered_df.columns:
        try:
            top_county = filtered_df['County'].dropna().mode().iloc[0]
            col2.metric("Top County", top_county)
        except:
            col2.metric("Top County", "N/A")
    else:
        col2.metric("Top County", "N/A")

    # C. DRAW MAP
    m = folium.Map(location=[30.27, -98.87], zoom_start=7, tiles="CartoDB positron")
    marker_cluster = MarkerCluster(options={'spiderfyOnMaxZoom': False}).add_to(m)

    for idx, row in filtered_df.head(2000).iterrows():
        try:
            # Get Description
            desc = str(row.get('MarkerText', ''))
            if desc == "nan" or desc == "None" or desc == "":
                desc = "No details available."

            # Popup HTML
            popup_html = f"""
            <div style="width: 300px; font-family: sans-serif;">
                <b>{row['Title']}</b><br>
                <i style="color: gray;">{row.get('City', 'Texas')}</i>
                <hr style="margin: 5px 0;">
                <div style="height: 150px; overflow-y: auto; font-size: 14px;">
                    {desc}
                </div>
            </div>
            """

            # Color Logic
            color = 'blue'
            full_text = str(row['Title']) + " " + desc
            if 'Dance' in full_text: color = 'red'
            elif 'Church' in full_text: color = 'purple'
            elif 'School' in full_text: color = 'green'
            elif 'Cemetery' in full_text: color = 'gray'

            # Add Marker
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=folium.Popup(popup_html, max_width=350),
                icon=folium.Icon(color=color, icon="info-sign")
            ).add_to(marker_cluster)

        except Exception:
            continue

# --- 8. DISPLAY MAP (OUTSIDE THE LOOP) ---
st_folium(m, width=1200, height=600)
