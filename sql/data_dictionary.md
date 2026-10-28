# YatraSetu: Database Data Dictionary

Database: `yatrasetu_db`  
DBMS: MySQL 8.0.40 Community Server  
Engine: InnoDB  
Default Character Set: `utf8mb4`  
Collation: `utf8mb4_unicode_ci`  

---

## 1. Table: `destination_core`
Stores primary geographical, municipal, and categorical classifications for destinations across India.

| Column Name | Data Type | Nullable | Key | Default | Description / Purpose |
|---|---|---|---|---|---|
| `destination_id` | `INT` | NO | Primary Key | `AUTO_INCREMENT` | Unique identifier for each destination. Supports explicit IDs during CSV import. |
| `place_name` | `VARCHAR(150)` | NO | None | None | Official name of the heritage monument, natural site, or pilgrimage location. |
| `locality_city` | `VARCHAR(150)` | NO | None | None | Immediate town, city, or municipal region housing the destination. |
| `district` | `VARCHAR(100)` | NO | None | None | Administrative district of the destination. |
| `state_ut` | `VARCHAR(100)` | NO | None | None | State or Union Territory of the destination. |
| `category` | `VARCHAR(100)` | NO | None | None | Tourism category (e.g., Heritage, Religious/Pilgrimage, Wildlife, Beach/Coastal). |

---

## 2. Table: `destination_details`
Stores descriptive travel logistics, visiting hours, official references, and operational guidelines.

| Column Name | Data Type | Nullable | Key | Default | Description / Purpose |
|---|---|---|---|---|---|
| `destination_id` | `INT` | NO | Primary Key, Foreign Key | None | References `destination_core(destination_id)`. Enforces a strict 1-to-1 relationship. Cascades on core delete/update. |
| `description` | `TEXT` | NO | None | None | Comprehensive overview and historical/cultural context of the location. |
| `best_time_to_visit` | `VARCHAR(500)` | NO | None | None | Recommended seasonal window, weather advisory, or opening periods. |
| `how_to_reach` | `TEXT` | NO | None | None | Transit directions, nearest railway stations, airports, and bus terminals. |
| `major_attractions` | `TEXT` | NO | None | None | Key highlights, viewpoints, monuments, or activities at the site. |
| `entry_fee_text` | `VARCHAR(500)` | NO | None | None | Text description of ticket prices, ASI rates, camera charges, or exemptions. |
| `opening_hours_text` | `VARCHAR(500)` | NO | None | None | Operational hours, visiting slots, weekly closures, and holiday schedules. |
| `primary_official_source_url` | `VARCHAR(500)` | NO | None | None | Authoritative government or tourism board web address. |
| `supporting_source_urls` | `TEXT` | YES | None | `NULL` | Secondary verified reference links and departmental resources. |
| `local_languages` | `VARCHAR(255)` | NO | None | None | Commonly spoken regional languages in the locality. |

---

## 3. Table: `budget_estimates`
Stores itemized cost estimates, transit modes, and calculation methodologies from major Indian starting cities.

| Column Name | Data Type | Nullable | Key | Default | Description / Purpose |
|---|---|---|---|---|---|
| `budget_id` | `INT` | NO | Primary Key | `AUTO_INCREMENT` | Unique identifier for each budget estimate. |
| `destination_id` | `INT` | NO | Foreign Key, Unique (composite) | None | References `destination_core(destination_id)`. Cascades on core delete/update. |
| `starting_city` | `VARCHAR(100)` | NO | Unique (composite) | None | Origin hub (e.g., Bengaluru, Kolkata, New Delhi). Composite UNIQUE with `destination_id`. |
| `trip_duration_days` | `INT` | NO | None | None | Planned itinerary duration in days. |
| `accommodation_nights` | `INT` | NO | None | None | Number of hotel/homestay nights required. |
| `transport_mode` | `VARCHAR(255)` | NO | None | None | Transit mechanism (e.g., Economy rail/bus, flight transfer). |
| `transport_class` | `VARCHAR(255)` | NO | None | None | Indicative seat or berth class (e.g., Sleeper, 3AC, Economy air). |
| `target_travel_period` | `VARCHAR(255)` | NO | None | None | Target seasonal pricing benchmark (e.g., Non-peak season). |
| `long_distance_round_trip_cost_inr` | `DECIMAL(10,2)` | NO | None | None | Estimated round-trip intercity fare in INR. |
| `onward_transport_cost_inr` | `DECIMAL(10,2)` | NO | None | None | Cost of transfer from transit terminus to destination town in INR. |
| `local_transport_cost_inr` | `DECIMAL(10,2)` | NO | None | None | Commuting expenses within destination (auto, taxi, local bus) in INR. |
| `accommodation_cost_inr` | `DECIMAL(10,2)` | NO | None | None | Total lodging expense across all nights in INR. |
| `food_and_water_cost_inr` | `DECIMAL(10,2)` | NO | None | None | Estimated dining and hydration budget for full duration in INR. |
| `entry_and_mandatory_fees_inr` | `DECIMAL(10,2)` | NO | None | None | Monument passes, park entry fees, and mandatory charges in INR. |
| `other_essential_cost_inr` | `DECIMAL(10,2)` | NO | None | None | Incidental permits, locker fees, or temple offerings in INR. |
| `contingency_cost_inr` | `DECIMAL(10,2)` | NO | None | None | Emergency safety margin buffer in INR. |
| `estimated_total_budget_inr` | `DECIMAL(10,2)` | NO | None | None | Sum total of all 8 component cost fields in INR. |
| `calculation_methodology` | `TEXT` | NO | None | None | Explanation of cost assumptions, formula, and daily allowances. |
| `confidence_level` | `VARCHAR(100)` | NO | None | None | Reliability rating of the estimate (e.g., Prototype estimate). |
| `date_checked` | `DATE` | NO | None | None | Date on which fares and rates were verified. |
| `data_status` | `VARCHAR(100)` | NO | None | None | Operational status of the estimate row. |
| `limitations` | `TEXT` | YES | None | `NULL` | Explicit disclaimers regarding seasonal surges, inflation, or fare fluctuations. |
| `source_urls` | `TEXT` | YES | None | `NULL` | Reference links supporting tariff estimates. |

---

## 4. Table: `trip_plans`
Stores user-created itineraries, origin hubs, duration targets, and custom notes.

| Column Name | Data Type | Nullable | Key | Default | Description / Purpose |
|---|---|---|---|---|---|
| `trip_id` | `INT` | NO | Primary Key | `AUTO_INCREMENT` | Unique identifier for the trip plan. |
| `trip_name` | `VARCHAR(150)` | NO | None | None | User-assigned itinerary title (e.g., 'Golden Triangle Expedition'). |
| `starting_city` | `VARCHAR(100)` | NO | None | None | Selected departure origin hub. |
| `planned_duration_days` | `INT` | NO | None | None | Total targeted duration in days. |
| `notes` | `TEXT` | YES | None | `NULL` | Itinerary objectives, packing reminders, or group notes. |
| `created_at` | `TIMESTAMP` | NO | None | `CURRENT_TIMESTAMP` | System timestamp when the trip plan was first saved. |
| `updated_at` | `TIMESTAMP` | NO | None | `CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` | Timestamp updated automatically whenever plan details change. |

---

## 5. Table: `trip_plan_destinations`
Junction table mapping destinations to trip plans in an ordered sequence, establishing a Many-to-Many relationship.

| Column Name | Data Type | Nullable | Key | Default | Description / Purpose |
|---|---|---|---|---|---|
| `stop_id` | `INT` | NO | Primary Key | `AUTO_INCREMENT` | Unique identifier for each itinerary stop. |
| `trip_id` | `INT` | NO | Foreign Key, Unique (composite) | None | References `trip_plans(trip_id)`. Deleting a trip cascades to delete all its stops (`ON DELETE CASCADE`). |
| `destination_id` | `INT` | NO | Foreign Key | None | References `destination_core(destination_id)`. Restricts destination deletion if referenced by a saved trip (`ON DELETE RESTRICT`). |
| `visit_order` | `INT` | NO | Unique (composite) | None | Position sequence in the trip (1 = 1st stop, 2 = 2nd stop). Unique with `trip_id`. |
| `planned_days` | `INT` | NO | None | `1` | Number of days allocated specifically to this stop. |
| `stop_notes` | `TEXT` | YES | None | `NULL` | Custom notes or planned activities for this specific stop. |

---

## Referential Integrity and Foreign Key Summary
1. `destination_details.destination_id` -> `destination_core.destination_id`
   - `ON DELETE CASCADE`: Removing an unreferenced destination automatically removes its detail record.
2. `budget_estimates.destination_id` -> `destination_core.destination_id`
   - `ON DELETE CASCADE`: Removing an unreferenced destination automatically removes its budget records.
3. `trip_plan_destinations.trip_id` -> `trip_plans.trip_id`
   - `ON DELETE CASCADE`: Deleting an entire trip plan automatically cleans up all associated stop records (no orphaned stops).
4. `trip_plan_destinations.destination_id` -> `destination_core.destination_id`
   - `ON DELETE RESTRICT`: Prevents deleting any destination that is currently part of an active trip plan, preserving database consistency and preventing invalid itineraries.
