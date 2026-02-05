import streamlit as st
import pandas as pd

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="NH Real Estate Search", page_icon="🌲", layout="wide")

# Custom CSS for polished UI
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div.block-container { padding-top: 2rem; }
    .stButton>button { width: 100%; border-radius: 5px; font-weight: bold;}
    .price-tag { font-size: 1.2rem; font-weight: bold; color: #2E86C1; }
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA LOADING (The "No Upload" Magic) ---
@st.cache_data
def load_data():
    # Looks for the file directly in the repository
    file_name = 'Default_MLS_Defined_Spreadsheet.csv'
    
    try:
        df = pd.read_csv(file_name)
        
        # --- CLEANING DATA ---
        # Clean Price
        if df['Price'].dtype == 'O': 
            df['Clean_Price'] = df['Price'].astype(str).str.replace(r'[$,]', '', regex=True)
            df['Clean_Price'] = pd.to_numeric(df['Clean_Price'], errors='coerce').fillna(0)
        else:
            df['Clean_Price'] = df['Price']
            
        # Clean SqFt
        if 'SqFtTotFn' in df.columns:
            df['Clean_SqFt'] = df['SqFtTotFn'].astype(str).str.replace(',', '', regex=False)
            df['Clean_SqFt'] = pd.to_numeric(df['Clean_SqFt'], errors='coerce').fillna(0)
        else:
            df['Clean_SqFt'] = 0

        # Clean DOM (Days on Market)
        if 'DOM' in df.columns:
            df['DOM'] = pd.to_numeric(df['DOM'], errors='coerce').fillna(0)
            
        return df
        
    except FileNotFoundError:
        return None

df = load_data()

# --- 3. THE INTERFACE ---
if df is None:
    st.error("⚠️ Data file not found. Please upload 'Default_MLS_Defined_Spreadsheet.csv' to your GitHub repository.")
else:
    # --- SIDEBAR FILTERS ---
    st.sidebar.header("🌲 Filter Listings")
    
    # Quick Search
    search_term = st.sidebar.text_input("🔍 Search Address or MLS#", "")

    # City Filter
    if 'City' in df.columns:
        cities = sorted(df['City'].unique())
        selected_cities = st.sidebar.multiselect("Town / City", cities)
    else:
        selected_cities = []

    # Price Slider
    min_p, max_p = int(df['Clean_Price'].min()), int(df['Clean_Price'].max())
    price_range = st.sidebar.slider("Price Range", min_p, max_p, (min_p, max_p), step=10000)
    
    # Beds & Baths
    c1, c2 = st.sidebar.columns(2)
    min_beds = c1.number_input("Min Beds", 0, 10, 0)
    min_baths = c2.number_input("Min Baths", 0, 10, 0)

    # Advanced Filters (Collapsible)
    with st.sidebar.expander("More Filters (SqFt, DOM)"):
        # SqFt Slider
        max_sq = int(df['Clean_SqFt'].max())
        sqft_range = st.slider("Square Footage", 0, max_sq, (0, max_sq), step=100)
        
        # Days on Market Slider
        max_dom = int(df.get('DOM', pd.Series([0])).max())
        dom_range = st.slider("Days on Market", 0, max_dom, (0, max_dom))

    # --- FILTERING LOGIC ---
    mask = (
        (df['Clean_Price'].between(price_range[0], price_range[1])) &
        (df['Clean_SqFt'].between(sqft_range[0], sqft_range[1]))
    )
    
    if 'DOM' in df.columns:
        mask = mask & (df['DOM'].between(dom_range[0], dom_range[1]))
        
    if selected_cities:
        mask = mask & (df['City'].isin(selected_cities))
        
    if search_term:
        # Search inside Address or MLS#
        term = search_term.lower()
        mask = mask & (
            df['Address'].str.lower().str.contains(term, na=False) | 
            df['MLS #'].astype(str).str.contains(term, na=False)
        )
        
    if 'Bedrooms Total' in df.columns:
        mask = mask & (df['Bedrooms Total'] >= min_beds)
    if 'Bathrooms Total' in df.columns:
        mask = mask & (df['Bathrooms Total'] >= min_baths)

    filtered_df = df[mask]

    # --- MAIN DISPLAY ---
    c_top1, c_top2 = st.columns([3, 1])
    c_top1.title("NH Real Estate Search")
    
    # Sorting
    sort_option = c_top2.selectbox("Sort By", ["Price: High to Low", "Price: Low to High", "Newest (DOM)", "SqFt: High to Low"])
    
    if sort_option == "Price: Low to High":
        filtered_df = filtered_df.sort_values("Clean_Price", ascending=True)
    elif sort_option == "Price: High to Low":
        filtered_df = filtered_df.sort_values("Clean_Price", ascending=False)
    elif sort_option == "Newest (DOM)" and 'DOM' in df.columns:
        filtered_df = filtered_df.sort_values("DOM", ascending=True) # Low DOM = Newer
    elif sort_option == "SqFt: High to Low":
        filtered_df = filtered_df.sort_values("Clean_SqFt", ascending=False)

    st.markdown(f"**Showing {len(filtered_df)} Listings**")
    st.divider()

    if filtered_df.empty:
        st.info("No listings found matching your criteria.")
    else:
        # Loop through listings
        for index, row in filtered_df.iterrows():
            # Data prep
            addr = row.get('Address', 'Unknown Address')
            city = row.get('City', 'NH')
            price_str = f"${row.get('Clean_Price', 0):,.0f}"
            img_url = row.get('Pics', "https://via.placeholder.com/800x600?text=No+Image")
            mls_id = row.get('MLS #', '')
            dom = row.get('DOM', 0)
            
            # Layout: Image on Left, Details on Right
            c1, c2 = st.columns([1, 2])
            
            with c1:
                st.image(img_url, use_column_width=True)
                
            with c2:
                st.markdown(f"### {price_str}")
                st.markdown(f"**{addr}, {city}**")
                
                # Stats Row
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Beds", row.get('Bedrooms Total', '-'))
                col_b.metric("Baths", row.get('Bathrooms Total', '-'))
                col_c.metric("SqFt", f"{row.get('Clean_SqFt', 0):,.0f}")
                
                # Details
                st.text(f"Type: {row.get('Property Type', 'N/A')}  |  DOM: {dom} days")
                
                # Action Button
                email_subject = f"Inquiry: {addr} (MLS {mls_id})"
                email_body = f"Hi, I am interested in viewing {addr} in {city}."
                mailto_link = f"mailto:your_email@brokerage.com?subject={email_subject}&body={email_body}"
                
                st.markdown(f"""
                    <a href="{mailto_link}" style="text-decoration:none;">
                        <div style="background-color:#2E86C1; color:white; padding:10px; text-align:center; border-radius:5px; margin-top:10px;">
                            ✉️ Request Info
                        </div>
                    </a>
                """, unsafe_allow_html=True)
            
            st.divider()
