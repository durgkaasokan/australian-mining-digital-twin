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
    try:
        # Extra safeguard: parse table name from simple SELECT queries to verify it exists
        table_match = re.search(r"FROM\s+(\w+)", query, re.IGNORECASE)
        if table_match:
            table_name = table_match.group(1)
            cursor = conn.cursor()
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if not cursor.fetchone():
                return pd.DataFrame() # Return empty DataFrame gracefully if table doesn't exist yet
        
        df = pd.read_sql_query(query, conn)
    except Exception:
        df = pd.DataFrame()
    finally:
        conn.close()
    return df

# ==========================================
# 2. ADVANCED CONTROL ROOM SIDEBAR
# ==========================================
st.sidebar.header("🕹️ Global Control Parameters")

weather_filter = st.sidebar.multiselect(
    "Operational Weather Window:",
    options=["Clear", "Light Rain", "Heavy Rain"],
    default=["Clear", "Light Rain", "Heavy Rain"]
)

st.sidebar.markdown("---")
st.sidebar.header("🎯 Target Benchmarks")

tononnage_target = st.sidebar.slider(
    "Monthly Throughput Target (K Tonnes)", 
    min_value=100.0, 
    max_value=1500.0, 
    value=750.0, 
    step=10.0
)
fuel_budget = st.sidebar.slider(
    "Max Fuel Allocation (K Litres)", 
    min_value=50.0, 
    max_value=500.0, 
    value=120.0, 
    step=5.0
)

st.sidebar.markdown("---")
st.sidebar.header("🚛 Fleet Management")
available_trucks = ["HT-001", "HT-002", "HT-003", "HT-004"]
selected_trucks = [truck for truck in available_trucks if st.sidebar.checkbox(truck, value=True)]

weather_list_clean = [w.strip().lower() for w in weather_filter] if weather_filter else ["none"]
truck_list_clean = [t.strip() for t in selected_trucks] if selected_trucks else ["NONE"]

# ==========================================
# 3. DYNAMIC DATA QUERIES & COMPUTATION
# ==========================================
df_all_logs = get_data("SELECT *, DATE(timestamp) as production_date FROM fact_operational_logs")

if not df_all_logs.empty:
    df_all_logs['weather_clean'] = df_all_logs['weather_condition'].astype(str).str.strip().str.lower()
    df_logs = df_all_logs[
        (df_all_logs['weather_clean'].isin(weather_list_clean)) & 
        (df_all_logs['equipment_id'].isin(truck_list_clean))
    ]
    if not df_logs.empty:
        df_weather = df_logs.groupby(['activity', 'weather_condition'])['cycle_time_minutes'].mean().reset_index()
        df_weather.rename(columns={'cycle_time_minutes': 'avg_cycle_time_minutes'}, inplace=True)
    else:
        df_weather = pd.DataFrame()
else:
    df_logs = pd.DataFrame()
    df_weather = pd.DataFrame()

truck_clause = ','.join(f"'{t}'" for t in truck_list_clean)
df_maint = get_data(f"SELECT * FROM fact_maintenance_events WHERE equipment_id IN ({truck_clause})")

# Try to pull predictive ML scores, handle missing grace period gracefully
try:
    df_preds = get_data(f"SELECT * FROM ml_predictions WHERE equipment_id IN ({truck_clause})")
except Exception:
    df_preds = pd.DataFrame()

# ==========================================
# 4. EXECUTIVE KPI CARDS W/ TARGET MATCHING
# ==========================================
total_tons = df_logs['payload_tonnes'].sum() if not df_logs.empty else 0
total_fuel = df_logs['fuel_consumed_litres'].sum() if not df_logs.empty else 0
total_downtime = df_maint['downtime_hours'].sum() if not df_maint.empty else 0
total_maint_cost = df_maint['repair_cost_aud'].sum() if not df_maint.empty else 0

tons_k = total_tons / 1000
fuel_k = total_fuel / 1000

tonnage_delta = f"{(tons_k - tononnage_target):+.1f}K vs Target"
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
tab1, tab2, tab3, tab4 = st.tabs(["📊 Fleet Production & Yield", "🔧 Reliability & Risk Matrix", "💸 Commercial Analysis", "🔮 Machine Learning Health Outlook"])

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
            fig_fleet.update_layout(margin=dict(l=40, r=40, t=40, b=60))
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
            fig_weather.update_layout(margin=dict(l=40, r=40, t=40, b=60))
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
            fig_scatter.update_layout(margin=dict(l=40, r=40, t=40, b=80))
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
            fig_pie.update_layout(margin=dict(l=40, r=40, t=40, b=60))
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
            fig_efficiency.update_layout(margin=dict(l=40, r=40, t=40, b=60))
            st.plotly_chart(fig_efficiency, use_container_width=True)
            
    with col_t3_2:
        lost_production_revenue = total_downtime * 3500 
        st.markdown("### Revenue Leakage Audit")
        st.error(f"⚠️ Estimated Opportunity Cost Variance: -${lost_production_revenue:,.2f} AUD")
        st.caption("Calculated assuming a localized market value index of $3,500.00 AUD total production throughput capability loss per system machine downtime hour.")

with tab4:
    st.markdown("#### 🔮 Predictive Fleet Diagnostics & Machine Learning Risk Allocation")
    if not df_preds.empty:
        col_m1, col_m2 = st.columns([1, 1])
        
        with col_m1:
            st.markdown("##### Current Fleet Risk Profiles")
            fig_pred_bar = px.bar(
                df_preds, x="equipment_id", y="failure_risk_percentage",
                color="failure_risk_percentage", color_continuous_scale="Reds",
                title="Random Forest Asset Failure Probabilities",
                labels={'failure_risk_percentage': 'Risk Rating (%)', 'equipment_id': 'Asset ID'}
            )
            fig_pred_bar.update_layout(yaxis_range=[0, 100], margin=dict(l=30, r=30, t=30, b=40))
            st.plotly_chart(fig_pred_bar, use_container_width=True)
            
        with col_m2:
            st.markdown("##### Model Attribution: Explainable AI (XAI)")
            try:
                df_imp = get_data("SELECT * FROM ml_feature_importance ORDER BY importance_score ASC")
                fig_imp = px.bar(
                    df_imp, x="importance_score", y="feature_name", orientation="h",
                    title="What Metrics Drive the Failure Predictions?",
                    labels={'importance_score': 'Relative Predictive Weight', 'feature_name': 'Telemetry Metric'},
                    color_discrete_sequence=["#2b5c8f"]
                )
                fig_imp.update_layout(margin=dict(l=30, r=30, t=30, b=40))
                st.plotly_chart(fig_imp, use_container_width=True)
            except Exception:
                st.info("Feature importance metrics loading...")
    else:
        st.warning("No live predictions found. Ensure you run your machine learning pipeline file first.")

# ==========================================
# 6. DATA WAREHOUSE TRANSPARENCY EXPANDER
# ==========================================
st.markdown("---")
with st.expander("🔍 System Audit Trail: Core Data Warehouse Ledger"):
    if not df_logs.empty:
        st.dataframe(df_logs.sort_values(by="timestamp", ascending=False).head(200), use_container_width=True)
