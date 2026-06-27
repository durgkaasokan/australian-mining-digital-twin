import sqlite3
import pandas as pd

def build_machine_learning_features():
    conn = sqlite3.connect("mining_digital_twin.db")
    print("🛰️ Extracting raw telemetry and maintenance logs...")
    df_ops = pd.read_sql_query("SELECT * FROM fact_operational_logs", conn)
    df_maint = pd.read_sql_query("SELECT * FROM fact_maintenance_events", conn)
    
    if df_ops.empty or df_maint.empty:
        print("❌ Error: Operational or Maintenance tables are empty.")
        conn.close()
        return

    print("⚙️ Processing features per asset profile...")
    df_truck_stats = df_ops.groupby('equipment_id').agg(
        total_payload_tonnes=('payload_tonnes', 'sum'),
        avg_fuel_litres=('fuel_consumed_litres', 'mean'),
        avg_cycle_time=('cycle_time_minutes', 'mean'),
        total_trips=('log_id', 'count')
    ).reset_index()
    
    df_maint_stats = df_maint.groupby('equipment_id').agg(
        total_breakdowns=('event_id', 'count'),
        total_repair_cost_aud=('repair_cost_aud', 'sum'),
        total_downtime_hours=('downtime_hours', 'sum')
    ).reset_index()
    
    df_features = pd.merge(df_truck_stats, df_maint_stats, on='equipment_id', how='left')
    df_features.fillna(0, inplace=True)
    
    median_cost = df_features['total_repair_cost_aud'].median()
    df_features['high_risk_failure'] = (df_features['total_repair_cost_aud'] > median_cost).astype(int)
    
    df_features.to_sql("ml_truck_features", conn, if_exists="replace", index=False)
    print("✅ Success: Trained features compiled into 'ml_truck_features' table!")
    conn.close()

if __name__ == "__main__":
    build_machine_learning_features()
