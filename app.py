import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# 1. Page Configuration & Theme
st.set_page_config(page_title="Mining Twin Control Tower", layout="wide")

st.markdown("""
    <style>
    h1, h2, h3 { font-weight: 700 !important; }
    </style>
""", unsafe_allow_html=True)

st.title("🇦🇺 Western Australia Iron Ore Operations Management Suite")
st.markdown("### `SYSTEM STATUS: ACTIVE` | Enterprise Telemetry & Digital Twin Analytics")
st.markdown("---")

# Connect to database helper
def get_data(query):
    conn = sqlite3.connect("mining_digital_twin.db")
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# ==========================================
# 2. ADVANCED CONTROL ROOM SIDEBAR
# ==========================================
st.sidebar.header("🕹️ Global Control Parameters")

# Filter 1: Weather Condition Multi-Select
weather_filter = st.sidebar.multiselect(
    "Operational Weather Window:",
    options=["Clear", "Light Rain", "Heavy Rain"],
    default=["Clear", "Light Rain", "Heavy Rain"]
)

st.sidebar.markdown("---")
st.sidebar.header("🎯 Target Benchmarks")
tononnage_target = st.sidebar.slider("Monthly Throughput Target (K Tonnes)", 10.0, 45.0, 30.0)
fuel_budget = st.sidebar.slider("Max Fuel Allocation (K Litres)", 50.0, 150.0, 100.0)

# Filter 3: Asset Filter Checkboxes
st.sidebar.markdown("---")
st.sidebar.header("🚛 Fleet Management")
available_trucks = ["HT-001", "HT-002", "HT-003", "HT-004"]
selected_trucks = [truck for truck in available_trucks if st.sidebar.checkbox(truck, value=True)]

# SQL Clause Handling safely (with clean trimming)
weather_list = [w.strip() for w in weather_filter] if weather_filter else ["NONE"]
truck_list = selected_trucks if selected_trucks else ["NONE"]

# ==========================================
# 3. DYNAMIC DATA QUERIES (FULLY FILTERED)
# ==========================================
# Read raw logs table completely to do Python side resilient filtering
df_all_logs = get_data("SELECT *, DATE(timestamp) as production_date FROM fact_operational_logs")

# Apply defensive filters directly using Pandas to avoid SQL string mismatch bugs
if not df_all_logs.empty:
    df_logs = df_all_logs[
        (df_all_logs['weather_condition'].str.strip().isin(weather_list)) & 
        (df_all_logs['equipment_id'].isin(truck_list))
    ]
else:
    df_logs = pd.DataFrame()

# Maintenance events filtered by trucks
truck_clause = ','.join(f"'{t}'" for t in truck_list)
df_maint = get_data(f"SELECT * FROM fact_maintenance_events WHERE equipment_id IN ({truck_clause})")

# Weather Matrix 
df_weather = get_data("SELECT * FROM view_weather_impact_matrix")

# ==========================================
# 4. EXECUTIVE KPI CARDS W/ TARGET MATCHING
# ==========================================
total_tons = df_logs['payload_tonnes'].sum() if not df_logs.empty else 0
total_fuel = df_logs['fuel_consumed_litres'].sum() if not df_logs.empty else 0
total_downtime = df_maint['downtime_hours'].sum() if not df_maint.empty else 0
total_maint_cost = df_maint['repair_cost_aud'].sum() if not df_maint.empty else 0

tons_k = total_tons / 1000
fuel_k = total_fuel / 1000

tonnage_delta = f"{(tons_k - tononnage_target):.1f}K vs Target"
fuel_delta = f"{(fuel_budget - fuel_k):.1f}K Under Budget" if fuel_k <= fuel_budget else f"{(fuel_k - fuel_budget):.1f}K OVER BUDGET"

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.metric("Total Yield Throughput", f"{tons_k:.1f}K Tonnes", delta=tonnage_delta, delta_color="normal" if tons_k >= tononnage_target else "inverse")
with kpi2:
    st.metric("Consolidated Fuel Burn", f"{fuel_k:.1f}K Litres", delta=fuel_delta, delta_color="normal" if fuel_k <= fuel_budget else "inverse")
with kpi3:
    st.metric("Asset Mechanical Downtime", f"{total_downtime:,.1f} Hrs", delta="Unscheduled Loss", delta_color="off")
with kpi4:
    st.metric("Total OPEX Maintenance Spend", f"${total_maint_cost:,.2f} AUD", delta="Direct Repair Cost", delta_color="off")

st.markdown("---")

# ==========================================
# 5. HIGH-DENSITY ANALYTICS INTERFACES
# ==========================================
tab1, tab2, tab3 = st.tabs(["📊 Fleet Production & Yield", "🔧 Reliability & Risk Matrix", "💸 Commercial Analysis"])

with tab1:
    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.markdown("#### Production Timeline by Asset Profile")
        if not df_logs.empty:
            df_fleet_dynamic = df_logs.groupby(['production_date', 'equipment_id'])['payload_tonnes'].sum().reset_index()
            
            fig_fleet = px.bar(
                df_fleet_dynamic, x="production_date", y="payload_tonnes", color="equipment_id",
                title="Dynamic Production Schedule (Tonnes)", barmode="stack",
                color_discrete_sequence=px.colors.sequential.YlOrBr_r
            )
            st.plotly_chart(fig_fleet, use_container_width=True)
        else:
            st.warning("No data matches current tracking criteria.")
            
    with col_right:
        st.markdown("#### Climate Disruption Impact")
        if not df_weather.empty:
            fig_weather = px.bar(
                df_weather, x="activity", y="avg_cycle_time_minutes", color="weather_condition",
                barmode="group", title="Avg Operational Cycle Speeds (Minutes)"
            )
            st.plotly_chart(fig_weather, use_container_width=True)

with tab2:
    col_t2_left, col_t2_right = st.columns(2)
    with col_t2_left:
        st.markdown("#### Stress Profiling: Downtime vs Engineering Costs")
        if not df_maint.empty:
            fig_scatter = px.scatter(
                df_maint, x="downtime_hours", y="repair_cost_aud",
                color="component_affected", hover_name="equipment_id",
                title="Asset Integrity Mapping Structure"
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("Select fleet equipment to populate reliability tracking maps.")
            
    with col_t2_right:
        st.markdown("#### Critical System Component Failures")
        if not df_maint.empty:
            fig_pie = px.pie(
                df_maint, values="repair_cost_aud", names="component_affected",
                hole=0.4, title="Total Operational Maintenance Outlay Breakdown"
            )
            st.plotly_chart(fig_pie, use_container_width=True)

with tab3:
    st.markdown("#### Operational Efficiency & Financial Variance Mapping")
    col_t3_1, col_t3_2 = st.columns(2)
    
    with col_t3_1:
        if not df_logs.empty:
            fig_efficiency = px.scatter(
                df_logs[df_logs['activity'].isin(['Hauling', 'Empty Return'])],
                x="cycle_time_minutes", y="fuel_consumed_litres", color="activity",
                trendline="ols", title="Payload Transportation Variable Inefficiencies"
            )
            st.plotly_chart(fig_efficiency, use_container_width=True)
            
    with col_t3_2:
        lost_production_revenue = total_downtime * 3500 
        st.markdown("### Revenue Leakage Audit")
        st.error(f"⚠️ Estimated Opportunity Cost Variance: -${lost_production_revenue:,.2f} AUD")
        st.caption("Calculated assuming a localized market value index of $3,500.00 AUD total production throughput capability loss per system machine downtime hour.")

# ==========================================
# 6. DATA WAREHOUSE TRANSPARENCY EXPANDER
# ==========================================
st.markdown("---")
with st.expander("🔍 System Audit Trail: Core Data Warehouse Ledger"):
    if not df_logs.empty:
        st.dataframe(df_logs.sort_values(by="timestamp", ascending=False).head(200), use_container_width=True)
