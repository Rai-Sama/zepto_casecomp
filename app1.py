import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Zepto Strategy Dashboard",
    page_icon="⚡",
    layout="wide"
)

# Title and Intro
st.title("⚡ Zepto Case Study: Strategic Analytics Dashboard")
st.markdown("""
This dashboard analyzes operational bottlenecks (Delivery SLA) and customer segmentation opportunities.
**Key Focus:** Solving the 10-minute delivery failure and identifying the 'Silver Economy'.
""")
st.markdown("---")

# ==========================================
# 2. DATA LOADING & PROCESSING
# ==========================================
@st.cache_data
def load_data():
    filename = "Zepto_Analytics_Dataset.csv"
    try:
        df = pd.read_csv(filename)
        
        # --- Feature Engineering ---
        
        # 1. SLA Logic
        # Assumption: 10 minutes is the strict promise
        df['SLA_Breach'] = df['Delivery_Time_mins'] > 10
        df['SLA_Status'] = df['SLA_Breach'].apply(lambda x: 'Breached (>10m)' if x else 'On Time (<=10m)')
        
        # 2. Age Groups
        bins = [18, 25, 35, 45, 55, 65]
        labels = ['18-25', '26-35', '36-45', '46-55', '56-65']
        df['Age_Group'] = pd.cut(df['Age'], bins=bins, labels=labels, right=True)
        
        # 3. Date Processing
        df['Order_Time'] = pd.to_datetime(df['Order_Time'])
        df['Hour'] = df['Order_Time'].dt.hour
        df['Day_of_Week'] = df['Order_Time'].dt.day_name()

        # 4. Financial Calculations (CORRECTED)
        # Revenue must be Price * Quantity
        df['Total_Spend'] = df['Price'] * df['Quantity']

        return df
        
    except FileNotFoundError:
        st.error(f"File '{filename}' not found. Please ensure it is in the same directory.")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.stop()

# ==========================================
# 3. SIDEBAR FILTERS
# ==========================================
st.sidebar.header("🔍 Filter Dashboard")

# A. City Filter
city_options = sorted(df['City'].unique())
selected_cities = st.sidebar.multiselect("Select City:", city_options, default=city_options)

# B. Category Filter
cat_options = sorted(df['Product_Category'].unique())
selected_cats = st.sidebar.multiselect("Select Category:", cat_options, default=cat_options)

# C. Age Group Filter
age_options = sorted(df['Age_Group'].dropna().unique())
selected_ages = st.sidebar.multiselect("Select Age Group:", age_options, default=age_options)

# Apply Filters
df_filtered = df[
    (df['City'].isin(selected_cities)) & 
    (df['Product_Category'].isin(selected_cats)) &
    (df['Age_Group'].isin(selected_ages))
]

st.sidebar.markdown("---")
st.sidebar.info(f"**Data Points:** {len(df_filtered)}")
st.sidebar.caption("Use these filters to drill down into specific cities or demographics.")

# ==========================================
# 4. KPI ROW
# ==========================================
if not df_filtered.empty:
    col1, col2, col3, col4 = st.columns(4)

    # KPIs calculated using Total_Spend
    total_revenue = df_filtered['Total_Spend'].sum()
    breach_rate = df_filtered['SLA_Breach'].mean() * 100
    avg_delivery = df_filtered['Delivery_Time_mins'].mean()
    avg_basket_size = df_filtered['Quantity'].mean()

    col1.metric("💰 Total Revenue", f"₹{total_revenue:,.0f}")
    col2.metric("🚨 SLA Breach Rate", f"{breach_rate:.1f}%", delta_color="inverse")
    col3.metric("⏱️ Avg Delivery Time", f"{avg_delivery:.1f} min")
    col4.metric("📦 Avg Basket Size", f"{avg_basket_size:.1f} items")
else:
    st.warning("No data matches your filters.")
    st.stop()

st.markdown("---")

# ==========================================
# 5. MAIN TABS
# ==========================================
tab1, tab2, tab3 = st.tabs(["📦 Delivery Crisis", "👥 Customer Segments", "💔 Loyalty Analysis"])

# --- TAB 1: DELIVERY OPTIMIZATION ---
with tab1:
    st.subheader("Why are we missing the 10-minute mark?")
    
    c1, c2 = st.columns(2)
    
    with c1:
        # 1. Breach by City
        city_breach = df_filtered.groupby('City')['SLA_Breach'].mean().reset_index()
        city_breach['SLA_Breach'] = city_breach['SLA_Breach'] * 100
        
        fig_city = px.bar(
            city_breach, x='City', y='SLA_Breach',
            title="SLA Breach % by City",
            color='SLA_Breach', color_continuous_scale='Reds',
            labels={'SLA_Breach': 'Breach % (>10 mins)'}
        )
        fig_city.add_hline(y=10, line_dash="dot", annotation_text="Target Limit", annotation_position="bottom right")
        st.plotly_chart(fig_city, use_container_width=True)
        
        with st.expander("💡 Insight: Systemic Failure"):
            st.write("The breach rate is consistently high (>40%) across ALL cities. This indicates a fundamental process flaw (e.g., store radius too large) rather than isolated traffic issues.")

    with c2:
        # 2. Quantity vs Time
        fig_box = px.box(
            df_filtered, x='Quantity', y='Delivery_Time_mins',
            title="Delivery Time Distribution by Order Quantity",
            color='Quantity',
            color_discrete_sequence=px.colors.sequential.Viridis
        )
        st.plotly_chart(fig_box, use_container_width=True)
        
        with st.expander("💡 Insight: Quantity ≠ Delay"):
            st.write("There is **zero correlation** between basket size and delivery time. Riders take the same time to deliver 1 item as 5 items. **Recommendation:** Implement order batching (multiple orders per rider) to improve efficiency without increasing time per drop.")

# --- TAB 2: CUSTOMER SEGMENTS ---
with tab2:
    st.subheader("Unlocking the 'Silver Economy'")
    
    c3, c4 = st.columns(2)
    
    with c3:
        # 1. Spend by Age (Using Total_Spend)
        age_spend = df_filtered.groupby('Age_Group')['Total_Spend'].sum().reset_index()
        
        fig_age = px.bar(
            age_spend, x='Age_Group', y='Total_Spend',
            title="Total Spending by Age Group",
            color='Total_Spend', color_continuous_scale='Teal',
            labels={'Total_Spend': 'Total Revenue (INR)'}
        )
        st.plotly_chart(fig_age, use_container_width=True)
        
        with st.expander("💡 Insight: The 56-65 Surprise"):
            st.write("Contrary to popular belief, the **56-65 Age Group** is the highest spending demographic. The 18-25 (Gen Z) group spends the least. Marketing should pivot to target seniors.")

    with c4:
        # 2. Category Heatmap (Using Total_Spend)
        st.markdown("**Spending Heatmap: Category vs. Age Group**")
        # Using Seaborn for better Heatmap control
        pivot = df_filtered.pivot_table(values='Total_Spend', index='Product_Category', columns='Age_Group', aggfunc='sum')
        
        fig_heat, ax = plt.subplots(figsize=(6, 4))
        sns.heatmap(pivot, annot=True, fmt='.0f', cmap="YlGnBu", ax=ax)
        st.pyplot(fig_heat)
        
        with st.expander("💡 Insight: Product Fit"):
            st.write("This view highlights which categories drive revenue for specific age demographics. For example, observe the high concentration of spend in **Snacks** for the **56-65** group, confirming the 'Silver Snacker' theory.")

# --- TAB 3: LOYALTY & CORRELATION ---
with tab3:
    st.subheader("The Broken Reward System")
    
    c5, c6 = st.columns(2)
    
    with c5:
        # 1. Scatter Plot (Using Total_Spend)
        fig_scatter = px.scatter(
            df_filtered, x='Total_Spend', y='Loyalty_Points_Earned',
            color='Age_Group',
            title="Total Spend vs. Loyalty Points Earned",
            labels={'Total_Spend': 'Total Transaction Value (INR)'},
            opacity=0.6
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    with c6:
        # 2. Correlation Matrix (Using Total_Spend)
        st.markdown("**Correlation Matrix**")
        # Swapped 'Price' for 'Total_Spend' to check actual value correlation
        numeric_df = df_filtered[['Total_Spend', 'Quantity', 'Delivery_Time_mins', 'Loyalty_Points_Earned', 'Age']]
        corr = numeric_df.corr()
        
        fig_corr, ax = plt.subplots(figsize=(6, 5))
        sns.heatmap(corr, annot=True, cmap='coolwarm', vmin=-1, vmax=1, ax=ax)
        st.pyplot(fig_corr)
    
    st.error("⚠️ **Critical Issue:** The correlation between Total Spend and Loyalty Points is ~0.00. Customers spending ₹1000 are getting the same points as those spending ₹100. The loyalty program is essentially random.")

# Footer
st.markdown("---")
st.caption("Zepto Strategic Analysis | Generated via Gemini")