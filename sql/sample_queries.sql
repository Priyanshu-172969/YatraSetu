-- ============================================================================
-- YatraSetu: Sample SQL Queries for Demonstration and College Viva
-- Database: yatrasetu_db (MySQL 8.0.40)
-- Covers: CRUD, Joins, Aggregates, GROUP BY, HAVING, Subqueries, & Reports
-- ============================================================================

USE yatrasetu_db;

-- ----------------------------------------------------------------------------
-- 1. BASIC CRUD OPERATIONS
-- ----------------------------------------------------------------------------

-- [READ] Select all destinations with their state and category
SELECT destination_id, place_name, state_ut, category
FROM destination_core
ORDER BY state_ut, place_name;

-- [READ with FILTER] Search destinations in a specific state
SELECT place_name, locality_city, category
FROM destination_core
WHERE state_ut = 'Rajasthan';

-- [INSERT] Add a new destination into destination_core
-- NOTE: Safe test insertion (run in a transaction or delete after testing)
START TRANSACTION;
INSERT INTO destination_core (place_name, locality_city, district, state_ut, category)
VALUES ('Hampi Monuments', 'Hampi', 'Vijayanagara', 'Karnataka', 'Heritage');

-- [INSERT] Add corresponding detail record
INSERT INTO destination_details (
    destination_id, description, best_time_to_visit, how_to_reach,
    major_attractions, entry_fee_text, opening_hours_text,
    primary_official_source_url, supporting_source_urls, local_languages
)
VALUES (
    LAST_INSERT_ID(),
    'UNESCO World Heritage site featuring ruins of the Vijayanagara Empire.',
    'October to March',
    'Nearest railway station is Hospet (13 km); Hubballi airport is 144 km.',
    'Virupaksha Temple, Vijaya Vittala Temple, Lotus Mahal',
    'INR 40 for Indians, INR 600 for foreigners',
    '6:00 AM to 6:00 PM',
    'https://karnatakatourism.org',
    'https://asi.nic.in',
    'Kannada, English, Hindi'
);
-- Rollback test data to keep database pristine:
ROLLBACK;


-- [UPDATE] Safely update notes and duration of a trip plan
UPDATE trip_plans
SET planned_duration_days = 6,
    notes = 'Updated itinerary with extended cultural exploration.'
WHERE trip_id = 1;


-- [DELETE] Safe deletion of a trip plan (Cascades automatically to its stops)
-- Notice: Stops belonging to this trip_id are automatically removed by ON DELETE CASCADE
-- Start a transaction to test safely:
START TRANSACTION;
DELETE FROM trip_plans WHERE trip_id = 999;
ROLLBACK;


-- ----------------------------------------------------------------------------
-- 2. JOINS
-- ----------------------------------------------------------------------------

-- [INNER JOIN] Combine core destination information with descriptive details
SELECT 
    c.destination_id,
    c.place_name,
    c.state_ut,
    c.category,
    d.best_time_to_visit,
    d.entry_fee_text,
    d.primary_official_source_url
FROM destination_core c
INNER JOIN destination_details d 
    ON c.destination_id = d.destination_id
ORDER BY c.place_name;


-- [INNER JOIN across 3 tables] View all stops in a specific trip plan with destination details
SELECT 
    t.trip_name,
    t.starting_city AS trip_origin,
    s.visit_order,
    c.place_name AS stop_destination,
    c.state_ut,
    s.planned_days,
    s.stop_notes
FROM trip_plans t
INNER JOIN trip_plan_destinations s 
    ON t.trip_id = s.trip_id
INNER JOIN destination_core c 
    ON s.destination_id = c.destination_id
WHERE t.trip_id = 1
ORDER BY s.visit_order ASC;


-- [LEFT JOIN] List all destinations and how many times each has been added to trip plans
-- Demonstrates destinations that have 0 plan references
SELECT 
    c.destination_id,
    c.place_name,
    c.category,
    COUNT(s.stop_id) AS total_trip_inclusions
FROM destination_core c
LEFT JOIN trip_plan_destinations s 
    ON c.destination_id = s.destination_id
GROUP BY c.destination_id, c.place_name, c.category
ORDER BY total_trip_inclusions DESC, c.place_name ASC;


-- ----------------------------------------------------------------------------
-- 3. AGGREGATES AND GROUP BY
-- ----------------------------------------------------------------------------

-- [COUNT and GROUP BY] Total destinations per Category
SELECT 
    category,
    COUNT(*) AS total_destinations
FROM destination_core
GROUP BY category
ORDER BY total_destinations DESC;


-- [COUNT and GROUP BY] Total destinations per State / Union Territory
SELECT 
    state_ut,
    COUNT(*) AS destination_count
FROM destination_core
GROUP BY state_ut
ORDER BY destination_count DESC, state_ut ASC;


-- [AVG, MIN, MAX] Budget analysis by Starting City
SELECT 
    starting_city,
    COUNT(*) AS total_routes_analyzed,
    ROUND(AVG(estimated_total_budget_inr), 2) AS avg_budget_inr,
    MIN(estimated_total_budget_inr) AS min_budget_inr,
    MAX(estimated_total_budget_inr) AS max_budget_inr,
    ROUND(AVG(long_distance_round_trip_cost_inr), 2) AS avg_transit_cost_inr,
    ROUND(AVG(accommodation_cost_inr), 2) AS avg_lodging_cost_inr
FROM budget_estimates
GROUP BY starting_city
ORDER BY avg_budget_inr ASC;


-- ----------------------------------------------------------------------------
-- 4. HAVING CLAUSE
-- ----------------------------------------------------------------------------

-- [HAVING] Categories that have more than 2 destinations
SELECT 
    category,
    COUNT(*) AS count_in_category
FROM destination_core
GROUP BY category
HAVING COUNT(*) > 2
ORDER BY count_in_category DESC;


-- [HAVING] Starting cities where average estimated budget exceeds 7,000 INR
SELECT 
    starting_city,
    ROUND(AVG(estimated_total_budget_inr), 2) AS avg_city_budget
FROM budget_estimates
GROUP BY starting_city
HAVING AVG(estimated_total_budget_inr) > 7000;


-- ----------------------------------------------------------------------------
-- 5. SUBQUERIES
-- ----------------------------------------------------------------------------

-- [SUBQUERY in WHERE] Find destinations whose budget from New Delhi is higher
-- than the overall average budget of all New Delhi estimates
SELECT 
    c.place_name,
    c.state_ut,
    b.starting_city,
    b.estimated_total_budget_inr
FROM budget_estimates b
INNER JOIN destination_core c 
    ON b.destination_id = c.destination_id
WHERE b.starting_city = 'New Delhi'
  AND b.estimated_total_budget_inr > (
      SELECT AVG(estimated_total_budget_inr)
      FROM budget_estimates
      WHERE starting_city = 'New Delhi'
  )
ORDER BY b.estimated_total_budget_inr DESC;


-- [SUBQUERY with NOT IN] Find destinations that have NOT yet been added to any trip plan
SELECT 
    destination_id,
    place_name,
    state_ut,
    category
FROM destination_core
WHERE destination_id NOT IN (
    SELECT DISTINCT destination_id 
    FROM trip_plan_destinations
);


-- [CORRELATED SUBQUERY] For each destination, find the difference between its
-- New Delhi budget and its Bengaluru budget
SELECT 
    c.place_name,
    b_delhi.estimated_total_budget_inr AS delhi_budget,
    b_blr.estimated_total_budget_inr AS blr_budget,
    (b_delhi.estimated_total_budget_inr - b_blr.estimated_total_budget_inr) AS delhi_minus_blr_diff
FROM destination_core c
JOIN budget_estimates b_delhi 
    ON c.destination_id = b_delhi.destination_id AND b_delhi.starting_city = 'New Delhi'
JOIN budget_estimates b_blr 
    ON c.destination_id = b_blr.destination_id AND b_blr.starting_city = 'Bengaluru'
ORDER BY delhi_minus_blr_diff DESC;


-- ----------------------------------------------------------------------------
-- 6. COMPREHENSIVE REPORT QUERY
-- ----------------------------------------------------------------------------

-- Joined report combining destination identity, logistics, and cost metrics
SELECT 
    c.place_name,
    c.state_ut,
    c.category,
    d.best_time_to_visit,
    b.starting_city,
    b.trip_duration_days,
    b.transport_mode,
    b.estimated_total_budget_inr,
    b.confidence_level
FROM destination_core c
INNER JOIN destination_details d 
    ON c.destination_id = d.destination_id
INNER JOIN budget_estimates b 
    ON c.destination_id = b.destination_id
WHERE b.starting_city = 'New Delhi'
ORDER BY b.estimated_total_budget_inr ASC
LIMIT 10;
