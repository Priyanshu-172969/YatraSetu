-- ============================================================================
-- YatraSetu: An Indian Destination Explorer and Trip Planner
-- Relational Database Schema Definition (MySQL 8.0.40)
-- Database Name: yatrasetu_db
-- Character Set: utf8mb4 | Collation: utf8mb4_unicode_ci | Engine: InnoDB
-- ============================================================================

CREATE DATABASE IF NOT EXISTS yatrasetu_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE yatrasetu_db;

-- ----------------------------------------------------------------------------
-- Table 1: destination_core
-- Stores core identification, geographical classification, and category of destinations.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS destination_core (
    destination_id INT AUTO_INCREMENT,
    place_name VARCHAR(150) NOT NULL,
    locality_city VARCHAR(150) NOT NULL,
    district VARCHAR(100) NOT NULL,
    state_ut VARCHAR(100) NOT NULL,
    category VARCHAR(100) NOT NULL,
    PRIMARY KEY (destination_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Table 2: destination_details
-- Stores descriptive travel context, visiting guidelines, hours, and sources.
-- Relationship: 1-to-1 with destination_core (destination_id is PK and FK).
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS destination_details (
    destination_id INT NOT NULL,
    description TEXT NOT NULL,
    best_time_to_visit VARCHAR(500) NOT NULL,
    how_to_reach TEXT NOT NULL,
    major_attractions TEXT NOT NULL,
    entry_fee_text VARCHAR(500) NOT NULL,
    opening_hours_text VARCHAR(500) NOT NULL,
    primary_official_source_url VARCHAR(500) NOT NULL,
    supporting_source_urls TEXT,
    local_languages VARCHAR(255) NOT NULL,
    PRIMARY KEY (destination_id),
    CONSTRAINT fk_details_core
        FOREIGN KEY (destination_id)
        REFERENCES destination_core (destination_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Table 3: budget_estimates
-- Stores 23 cost-breakdown and methodology attributes per destination and origin.
-- Enforces uniqueness per (destination_id, starting_city).
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS budget_estimates (
    budget_id INT AUTO_INCREMENT,
    destination_id INT NOT NULL,
    starting_city VARCHAR(100) NOT NULL,
    trip_duration_days INT NOT NULL,
    accommodation_nights INT NOT NULL,
    transport_mode VARCHAR(255) NOT NULL,
    transport_class VARCHAR(255) NOT NULL,
    target_travel_period VARCHAR(255) NOT NULL,
    long_distance_round_trip_cost_inr DECIMAL(10, 2) NOT NULL,
    onward_transport_cost_inr DECIMAL(10, 2) NOT NULL,
    local_transport_cost_inr DECIMAL(10, 2) NOT NULL,
    accommodation_cost_inr DECIMAL(10, 2) NOT NULL,
    food_and_water_cost_inr DECIMAL(10, 2) NOT NULL,
    entry_and_mandatory_fees_inr DECIMAL(10, 2) NOT NULL,
    other_essential_cost_inr DECIMAL(10, 2) NOT NULL,
    contingency_cost_inr DECIMAL(10, 2) NOT NULL,
    estimated_total_budget_inr DECIMAL(10, 2) NOT NULL,
    calculation_methodology TEXT NOT NULL,
    confidence_level VARCHAR(100) NOT NULL,
    date_checked DATE NOT NULL,
    data_status VARCHAR(100) NOT NULL,
    limitations TEXT,
    source_urls TEXT,
    PRIMARY KEY (budget_id),
    CONSTRAINT uq_dest_start_city
        UNIQUE (destination_id, starting_city),
    CONSTRAINT fk_budget_core
        FOREIGN KEY (destination_id)
        REFERENCES destination_core (destination_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Table 4: trip_plans
-- Stores user-created multi-day itineraries and travel parameters.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trip_plans (
    trip_id INT AUTO_INCREMENT,
    trip_name VARCHAR(150) NOT NULL,
    starting_city VARCHAR(100) NOT NULL,
    planned_duration_days INT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (trip_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Table 5: trip_plan_destinations
-- Junction table creating a Many-to-Many relationship between trip_plans and destination_core.
-- Enforces ordered sequence of stops per trip.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trip_plan_destinations (
    stop_id INT AUTO_INCREMENT,
    trip_id INT NOT NULL,
    destination_id INT NOT NULL,
    visit_order INT NOT NULL,
    planned_days INT NOT NULL DEFAULT 1,
    stop_notes TEXT,
    PRIMARY KEY (stop_id),
    CONSTRAINT uq_trip_visit_order
        UNIQUE (trip_id, visit_order),
    CONSTRAINT fk_stop_trip
        FOREIGN KEY (trip_id)
        REFERENCES trip_plans (trip_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_stop_destination
        FOREIGN KEY (destination_id)
        REFERENCES destination_core (destination_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
