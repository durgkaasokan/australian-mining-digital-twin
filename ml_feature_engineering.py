import sqlite3
import pandas as pd
import sys

def run_feature_engineering():
    print("⏳ Starting automated feature engineering pipeline...")
    try:
        conn = sqlite3.connect("mining_digital_twin.db")
        
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fact_operational_logs'")
        if not cursor.fetchone():
            print("❌ Error: 'fact_operational_logs' table not found. Run 'run_simulation.py' first.")
            sys.exit(1)

        query_ops = """
        SELECT 
            equipment_id,
            SUM(payload_tonnes) as total_payload_tonnes,
            AVG(fuel_consumed_litres) as avg_fuel_litres,
            AVG(cycle_time_minutes) as avg_cycle_time,
            COUNT(*) as total_trips
        FROM fact_operational_logs
        GROUP BY equipment_id
        """
        df_ops = pd.read_sql_query(query_ops, conn)
        
        query_maint = """
        SELECT 
            equipment_id,
            COUNT(*) as total_breakdowns
        FROM fact_maintenance_events
        GROUP BY equipment_id
        """
        df_maint = pd.read_sql_query(query_maint, conn)
        
        df_features = pd.merge(df_ops, df_maint, on="equipment_id", how="left").fillna(0)
        df_features['total_breakdowns'] = df_features['total_breakdowns'].astype(int)
        df_features['high_risk_failure'] = (df_features['total_breakdowns'] >= 2).astype(int)
        
        df_features.to_sql("ml_truck_features", conn, if_exists="replace", index=False)
        print("✅ Feature Store 'ml_truck_features' successfully updated!")
        
    except sqlite3.OperationalError as e:
        print(f"❌ Database Operational Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    run_feature_engineering()
