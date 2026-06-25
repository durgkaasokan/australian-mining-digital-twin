import sqlite3
import random
from datetime import datetime, timedelta

# =====================================================================
# 1. DATABASE INITIALIZATION & SCHEMA CREATION
# =====================================================================
def init_database(db_name="mining_digital_twin.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS fact_maintenance_events;")
    cursor.execute("DROP TABLE IF EXISTS fact_operational_logs;")
    cursor.execute("DROP TABLE IF EXISTS dim_locations;")
    cursor.execute("DROP TABLE IF EXISTS dim_equipment;")
    
    cursor.execute("""
    CREATE TABLE dim_equipment (
        equipment_id VARCHAR(50) PRIMARY KEY,
        equipment_type VARCHAR(50), 
        model VARCHAR(50),          
        capacity_tonnes INT,
        commission_year INT
    );
    """)
    
    cursor.execute("""
    CREATE TABLE dim_locations (
        location_id VARCHAR(50) PRIMARY KEY,
        location_name VARCHAR(100),
        location_type VARCHAR(50),  
        distance_from_pit_km DECIMAL(5,2)
    );
    """)
    
    cursor.execute("""
    CREATE TABLE fact_operational_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME,
        equipment_id VARCHAR(50),
        location_id VARCHAR(50),
        activity VARCHAR(50),       
        cycle_time_minutes DECIMAL(5,2),
        payload_tonnes DECIMAL(5,2),
        fuel_consumed_litres DECIMAL(5,2),
        weather_condition VARCHAR(20),
        FOREIGN KEY (equipment_id) REFERENCES dim_equipment(equipment_id),
        FOREIGN KEY (location_id) REFERENCES dim_locations(location_id)
    );
    """)
    
    cursor.execute("""
    CREATE TABLE fact_maintenance_events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME,
        equipment_id VARCHAR(50),
        event_type VARCHAR(50),     
        component_affected VARCHAR(50), 
        downtime_hours DECIMAL(5,2),
        repair_cost_aud DECIMAL(10,2),
        FOREIGN KEY (equipment_id) REFERENCES dim_equipment(equipment_id)
    );
    """)
    
    conn.commit()
    return conn

# =====================================================================
# 2. SEEDING STATIC DIMENSION DATA
# =====================================================================
def seed_static_dimensions(conn):
    cursor = conn.cursor()
    equipment = [
        ('HT-001', 'Haul Truck', 'Cat 797F', 363, 2018),
        ('HT-002', 'Haul Truck', 'Cat 797F', 363, 2019),
        ('HT-003', 'Haul Truck', 'Komatsu 930E', 290, 2022),
        ('HT-004', 'Haul Truck', 'Komatsu 930E', 290, 2025),
        ('EX-001', 'Excavator', 'Hitachi EX5600', 0, 2017),
        ('EX-002', 'Excavator', 'Hitachi EX5600', 0, 2023)
    ]
    cursor.executemany("INSERT INTO dim_equipment VALUES (?,?,?,?,?)", equipment)
    
    locations = [
        ('PIT_A', 'North Pit Center', 'Pit', 0.0),
        ('STK_01', 'Run-of-Mine Stockpile', 'Stockpile', 3.2),
        ('CRU_01', 'Primary Gyratory Crusher', 'Crusher', 4.8)
    ]
    cursor.executemany("INSERT INTO dim_locations VALUES (?,?,?,?)", locations)
    conn.commit()

# =====================================================================
# 3. CORE SIMULATION ENGINE
# =====================================================================
def run_simulation(conn, days_to_simulate=30):
    cursor = conn.cursor()
    
    cursor.execute("SELECT equipment_id, capacity_tonnes, commission_year FROM dim_equipment WHERE equipment_type='Haul Truck'")
    trucks = [{'id': r[0], 'capacity': r[1], 'age_factor': (2026 - r[2])} for r in cursor.fetchall()]
    
    current_time = datetime(2026, 6, 1, 6, 0, 0)
    end_time = current_time + timedelta(days=days_to_simulate)
    
    print(f"Starting simulation from {current_time} to {end_time}...")
    
    logs_buffer = []
    maintenance_buffer = []
    
    weather = "Clear"
    last_weather_check_hour = -1  # Explicit hour tracker flag
    
    while current_time < end_time:
        # Check weather shifts based on a strict hourly tracker flag instead of minute matching
        if current_time.hour != last_weather_check_hour:
            last_weather_check_hour = current_time.hour
            if random.random() < 0.35:
                weather = random.choices(
                    ["Clear", "Light Rain", "Heavy Rain"], 
                    weights=[0.50, 0.35, 0.15], 
                    k=1
                )[0]
        
        weather_delay_multiplier = 1.0
        if weather == "Light Rain":
            weather_delay_multiplier = 1.2
        elif weather == "Heavy Rain":
            weather_delay_multiplier = 1.6  
            
        for truck in trucks:
            breakdown_chance = 0.002 * truck['age_factor']
            if random.random() < breakdown_chance:
                component = random.choice(['Engine', 'Hydraulics', 'Drivetrain', 'Tyres'])
                downtime = round(random.uniform(2.0, 8.0), 2)
                cost = round(downtime * random.uniform(1500, 4000), 2)
                
                maintenance_buffer.append((
                    current_time.strftime('%Y-%m-%d %H:%M:%S'),
                    truck['id'],
                    'Unscheduled Breakdown',
                    component,
                    downtime,
                    cost
                ))
                continue

            # PHASE 1: Loading
            load_time = random.normalvariate(10, 1.5) * weather_delay_multiplier
            payload = random.normalvariate(truck['capacity'] * 0.96, truck['capacity'] * 0.04)
            fuel_loading = load_time * 1.2  
            
            logs_buffer.append((
                current_time.strftime('%Y-%m-%d %H:%M:%S'),
                truck['id'], 'PIT_A', 'Loading',
                round(load_time, 2), round(payload, 2), round(fuel_loading, 2), weather
            ))
            current_time += timedelta(minutes=load_time)
            
            # PHASE 2: Hauling
            haul_time = random.normalvariate(16, 2.0) * weather_delay_multiplier
            fuel_hauling = haul_time * 5.2  
            
            logs_buffer.append((
                current_time.strftime('%Y-%m-%d %H:%M:%S'),
                truck['id'], 'CRU_01', 'Hauling',
                round(haul_time, 2), round(payload, 2), round(fuel_hauling, 2), weather
            ))
            current_time += timedelta(minutes=haul_time)
            
            # PHASE 3: Dumping
            dump_time = random.normalvariate(3, 0.5)
            fuel_dumping = dump_time * 1.0
            
            logs_buffer.append((
                current_time.strftime('%Y-%m-%d %H:%M:%S'),
                truck['id'], 'CRU_01', 'Dumping',
                round(dump_time, 2), round(payload, 2), round(fuel_dumping, 2), weather
            ))
            current_time += timedelta(minutes=dump_time)
            
            # PHASE 4: Empty Return
            return_time = random.normalvariate(12, 1.5) * weather_delay_multiplier
            fuel_return = return_time * 2.8  
            
            logs_buffer.append((
                current_time.strftime('%Y-%m-%d %H:%M:%S'),
                truck['id'], 'PIT_A', 'Empty Return',
                round(return_time, 2), 0.0, round(fuel_return, 2), weather
            ))
            current_time += timedelta(minutes=return_time)

        current_time += timedelta(minutes=15)

    cursor.executemany("""
        INSERT INTO fact_operational_logs (timestamp, equipment_id, location_id, activity, cycle_time_minutes, payload_tonnes, fuel_consumed_litres, weather_condition)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, logs_buffer)
    
    cursor.executemany("""
        INSERT INTO fact_maintenance_events (timestamp, equipment_id, event_type, component_affected, downtime_hours, repair_cost_aud)
        VALUES (?, ?, ?, ?, ?, ?)
    """, maintenance_buffer)
    
    conn.commit()
    print(f"Simulation Finished! Logged {len(logs_buffer)} production rows and {len(maintenance_buffer)} breakdown events.")

if __name__ == "__main__":
    db_file = 'mining_digital_twin.db'
    db_conn = init_database(db_file)
    seed_static_dimensions(db_conn)
    run_simulation(db_conn, days_to_simulate=30)
    db_conn.close()
    print("Database is fully packed and ready for analytics.")
