import streamlit as st

import pandas as pd

import folium

from folium.plugins import MarkerCluster

from streamlit_folium import st_folium

import utm



# 1. PAGE CONFIGURATION 

st.set_page_config(

    page_title="German Texas Heritage",

    page_icon="🇩🇪",

    layout="wide"

)



# 2. CUSTOM CSS 

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

        background-color: #808080;

        border: 1px solid #e6e6e6;

        padding: 10px;

        border-radius: 5px;

    }

    </style>

    """, unsafe_allow_html=True)



# 3. TITLE SECTION

st.title("🇩🇪 The German Belt Navigator v2")

st.markdown("""

    Between 1830 and 1900, thousands of German immigrants settled in Texas, with the majority settling in Central Texas. This region is also known as the Texas Hill Country.

    This interactive map uses historical data to visualize their legacy in the form of historical markers that can be found throughout the state. You can filter specific historical markers below, as well as specific year ranges using the tab on the left. 

""")

st.markdown("""Note: Data is accurate based on Texas Historical Commission/Texas Historic Sites Atlas as of Jan. 2026  """)

##st.sidebar.write("---")

##st.sidebar.write(f"📂 Rows Loaded: {len(df)}")

##st.sidebar.write(f"📄 File Used: german_sites_full.csv") # Just text, but helps us check version



# 4. LOAD DATA

@st.cache_data

def load_data():

    # Load the Raw File (using latin1 for special characters)

    df = pd.read_csv("german_sites_full.csv", encoding='latin1')

    

    # Rename Columns to standard names

    df = df.rename(columns={'MarkerTex': 'MarkerText', 'marker_text': 'MarkerText'})

    

    # Remove Duplicates 

    df = df.drop_duplicates(subset=['Title', 'City'], keep='first')



    # Filter for German Keywords (The "Gold Sifter")

    keywords = ["German", "Verein", "Prussia", "Deutsch", "Adelsverein", "Liederkranz", "Alsatian"]

    pattern = '|'.join(keywords)

    df = df[

        df['Title'].str.contains(pattern, case=False, na=False) | 

        df['MarkerText'].str.contains(pattern, case=False, na=False)

    ]



    # Convert Coordinates (UTM -> Latitude/Longitude)

    def get_lat_lon(row):

        try:

            # If GPS already exists, use it

            if pd.notnull(row.get('latitude')) and pd.notnull(row.get('longitude')):

                return pd.Series([row['latitude'], row['longitude']])

            # Otherwise convert UTM

            lat, lon = utm.to_latlon(row['Utm_East'], row['Utm_North'], 14, 'R')

            return pd.Series([lat, lon])

        except:

            return pd.Series([None, None])



    df[['latitude', 'longitude']] = df.apply(get_lat_lon, axis=1)

    # Manual override for broken sites:

    mask = df['Title'].str.contains("Geroge Washington Savage", case=False, na=False)

    if mask.any():
            df.loc[mask, 'latitude'] = 31.9185
            df.loc[mask, 'longitude'] = -96.8970
    # Final Cleanup

    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')

    df = df.dropna(subset=['latitude', 'longitude'])

    

    return df


df = load_data()


# 5. SIDEBAR FILTERS

with st.sidebar:

    st.sidebar.header("🔍 Explore the History")





# 1. The Refresh Button

    if st.sidebar.button("🔄 Force Reload"):

        st.rerun()





# --- DUPLICATE HUNTER 

#st.sidebar.markdown("---")

#st.sidebar.subheader("🕵️ Data Detective")



# 1. Check for Duplicate Titles

#dupes = df[df.duplicated(subset=['Title', 'City'], keep=False)]



#if not dupes.empty:

#    st.sidebar.error(f"Found {len(dupes)} entries sharing the same name!")

    # Show the first few duplicates so you can identify them

#    st.sidebar.write(dupes[['Title', 'City']].sort_values(by='Title'), height =150)

#else:

#    st.sidebar.success("No duplicates found based on Name.")







# 2. The Slider Definition

min_year = 1800

max_year = 2024

year_range = st.sidebar.slider("Year Established", min_year, max_year, (1800, 2024))





    # Category Filter

categories = ["All", "Dance Hall", "School", "Church", "Cemetery", "Verein", "Saloon", "Store"]

selected_category = st.sidebar.selectbox("Select Category", categories)

    

    # Search Filter

search_query = st.sidebar.text_input("Search by Name", placeholder="e.g., Schmidt, Krause...")

    



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

    # --- PASTE THIS REPLACEMENT BLOCK ---

    

    # Create two columns side-by-side in the sidebar

    col1, col2 = st.sidebar.columns(2)

    

    # Metric 1: Total Count

    col1.metric("Total Sites", len(filtered_df))

    

    # Metric 2: Top County (The Data Science Part)

    # We check if data exists, then find the 'mode' (most common value)

    if not filtered_df.empty and 'County' in filtered_df.columns:

        try:

            top_county = filtered_df['County'].dropna().mode().iloc[0]

            col2.metric("Top County", top_county)

        except:

            col2.metric("Top County", "N/A")

    else:

        col2.metric("Top County", "N/A")

        

    # ------------------------------------



    # C. DRAW MAP

    m = folium.Map(location=[30.27, -98.87], zoom_start=7, tiles="CartoDB positron")

    

    # Faster clustering options

    marker_cluster = MarkerCluster(options={'spiderfyOnMaxZoom': False}).add_to(m)



for idx, row in filtered_df.head(2000).iterrows():



        try: 



        # --- EVERYTHING BELOW MUST BE INDENTED ---



        



        # 1. GET DESCRIPTION



            desc = str(row.get('MarkerText', ''))



            if desc == "nan" or desc == "None" or desc == "":



                desc = "No additional details available."







        # 2. CREATE HTML POPUP



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







        # 3. COLOR LOGIC



            color = 'blue'



            full_text = str(row['Title']) + " " + desc



            if 'Dance' in full_text: color = 'red'



            elif 'Church' in full_text: color = 'purple'



            elif 'School' in full_text: color = 'green'

            elif 'Cemetery' in full_text: color = 'gray'





    # 4. DRAW THE MARKER



            folium.Marker(



                location=[row['latitude'], row['longitude']],



                popup=folium.Popup(popup_html, max_width=350),



                icon=folium.Icon(color=color, icon="info-sign")



                ).add_to(marker_cluster)



        except Exception:



            continue



    # Display Map



st_folium(m, width=None, height=600, returned_objects=[])
