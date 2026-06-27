-- =====================================================================
-- ANALYTICAL VIEWS FOR EXECUTIVE CONTROL TOWER
-- =====================================================================

-- VIEW 1: Daily Equipment OEE & Performance Summary
CREATE VIEW IF NOT EXISTS view_daily_fleet_performance AS
SELECT 
    DATE(timestamp) AS production_date,
    equipment_id,
    COUNT(CASE WHEN activity = 'Dumping' THEN 1 END) AS total_trips_completed,
    ROUND(SUM(payload_tonnes), 2) AS total_tonnage_moved,
    ROUND(SUM(fuel_consumed_litres), 2) AS total_fuel_consumed_litres,
    ROUND(AVG(CASE WHEN activity = 'Hauling' THEN cycle_time_minutes END), 2) AS avg_haul_time_minutes,
    ROUND(SUM(fuel_consumed_litres) / SUM(payload_tonnes), 3) AS fuel_efficiency_litres_per_tonne
FROM fact_operational_logs
GROUP BY 1, 2;

-- VIEW 2: Operational Downtime & Maintenance Financial Impact
CREATE VIEW IF NOT EXISTS view_maintenance_loss_metrics AS
SELECT 
    equipment_id,
    component_affected,
    COUNT(event_id) AS breakdown_count,
    ROUND(SUM(downtime_hours), 2) AS total_downtime_hours,
    ROUND(SUM(repair_cost_aud), 2) AS total_maintenance_cost_aud,
    ROUND(AVG(downtime_hours), 2) AS mean_time_to_repair_mttr
FROM fact_maintenance_events
GROUP BY 1, 2;

-- VIEW 3: Weather Delay Analysis Matrix
CREATE VIEW IF NOT EXISTS view_weather_impact_matrix AS
SELECT 
    weather_condition,
    activity,
    ROUND(AVG(cycle_time_minutes), 2) AS avg_cycle_time_minutes,
    ROUND(AVG(fuel_consumed_litres), 2) AS avg_fuel_consumed_litres
FROM fact_operational_logs
GROUP BY 1, 2;