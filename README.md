# 🇦🇺 Australian Mining Operations Digital Twin

An end-to-end digital twin simulation and data analytics platform designed to model a discrete-event **Pit-to-Port Iron Ore supply chain network** in Western Australia. 

The project bridges the gap between raw industrial machine telemetry and executive-level corporate strategy by replicating real-world mining constraints, calculating asset performance, and mapping operational metrics directly to financial outcomes.

---

## 🏗️ Project Architecture

The platform is engineered as a multi-stage data pipeline, mirroring an enterprise analytics infrastructure:

1. **Simulation Engine (Python):** A stochastic, discrete-event simulation model that generates continuous telemetry logs. It injects operational variables including randomized cycle times, payload distributions, weather anomalies (light/heavy rain delays), and asset-age-based mechanical breakdown risks.
2. **Data Warehouse (SQL):** A structured SQLite database designed using an optimized **Star Schema** to enable high-performance analytical querying. The warehouse separates static dimensions (`dim_equipment`, `dim_locations`) from granular operational and maintenance event datasets (`fact_operational_logs`, `fact_maintenance_events`).
3. **Analytics Tower (Upcoming):** An executive-level control dashboard designed to track Overall Equipment Effectiveness (OEE), cycle delays, truck queue times, and total tonnage throughput.
4. **Financial ROI Model (Upcoming):** A commercial framework that translates an operational cycle time reduction (e.g., 5% optimization) into bottom-line profitability and additional revenue capture.

---

## 🚀 Technical Stack

* **Programming Language:** Python 3.x
* **Database Engine:** SQLite / SQL Data Warehousing
* **Data Modeling:** Star Schema (Fact & Dimension Tables)
* **Target BI Environment:** Power BI / Data Visualization Layer

---

## 📊 Database Schema Blueprint

The data warehouse uses the following core relational structure:

* **`dim_equipment`**: Tracks fleet assets (Haul Trucks and Excavators), capacities, models, and commission years.
* **`dim_locations`**: Captures mining network coordinates, types (Pits, Stockpiles, Crushers), and transit distances.
* **`fact_operational_logs`**: Captures real-time streaming telemetry records for loading, hauling, dumping, and empty return activities.
* **`fact_maintenance_events`**: Records unexpected breakdown events, component failures, repair durations, and associated maintenance costs (AUD).

---

## 📈 Target Key Performance Indicators (KPIs)

The database schema is engineered specifically to calculate the following target enterprise metrics:

* **OEE (Overall Equipment Effectiveness):** Measuring fleet availability (uptime vs downtime), performance efficiency (cycle times vs benchmarks), and quality throughput (actual total tons delivered).
* **Payload Variance:** Tracking haul truck under-loading or over-loading patterns against maximum rated physical capacities to optimize structural wear-and-tear vs throughput.
* **Mean Time To Repair (MTTR):** Evaluating maintenance responsiveness, engineering execution efficiency, and mean breakdown durations categorized by component type (Engine, Tyres, Hydraulics, Drivetrain).
* **Fuel Efficiency Metrics:** Analyzing average litres burned per hauled tonne (`Fuel / Tonne`) across specific routes and weather variations to identify high-cost haul segments and optimize carbon metrics.

---

## 📊 Relational Database Schema (ERD)

GitHub renders this code block into a live visual entity-relationship diagram:

```mermaid
erDiagram
    dim_equipment ||--o{ fact_operational_logs : tracks
    dim_equipment ||--o{ fact_maintenance_events : maintains
    dim_locations ||--o{ fact_operational_logs : locates

    dim_equipment {
        string equipment_id PK
        string equipment_type
        string model
        int capacity_tonnes
        int commission_year
    }

    dim_locations {
        string location_id PK
        string location_name
        string location_type
        decimal distance_from_pit_km
    }

    fact_operational_logs {
        int log_id PK
        datetime timestamp
        string equipment_id FK
        string location_id FK
        string activity
        decimal cycle_time_minutes
        decimal payload_tonnes
        decimal fuel_consumed_litres
        string weather_condition
    }

    fact_maintenance_events {
        int event_id PK
        datetime timestamp
        string equipment_id FK
        string event_type
        string component_affected
        decimal downtime_hours
        decimal repair_cost_aud
    }
