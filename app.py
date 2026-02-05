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
st.markdown("### Upload your market data to begin")

# --- 2. FILE UPLOADER ---
uploaded_file = st.sidebar.file_uploader("Upload NH Listings CSV", type=['csv'])

if uploaded_file is not None:
    # Load the data
    try:
        df = pd.read_csv(uploaded_file)
        
        # --- 3. DYNAMIC SIDEBAR FILTERS ---
        st.sidebar.header("🔍 Filter Properties")
        
        # A. Price Range (Auto-detects min/max from your CSV)
        min_p = int(df['Price'].min())
        max_p = int(df['Price'].max())
        price_range = st.sidebar.slider("Price Range", min_p, max_p, (min_p, max_p))
        
        # B. Property Type (Auto-detects types like 'Single Family', 'Land', etc.)
        # If 'Type' column exists, use it. Otherwise ignore.
        if 'Type' in df.columns:
            types = df['Type'].unique()
            selected_types = st.sidebar.multiselect("Property Type", types, default=types)
        else:
            selected_types = []

        # C. Towns/Cities (Auto-detects from 'City' column)
        if 'City' in df.columns:
            cities = sorted(df['City'].unique())
            selected_cities = st.sidebar.multiselect("Select Towns", cities, default=cities)
        else:
            selected_cities = []
            
        # D. Beds/Baths
        min_beds = st.sidebar.number_input("Min Bedrooms", 0, 10, 2)
        min_baths = st.sidebar.number_input("Min Bathrooms", 0, 10, 1)

        # --- 4. FILTERING LOGIC ---
        # Start with full dataframe
        filtered_df = df.copy()
        
        # Apply Price Filter
        filtered_df = filtered_df[filtered_df['Price'].between(price_range[0], price_range[1])]
        
        # Apply Type Filter
        if selected_types:
            filtered_df = filtered_df[filtered_df['Type'].isin(selected_types)]
            
        # Apply City Filter
        if selected_cities:
            filtered_df = filtered_df[filtered_df['City'].isin(selected_cities)]
            
        # Apply Bed/Bath Filter (Ensure columns exist first)
        if 'Bedrooms' in df.columns:
            filtered_df = filtered_df[filtered_df['Bedrooms'] >= min_beds]
        if 'Bathrooms' in df.columns:
            filtered_df = filtered_df[filtered_df['Bathrooms'] >= min_baths]

        # --- 5. RESULTS DISPLAY ---
        st.markdown(f"**Found {len(filtered_df)} properties matching your criteria.**")
        st.markdown("---")

        if not filtered_df.empty:
            # MAP (Requires 'latitude' and 'longitude' columns in CSV)
            if 'latitude' in filtered_df.columns and 'longitude' in filtered_df.columns:
                st.subheader("📍 Interactive Map")
                # Streamlit looks for columns named 'lat'/'lon' or 'latitude'/'longitude'
                st.map(filtered_df, latitude='latitude', longitude='longitude')
            else:
                st.warning("⚠️ Map hidden. Your CSV needs 'latitude' and 'longitude' columns.")

            # LISTINGS
            st.subheader("🏡 Current Listings")
            for index, row in filtered_df.iterrows():
                # Create a clean address string
                addr = row.get('Address', 'Unknown Address')
                city = row.get('City', 'NH')
                price = row.get('Price', 0)
                
                with st.expander(f"{addr}, {city} - ${price:,.0f}"):
                    c1, c2 = st.columns([1, 2])
                    
                    with c1:
                        # Checks for an image column, uses a placeholder if missing
                        img_url = row.get('Image_URL', "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=400")
                        st.image(img_url, use_column_width=True)
                        
                    with c2:
                        st.markdown(f"### ${price:,.0f}")
                        sqft = row.get('SqFt', 'N/A')
                        beds = row.get('Bedrooms', '-')
                        baths = row.get('Bathrooms', '-')
                        
                        st.markdown(f"**{beds}** Beds | **{baths}** Baths | **{sqft}** SqFt")
                        st.markdown(f"**Town:** {city}")
                        desc = row.get('Description', 'Contact agent for details.')
                        st.info(desc)
                        
                        # Email Button
                        contact_msg = f"I am interested in {addr}, {city} listed at ${price}."
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
    # --- 6. INSTRUCTIONS (Shown when no file is uploaded) ---
    st.info("👋 Welcome! Please upload your Property CSV file on the left.")
    st.markdown("""
    **Format your CSV with these exact column headers:**
    * `Address` (e.g., 123 Main St)
    * `City` (e.g., Manchester)
    * `Price` (Numbers only, e.g., 450000)
    * `Type` (e.g., Single Family, Condo)
    * `Bedrooms` (Number)
    * `Bathrooms` (Number)
    * `SqFt` (Number)
    * `latitude` (Decimal, e.g., 43.1939)
    * `longitude` (Decimal, e.g., -71.5724)
    * `Image_URL` (Optional link to photo)
    """)
