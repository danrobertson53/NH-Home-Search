import streamlit as st
import pandas as pd

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="NH Real Estate Finder", page_icon="🌲", layout="wide")

# Custom CSS for a professional look
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    .stButton>button { width: 100%; background-color: #2E86C1; color: white; }
    .metric-card { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

st.title("🌲 New Hampshire Property Search")
st.markdown("### Upload your 'Default MLS Defined Spreadsheet' to begin")

# --- 2. FILE UPLOADER ---
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=['csv'])

if uploaded_file is not None:
    try:
        # Load the data
        df = pd.read_csv(uploaded_file)

        # --- DATA CLEANING (Crucial for MLS Exports) ---
        # 1. Clean Price: Remove '$' and ',' and convert to number
        if df['Price'].dtype == 'O': # Check if it's text (Object)
            df['Clean_Price'] = df['Price'].astype(str).str.replace(r'[$,]', '', regex=True)
            df['Clean_Price'] = pd.to_numeric(df['Clean_Price'], errors='coerce').fillna(0)
        else:
            df['Clean_Price'] = df['Price']

        # 2. Clean SqFt: Remove ',' if present
        if 'SqFtTotFn' in df.columns:
            df['Clean_SqFt'] = df['SqFtTotFn'].astype(str).str.replace(',', '', regex=False)
            df['Clean_SqFt'] = pd.to_numeric(df['Clean_SqFt'], errors='coerce').fillna(0)
        else:
            df['Clean_SqFt'] = 0

        # --- 3. DYNAMIC SIDEBAR FILTERS ---
        st.sidebar.header("🔍 Filter Properties")
        
        # A. Price Range
        min_p = int(df['Clean_Price'].min())
        max_p = int(df['Clean_Price'].max())
        price_range = st.sidebar.slider("Price Range", min_p, max_p, (min_p, max_p))
        
        # B. Property Type
        if 'Property Type' in df.columns:
            types = df['Property Type'].unique()
            selected_types = st.sidebar.multiselect("Property Type", types, default=types)
        else:
            selected_types = []

        # C. Towns/Cities
        if 'City' in df.columns:
            cities = sorted(df['City'].unique())
            selected_cities = st.sidebar.multiselect("Select Towns", cities, default=cities)
        else:
            selected_cities = []
            
        # D. Beds/Baths
        min_beds = st.sidebar.number_input("Min Bedrooms", 0, 10, 2)
        min_baths = st.sidebar.number_input("Min Bathrooms", 0, 10, 1)

        # --- 4. FILTERING LOGIC ---
        filtered_df = df.copy()
        
        # Filter by Price
        filtered_df = filtered_df[filtered_df['Clean_Price'].between(price_range[0], price_range[1])]
        
        # Filter by Type
        if selected_types:
            filtered_df = filtered_df[filtered_df['Property Type'].isin(selected_types)]
            
        # Filter by City
        if selected_cities:
            filtered_df = filtered_df[filtered_df['City'].isin(selected_cities)]
            
        # Filter by Beds/Baths (Using MLS specific column names)
        if 'Bedrooms Total' in df.columns:
            filtered_df = filtered_df[filtered_df['Bedrooms Total'] >= min_beds]
        if 'Bathrooms Total' in df.columns:
            filtered_df = filtered_df[filtered_df['Bathrooms Total'] >= min_baths]

        # --- 5. RESULTS DISPLAY ---
        st.markdown(f"**Found {len(filtered_df)} properties matching your criteria.**")
        st.markdown("---")

        if not filtered_df.empty:
            # Note: Map is hidden because this specific MLS export doesn't have Lat/Lon columns.
            
            # LISTINGS
            st.subheader("🏡 Current Listings")
            for index, row in filtered_df.iterrows():
                # Extract Data
                addr = row.get('Address', 'Unknown Address')
                city = row.get('City', 'NH')
                price_val = row.get('Clean_Price', 0)
                price_str = f"${price_val:,.0f}"
                
                with st.expander(f"{addr}, {city} - {price_str}"):
                    c1, c2 = st.columns([1, 2])
                    
                    with c1:
                        # Use the 'Pics' column from your CSV
                        img_url = row.get('Pics', None)
                        if pd.isna(img_url) or img_url == '':
                            # Fallback image if empty
                            img_url = "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=400"
                        st.image(img_url, use_column_width=True)
                        
                    with c2:
                        st.markdown(f"### {price_str}")
                        sqft = row.get('Clean_SqFt', 'N/A')
                        beds = row.get('Bedrooms Total', '-')
                        baths = row.get('Bathrooms Total', '-')
                        prop_type = row.get('Property Type', 'Home')
                        mls_id = row.get('MLS #', '')
                        
                        st.markdown(f"**{beds}** Beds | **{baths}** Baths | **{sqft:,.0f}** SqFt")
                        st.markdown(f"**Type:** {prop_type} | **MLS#:** {mls_id}")
                        st.markdown(f"**Town:** {city}")
                        
                        # Email Button
                        contact_msg = f"I am interested in {addr}, {city} (MLS# {mls_id})."
                        st.markdown(f"""
                            <a href="mailto:your_email@brokerage.com?subject=Inquiry: {addr}&body={contact_msg}">
                                <button style="background-color:#2E86C1; color:white; padding:10px 20px; border:none; border-radius:5px; cursor:pointer;">
                                    📧 Contact Agent
                                </button>
                            </a>
                        """, unsafe_allow_html=True)
        else:
            st.error("No homes found in this range. Try adjusting the filters.")
            
    except Exception as e:
        st.error(f"Error reading file: {e}")

else:
    # --- 6. INSTRUCTIONS ---
    st.info("👋 Welcome! Please upload your 'Default_MLS_Defined_Spreadsheet.csv' on the left.")
