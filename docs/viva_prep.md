# YatraSetu: College Viva & Practical Examination Guide

This guide prepares you to explain the **YatraSetu** project during your DBMS practical examination, demonstration, and viva.

---

## 1. Project Overview & Architecture

### Q1: What is YatraSetu and what real-world problem does it solve?
**Answer:**
YatraSetu is an Indian Destination Explorer and Trip Planner. Travelers in India often struggle to estimate total trip budgets because costs vary significantly depending on the departure city (e.g., Bengaluru vs. New Delhi) and transit modes. YatraSetu solves this by storing normalized destination information, 23-attribute itemized budget estimates from multiple origin hubs, and an interactive itinerary planner that lets users sequence destinations into multi-day trip plans.

### Q2: What is the architectural pattern of this project?
**Answer:**
YatraSetu follows a classic **3-Tier Client-Server Architecture**:
1. **Presentation Tier (Frontend):** HTML5, responsive CSS3, Jinja2 template rendering, and vanilla JavaScript for dynamic interactions.
2. **Application Tier (Backend):** Python with Flask handling routing, server-side data validation, transaction management, and business logic.
3. **Data Tier (Database):** MySQL 8.0.40 Community Server storing data in 5 normalized relational tables managed by InnoDB engine with parameterized queries executed via `mysql-connector-python`.

---

## 2. Database Design & Normalization

### Q3: How many tables exist in your database and what are their roles?
**Answer:**
Exactly **five tables**:
1. `destination_core`: Stores primary identity and location (name, city, district, state/UT, category).
2. `destination_details`: 1:1 relationship with core; stores extensive narrative, visiting hours, entry fees, and government links.
3. `budget_estimates`: 1:N relationship with core; stores 23 fields covering 8 itemized cost components, duration, transit mode, confidence level, and source notes for each (destination, starting city) pair.
4. `trip_plans`: Stores user-created itinerary headers (name, starting city, total planned days, notes).
5. `trip_plan_destinations`: Junction table creating an M:N relationship between `trip_plans` and `destination_core`, enforcing visit sequence order and stop duration.

### Q4: Why is `destination_details` separate from `destination_core`?
**Answer:**
For two main reasons:
1. **Performance & Buffer Pool Optimization:** Frequent browse and filter queries only need short columns (`place_name`, `state_ut`, `category`). Keeping large `TEXT` columns in a separate 1:1 table allows MySQL InnoDB B-tree pages for `destination_core` to stay compact in memory.
2. **Logical Separation of Concerns:** Core geographical metadata is distinct from operational visitor logistics and narrative descriptions.

### Q5: How does your database achieve 3NF?
**Answer:**
- **1NF:** Every column has atomic scalar values, and there are no repeating groups.
- **2NF:** In tables with composite keys like `budget_estimates` (`destination_id`, `starting_city`) and `trip_plan_destinations` (`trip_id`, `visit_order`), all non-prime attributes (e.g., travel cost, planned stop days) depend on the complete composite key, not just a part of it.
- **3NF:** There are no transitive dependencies ($X \rightarrow Y \rightarrow Z$). Non-key attributes depend only on the primary key.

### Q6: What referential actions did you choose and why?
**Answer:**
- `trip_plans` $\rightarrow$ `trip_plan_destinations`: **`ON DELETE CASCADE`**. When a trip plan is deleted, its associated stops are automatically deleted, ensuring no orphaned stops remain.
- `destination_core` $\rightarrow$ `trip_plan_destinations`: **`ON DELETE RESTRICT`**. A destination that is actively part of a user's trip plan cannot be deleted. MySQL rejects the deletion to prevent corrupting saved itineraries.
- `destination_core` $\rightarrow$ `destination_details` / `budget_estimates`: **`ON DELETE CASCADE`**. If an unreferenced destination is removed, its associated details and tariff estimates are cleanly purged.

---

## 3. SQL & Query Execution

### Q7: How do you prevent SQL Injection?
**Answer:**
We use **parameterized queries** everywhere. Instead of concatenating user strings (`f"SELECT * FROM users WHERE name='{name}'"`), we pass query placeholders (`%s`) and supply parameters as a separate tuple to `cursor.execute(query, (name,))`. MySQL's connector handles proper escaping and binary protocol typing, completely preventing SQL injection.

### Q8: Give an example of a SQL Join used in YatraSetu.
**Answer:**
In the Trip Details view, an **INNER JOIN across 3 tables** fetches itinerary stops with their place name and state:
```sql
SELECT t.trip_name, s.visit_order, c.place_name, c.state_ut, s.planned_days
FROM trip_plans t
INNER JOIN trip_plan_destinations s ON t.trip_id = s.trip_id
INNER JOIN destination_core c ON s.destination_id = c.destination_id
WHERE t.trip_id = %s
ORDER BY s.visit_order ASC;
```

### Q9: Give an example of an Aggregate function with GROUP BY and HAVING.
**Answer:**
To list categories that have more than 2 destinations:
```sql
SELECT category, COUNT(*) AS total
FROM destination_core
GROUP BY category
HAVING COUNT(*) > 2
ORDER BY total DESC;
```

### Q10: Give an example of a Subquery used in your project.
**Answer:**
In reports, to find destinations whose New Delhi budget is greater than the average of all New Delhi estimates:
```sql
SELECT c.place_name, b.estimated_total_budget_inr
FROM budget_estimates b
JOIN destination_core c ON b.destination_id = c.destination_id
WHERE b.starting_city = 'New Delhi'
  AND b.estimated_total_budget_inr > (
      SELECT AVG(estimated_total_budget_inr) 
      FROM budget_estimates 
      WHERE starting_city = 'New Delhi'
  );
```

---

## 4. Transactions and Integrity

### Q11: Where are database transactions (`START TRANSACTION`, `COMMIT`, `ROLLBACK`) used in YatraSetu?
**Answer:**
Transactions are critical in three operations:
1. **Destination Creation / Edit:** Adding a destination inserts a row into `destination_core` and another into `destination_details`. If the second insert fails, the transaction is rolled back so no half-created destination exists.
2. **Stop Reordering:** When a user changes stop orders or removes a stop, multiple stop sequence numbers must be updated atomically.
3. **Data Importer (`import_data.py`):** Inserts records across core, details, and budget tables within managed transactions so that import batches are atomic.

---

## 5. Data Importer & Edge Cases

### Q12: How does your importer handle UTF-8 BOM and duplicate records?
**Answer:**
1. **UTF-8 BOM:** The importer opens CSV files using Python's `utf-8-sig` encoding, which automatically strips the `\ufeff` Byte Order Mark from header column names.
2. **Safe Re-run:** For each row, it queries existing database records. If an identical row exists, it skips it cleanly. If a record has the same primary key or composite unique key but conflicting values, it flags a conflict and rejects the record rather than silently overwriting.
3. **Data Verification:** It verifies that the sum of the 8 individual cost components matches `estimated_total_budget_inr` and validates ISO date formats before inserting into MySQL `DATE` fields.
