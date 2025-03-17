from matplotlib import pyplot as plt
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import us 


# Set page config for wide layout
st.set_page_config(page_title="SuperStore KPI Dashboard", layout="wide")

# ---- Load Data ----
@st.cache_data
def load_data():
    # Adjust the path if needed, e.g. "data/Sample - Superstore.xlsx"
    df = pd.read_excel("Sample - Superstore.xlsx", engine="openpyxl")
    # Convert Order Date to datetime if not already
    if not pd.api.types.is_datetime64_any_dtype(df["Order Date"]):
        df["Order Date"] = pd.to_datetime(df["Order Date"])
    return df

df_original = load_data()

# ---- Sidebar Filters ----
st.sidebar.title("Filters")

# Region Filter
all_regions = sorted(df_original["Region"].dropna().unique())
selected_region = st.sidebar.selectbox("Select Region", options=["All"] + all_regions)

# Filter data by Region
if selected_region != "All":
    df_filtered_region = df_original[df_original["Region"] == selected_region]
else:
    df_filtered_region = df_original

# State Filter
all_states = sorted(df_filtered_region["State"].dropna().unique())
selected_state = st.sidebar.selectbox("Select State", options=["All"] + all_states)

# Filter data by State
if selected_state != "All":
    df_filtered_state = df_filtered_region[df_filtered_region["State"] == selected_state]
else:
    df_filtered_state = df_filtered_region

# Category Filter
all_categories = sorted(df_filtered_state["Category"].dropna().unique())
selected_category = st.sidebar.selectbox("Select Category", options=["All"] + all_categories)

# Filter data by Category
if selected_category != "All":
    df_filtered_category = df_filtered_state[df_filtered_state["Category"] == selected_category]
else:
    df_filtered_category = df_filtered_state

# Sub-Category Filter
all_subcats = sorted(df_filtered_category["Sub-Category"].dropna().unique())
selected_subcat = st.sidebar.selectbox("Select Sub-Category", options=["All"] + all_subcats)

# Final filter by Sub-Category
df = df_filtered_category.copy()
if selected_subcat != "All":
    df = df[df["Sub-Category"] == selected_subcat]

# Enhancement: Filter Addition for Consumer Trends
all_segments = sorted(df["Segment"].dropna().unique())
selected_segment = st.sidebar.selectbox("Select Segment", options=["All"] + all_segments)

# Final filter by Sub-Category
df = df.copy()
if selected_segment != "All":
    df = df[df["Segment"] == selected_segment]

# ---- Sidebar Date Range (From and To) ----
if df.empty:
    # If there's no data after filters, default to overall min/max
    min_date = df_original["Order Date"].min()
    max_date = df_original["Order Date"].max()
else:
    min_date = df["Order Date"].min()
    max_date = df["Order Date"].max()

from_date = st.sidebar.date_input(
    "From Date", value=min_date, min_value=min_date, max_value=max_date
)
to_date = st.sidebar.date_input(
    "To Date", value=max_date, min_value=min_date, max_value=max_date
)

# Ensure from_date <= to_date
if from_date > to_date:
    st.sidebar.error("From Date must be earlier than To Date.")

# Apply date range filter
df = df[
    (df["Order Date"] >= pd.to_datetime(from_date))
    & (df["Order Date"] <= pd.to_datetime(to_date))
]


# ---- Page Title ----
st.title("SuperStore KPI Dashboard")

# ---- Custom CSS for KPI Tiles ----
st.markdown(
    """
    <style>
    .kpi-box {
        background-color: #FFFFFF;
        border: 2px solid #EAEAEA;
        border-radius: 8px;
        padding: 16px;
        margin: 8px;
        text-align: center;
    }
    .kpi-title {
        font-weight: 600;
        color: #333333;
        font-size: 16px;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-weight: 700;
        font-size: 24px;
        color: #1E90FF;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---- KPI Calculation ----
if df.empty:
    total_sales = 0
    total_quantity = 0
    total_profit = 0
    margin_rate = 0
else:
    total_sales = df["Sales"].sum()
    total_quantity = df["Quantity"].sum()
    total_profit = df["Profit"].sum()
    margin_rate = (total_profit / total_sales) if total_sales != 0 else 0

# ---- KPI Display (Rectangles) ----
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
with kpi_col1:
    st.markdown(
        f"""
        <div class='kpi-box'>
            <div class='kpi-title'>Sales</div>
            <div class='kpi-value'>${total_sales:,.2f}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
with kpi_col2:
    st.markdown(
        f"""
        <div class='kpi-box'>
            <div class='kpi-title'>Quantity Sold</div>
            <div class='kpi-value'>{total_quantity:,.0f}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
with kpi_col3:
    st.markdown(
        f"""
        <div class='kpi-box'>
            <div class='kpi-title'>Profit</div>
            <div class='kpi-value'>${total_profit:,.2f}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
with kpi_col4:
    st.markdown(
        f"""
        <div class='kpi-box'>
            <div class='kpi-title'>Margin Rate</div>
            <div class='kpi-value'>{(margin_rate * 100):,.2f}%</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ---- KPI Selection (Affects Both Charts) ----
st.subheader("Visualize KPI Across Time & Top Products")

if df.empty:
    st.warning("No data available for the selected filters and date range.")
else:
    # Radio button above both charts
    kpi_options = ["Sales", "Quantity", "Profit", "Margin Rate"]
    selected_kpi = st.radio("Select KPI to display:", options=kpi_options, horizontal=True)

    # ---- Prepare Data for Charts ----
    # Daily grouping for line chart
    daily_grouped = df.groupby("Order Date").agg({
        "Sales": "sum",
        "Quantity": "sum",
        "Profit": "sum"
    }).reset_index()
    # Avoid division by zero
    daily_grouped["Margin Rate"] = daily_grouped["Profit"] / daily_grouped["Sales"].replace(0, 1)

    # Product grouping for top 10 chart
    product_grouped = df.groupby("Product Name").agg({
        "Sales": "sum",
        "Quantity": "sum",
        "Profit": "sum"
    }).reset_index()
    product_grouped["Margin Rate"] = product_grouped["Profit"] / product_grouped["Sales"].replace(0, 1)

    # Sort for top 10 by selected KPI
    product_grouped.sort_values(by=selected_kpi, ascending=False, inplace=True)
    top_10 = product_grouped.head(10)

    # Group by 'Year' and 'Segment' for aggregation
    df['Year'] = df['Order Date'].dt.year
    year_segment_grouped = df.groupby(["Year", "Segment"]).agg({
        "Sales": "sum",
        "Profit": "sum",
        "Quantity": "sum"
    }).reset_index()
    year_segment_grouped['Margin Rate']=year_segment_grouped['Profit'] / year_segment_grouped["Sales"].replace(0, 1)

    # Enhancement-1: Group by State for KPI mapping
    # Convert full state names to abbreviations
    df["State"] = df["State"].apply(lambda x: us.states.lookup(x).abbr if us.states.lookup(x) else x)
    #print(df["State"].unique()) 
    state_grouped = df.groupby("State").agg({
        "Sales": "sum",
        "Quantity": "sum",
        "Profit": "sum",
    }).reset_index()
    state_grouped["Margin Rate"] = state_grouped["Profit"] / state_grouped["Sales"].replace(0, 1)
    #print(state_grouped)

    # Enhancement-2: Convert Order Date to datetime and extract quarterly period as a string
    # Convert Order Date to datetime and extract quarterly period as a string
    df['Order Date'] = pd.to_datetime(df['Order Date'])
    df['Quarter'] = df['Order Date'].dt.to_period('Q').astype(str)  # Convert Period to string

    # Group by Quarter and calculate total Sales, Profit
    quarterly_grouped = df.groupby("Quarter").agg({
        "Sales": "sum",
        "Profit": "sum",
        "Quantity": "sum",
    }).reset_index()

    # Calculate Margin Rate safely
    quarterly_grouped["Margin Rate"] = quarterly_grouped["Profit"] / quarterly_grouped["Sales"].replace(0, 1)
    print(quarterly_grouped)

    # Enhancement-3: category-wise sale trend
    # Group by Quarter and Category to calculate Sales, Profit, and Margin Rate
    quarterly_data = df.groupby(['Quarter', 'Category']).agg({
        "Sales": "sum",
        "Quantity": "sum",
        "Profit": "sum"
    }).reset_index()

    # Compute Margin Rate
    quarterly_data["Margin Rate"] = quarterly_data["Profit"] / quarterly_data["Sales"].replace(0, 1)

    # Pivot table for visualization
    pivot_data = quarterly_data.pivot(index='Quarter', columns='Category', values=selected_kpi).fillna(0)
    col_left, col_right = st.columns(2)

    with col_left:
        fig_map = px.choropleth(
                    state_grouped,
                        locations="State",
                        locationmode="USA-states",
                        color=selected_kpi,
                        hover_name="State",
                        #title=f"State-wise {selected_kpi} Distribution",
                        color_continuous_scale="Blues",
                        template="plotly_white"
                        )
        fig_map.update_geos(scope="usa", showlakes=True, lakecolor="rgb(255, 255, 255)")
        st.subheader(f"State-wise {selected_kpi} Distribution")
        st.plotly_chart(fig_map, use_container_width=True)

    with col_right:
        df["Margin Rate"]= df["Profit"]/df["Sales"].replace(0, 1)
        # Create Stacked Bar Chart
        fig = px.bar(
            df,
            x="Year",
            y=selected_kpi,
            color="Segment",
            labels={selected_kpi: selected_kpi, "Year": "Order Date"},
            barmode="stack",
        )
        st.subheader(" Who are our Consumers? ")
        # Display Chart in Streamlit
        st.plotly_chart(fig)

    col_left, col_right = st.columns(2)
    with col_left:
        # Line Chart
        fig_line = px.line(
            daily_grouped,
            x="Order Date",
            y=selected_kpi,
            title=f"{selected_kpi} Over Time",
            labels={"Order Date": "Date", selected_kpi: selected_kpi},
            template="plotly_white",
        )
        fig_line.update_layout(height=400)
        st.plotly_chart(fig_line, use_container_width=True)
    
    # ---- Plot in Right Column ----
    with col_right:
        fig1, ax1 = plt.subplots(figsize=(12, 6))

        # Aggregate KPI per quarter (sum across all categories)
        quarterly_total = quarterly_grouped.groupby("Quarter")[selected_kpi].sum().reset_index()

        # Plot total quarterly KPI trend
        ax1.plot(quarterly_total["Quarter"], quarterly_total[selected_kpi], marker='o', linestyle='-', color='b', label="Total KPI")

        # Formatting
        ax1.set_xlabel("Quarter")
        ax1.set_ylabel(f"Total {selected_kpi}")
        ax1.set_title(f"{selected_kpi} Over Time :Quarterly Trend")
        ax1.legend()
        plt.xticks(rotation=45)
        plt.grid()
        st.subheader(f"{selected_kpi} Over Time :Quarterly Trend")
        # Show plot in Streamlit
        st.pyplot(fig1)

    # ---- Side-by-Side Layout for Charts ----
    col_left, col_right = st.columns(2)
    # Create a Choropleth Map for State-wise KPI Distribution
    with col_left:
        # Plot
        fig, ax = plt.subplots(figsize=(12, 6))

        for category in pivot_data.columns:
            ax.plot(pivot_data.index, pivot_data[category], marker='o', label=category)

        # Formatting
        ax.set_xlabel("Quarter")
        ax.set_ylabel(f"Total {selected_kpi}")
        ax.set_title(f"Category {selected_kpi} Over Time")
        ax.legend(title="Category")
        plt.xticks(rotation=45)
        plt.grid()
        # Show plot in Streamlit
        st.subheader(f"Category {selected_kpi} Over Time")
        st.pyplot(fig) 
    
    with col_right:
        # Horizontal Bar Chart
        fig_bar = px.bar(
            top_10,
            x=selected_kpi,
            y="Product Name",
            orientation="h",
            title=f"Top 10 Products by {selected_kpi}",
            labels={selected_kpi: selected_kpi, "Product Name": "Product"},
            color=selected_kpi,
            color_continuous_scale="Blues",
            template="plotly_white",
        )
        fig_bar.update_layout(
            height=400,
            yaxis={"categoryorder": "total ascending"}
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    

    # Group by Category and Quarter-Year, then aggregate
    df_grouped_new = df.groupby(["Category", "Quarter"]).agg(
        {"Sales": "sum", 
         "Profit": "sum",
         "Quantity":"sum",
         "Margin Rate":"sum"}
    ).reset_index()


    if selected_kpi!="Profit":
        # Streamlit UI
        st.subheader(f"Profitable Category Year-over-Year (YoY) {selected_kpi} (Bar) & Profit(Line) Analysis ")
        # Create Faceted Bar and Line Chart
        fig = px.bar(df_grouped_new, 
                    x="Quarter", 
                    y=selected_kpi, 
                    facet_row="Category",  # Creates separate rows per category
                    color_discrete_sequence=["orange"]
                    )

        # Add Sales Line Chart per Category
        for cat in df_grouped_new["Category"].unique():
            subset = df_grouped_new[df_grouped_new["Category"] == cat]
            fig.add_scatter(x=subset["Quarter"], 
                            y=subset["Profit"], 
                            mode="lines+markers", 
                            name=f"Profit - {cat}", 
                            line=dict(color="blue"), 
                            row=list(df_grouped_new["Category"].unique()).index(cat) + 1, 
                            col=1)

        # Adjust Layout for Better Readability
        fig.update_layout(height=600)

        # Display Chart
        st.plotly_chart(fig)
