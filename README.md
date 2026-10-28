# 🏛️ YatraSetu: An Indian Destination Explorer and Trip Planner

> **College DBMS Individual Academic Project**  
> **Technologies:** Python 3 (Flask), MySQL Community Server 8.0.40, HTML5, CSS3, Vanilla JavaScript, `mysql-connector-python`  
> **Tools:** Visual Studio Code and MySQL Workbench  
> **Operating Environment:** Windows Local Development (Port `5000` / MySQL Port `3306`)

---

## 1. Project Title & Real-World Problem Statement

### Title
**YatraSetu: An Indian Destination Explorer and Trip Planner**

### Problem Statement
India possesses extraordinary cultural, archaeological, and natural travel destinations. However, prospective domestic travelers and students face significant challenges when planning journeys:
1. **Origin-Dependent Tariffs:** Travel expenses vary drastically based on the starting city (e.g., traveling to Agra or Varanasi from New Delhi vs. from Bengaluru or Kolkata entails completely different transit allowances, durations, and onward transport).
2. **Scattered Logistics:** Monument opening hours, ASI entry fee structures, and transit connections are fragmented across disparate websites.
3. **Lack of Realistic Budget Estimators:** Most commercial travel portals display dynamic, commercial tour packages rather than itemized realistic baseline costs (long-distance transit, onward connections, local auto/taxi fares, lodging, food/water, monument permits, and safety margins).

### Solution
**YatraSetu** solves these problems by providing a unified, database-driven platform where travelers can:
- Explore destinations categorized by geography, heritage classification, and visiting guidelines.
- Compare itemized 23-attribute budget estimates across major Indian starting hubs (Bengaluru, Kolkata, New Delhi).
- Create, customize, sequence, and manage multi-destination travel itineraries persisted in MySQL.
- Analyze travel statistics using advanced SQL queries (aggregates, grouping, multi-table joins, and subqueries).

---

## 2. Objectives & Main Features

- **Database-Driven Design:** Exactly 5 normalized relational tables in MySQL 8.0.40 (`yatrasetu_db`).
- **Complete CRUD Operations:** Full create, read, update, and delete functionality for Destinations and Trip Plans.
- **Relational Integrity:** Enforces strict Foreign Key constraints (`ON DELETE CASCADE` for trip stops, `ON DELETE RESTRICT` to prevent deleting destinations active in user itineraries).
- **Multi-Hub Budget Comparison:** Side-by-side comparison of 8 audited cost components across departure cities.
- **Ordered Itinerary Planner:** Custom sequencing of trip stops with automatic gap-free re-numbering.
- **SQL Analytics Dashboard:** Real-time DBMS reports demonstrating `COUNT`, `AVG`, `GROUP BY`, `HAVING`, `INNER/LEFT JOIN`, and Subqueries.
- **Atomic Importer:** Automated validation and importer for `destination_core.csv`, `destination_details.csv`, and `budget_estimates.csv` with UTF-8 BOM stripping and duplicate conflict detection.

---

## 3. Technology Stack

| Component | Technology | Role |
|---|---|---|
| **Database** | MySQL Community Server 8.0.40 | Relational database management system with InnoDB engine |
| **Backend** | Python 3.13 + Flask 3.1 | Application routing, server-side validation, transaction control |
| **DB Connector** | `mysql-connector-python` | Official Oracle MySQL driver for parameterized query execution |
| **Config Loader** | `python-dotenv` | Environment variable management from `.env` |
| **Frontend** | HTML5 + Jinja2 Templates | Semantic structure and dynamic server-side rendering |
| **Styling** | Vanilla CSS3 | Indian heritage-inspired responsive styling (self-contained, no external CDNs) |
| **Interactivity** | Vanilla JavaScript | Delete confirmation modals, client-side validation, filter helpers |
| **Tools** | VS Code & MySQL Workbench | Code editing and database schema management |

---

## 4. Project Directory Structure

```
YatraSetu/
│
├── .env.example                     <- Sample environment configuration
├── .gitignore                        <- Git ignore rules (protects credentials)
├── requirements.txt                  <- Python project dependencies
├── README.md                         <- Comprehensive project documentation
│
├── destination_core.csv              <- Source dataset: 30 destination records (UNTOUCHED)
├── destination_details.csv           <- Source dataset: 30 descriptive records (UNTOUCHED)
├── budget_estimates.csv              <- Source dataset: 90 budget-estimate records (UNTOUCHED)
│
├── config.py                         <- Application configuration & environment settings
├── db.py                             <- Database connection helper & transaction context manager
├── init_db.py                        <- Safe database & table initialization script
├── import_data.py                    <- CSV pre-validator & atomic MySQL importer
├── app.py                            <- Main Flask web application routes & logic
│
├── sql/
│   ├── schema.sql                    <- Canonical DDL for MySQL 8.0.40 (5 tables, InnoDB)
│   ├── sample_queries.sql            <- Viva-ready SQL queries (Joins, Aggregates, Subqueries)
│   └── data_dictionary.md            <- Detailed field dictionary with data types & constraints
│
├── docs/
│   ├── er_diagram_and_normalization.md <- Mermaid ER diagram & 1NF/2NF/3NF proofs
│   └── viva_prep.md                  <- Viva questions & answers for practical examination
│
├── static/
│   ├── css/
│   │   └── style.css                 <- Responsive travel visual identity & typography
│   └── js/
│       └── main.js                   <- Delete modals, alerts, and client validation
│
├── templates/
│   ├── base.html                     <- Master HTML layout with responsive navbar & footer
│   ├── index.html                    <- Home page with database statistics & highlights
│   ├── destinations/
│   │   ├── list.html                 <- Destination Explorer (search, state & category filters)
│   │   ├── detail.html               <- Detailed profile (attractions, hours, sources)
│   │   ├── form.html                 <- Create & Edit destination form (transactional)
│   │   └── manage.html               <- Destination CRUD management table
│   ├── budgets/
│   │   └── compare.html              <- Budget comparison across departure hubs
│   ├── trips/
│   │   ├── list.html                 <- Itinerary list & create new plan form
│   │   ├── detail.html               <- Itinerary stops sequence manager & stop reordering
│   │   └── edit.html                 <- Edit trip plan parameters
│   ├── reports/
│   │   └── index.html                <- SQL Reports dashboard
│   └── errors/
│       ├── 404.html                  <- Friendly 404 page
│       ├── 500.html                  <- Safe 500 error page
│       └── db_unavailable.html       <- Helpful MySQL offline connection banner
│
└── tests/
    ├── __init__.py
    ├── test_csv_validation.py        <- Validates CSV integrity, BOM, sums & types
    ├── test_sql_schema.py            <- Validates schema statements & absence of DROP commands
    ├── test_routes.py                <- Tests Flask endpoints & template rendering
    └── test_trip_logic.py            <- Tests stop sequencing & referential integrity guards
```

---

## 5. Local MySQL Server Setup

YatraSetu is configured to connect to your local MySQL 8.0 Community Server running on `127.0.0.1:3306`.

### Verifying MySQL Server Status on Windows
Open **Windows PowerShell** as Administrator and run:
```powershell
Get-Service -Name *mysql*
```
If the service is stopped, start it:
```powershell
Start-Service -Name MySQL80
```
*(Replace `MySQL80` with your installed service name if different, e.g. `mysql`).*

---

## 6. MySQL Workbench Instructions

You can create and inspect the database directly inside **MySQL Workbench**:
1. Open **MySQL Workbench** and connect to your **Local instance MySQL80** (user: `root`).
2. Click **File -> Open SQL Script...** and select `C:\Users\Priyanshu\YatraSetu\sql\schema.sql`.
3. Click the ⚡ **Execute** button (or press `Ctrl + Shift + Enter`).
4. In the left **Navigator** pane, right-click the **Schemas** area and click **Refresh All**. You will see `yatrasetu_db` with all 5 tables:
   - `destination_core`
   - `destination_details`
   - `budget_estimates`
   - `trip_plans`
   - `trip_plan_destinations`
5. To test queries, open `sql/sample_queries.sql` in Workbench and execute any query individually.

---

## 7. Environment Configuration

1. In the project root, copy `.env.example` to create `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```
2. Open `.env` in VS Code and set your local MySQL password:
   ```env
   MYSQL_HOST=127.0.0.1
   MYSQL_PORT=3306
   MYSQL_DATABASE=yatrasetu_db
   MYSQL_USER=root
   MYSQL_PASSWORD=your_actual_mysql_root_password
   SECRET_KEY=yatrasetu-secret-key-for-sessions
   ```

---

## 8. Dependency Installation

The declared project dependencies are listed in `requirements.txt`:
```powershell
pip install -r requirements.txt
```
*(Packages: `Flask`, `mysql-connector-python`, `python-dotenv`).*

---

## 9. Database Initialization & Dataset Import

Run the automated scripts in sequence from Windows PowerShell:

### Step 1: Initialize Database & Tables Safely
```powershell
python init_db.py
```
*Creates `yatrasetu_db` and the 5 tables if they do not exist. Never wipes existing data.*

### Step 2: Validate & Import Datasets
```powershell
python import_data.py
```
*Validates the 3 CSV files, verifies cost component calculations, and imports 30 destinations, 30 details, and 90 budget estimates atomically into MySQL.*

---

## 10. Running the Application

To start the Flask local development server:
```powershell
python app.py
```
Open your web browser and visit:
👉 **`http://127.0.0.1:5000`**

To stop the server, press `Ctrl + C` in PowerShell.

---

## 11. Running Automated Tests

Run the complete test suite using Python's built-in `unittest` runner:
```powershell
python -m unittest discover -s tests -v
```
All 25 tests verify:
- CSV UTF-8 BOM handling and cost component math
- SQL DDL schema definitions and constraints
- Route rendering and server-side validation
- Graceful database-offline handling (HTTP 503)
- Trip stop sequencing and referential protection

---

## 12. Database Design & Normalization Summary

Detailed documentation is available in:
- **[sql/data_dictionary.md](file:///C:/Users/Priyanshu/YatraSetu/sql/data_dictionary.md)**
- **[docs/er_diagram_and_normalization.md](file:///C:/Users/Priyanshu/YatraSetu/docs/er_diagram_and_normalization.md)**
- **[docs/viva_prep.md](file:///C:/Users/Priyanshu/YatraSetu/docs/viva_prep.md)**

### ER Diagram Summary
- `destination_core` (1:1) $\rightarrow$ `destination_details`
- `destination_core` (1:N) $\rightarrow$ `budget_estimates`
- `trip_plans` (1:N) $\rightarrow$ `trip_plan_destinations`
- `destination_core` (1:N) $\rightarrow$ `trip_plan_destinations` (forming an M:N relationship between trips and destinations)

### Normalization
- **1NF:** All column values are atomic scalar values with no repeating groups.
- **2NF:** In composite-key tables (`budget_estimates` on `[destination_id, starting_city]` and `trip_plan_destinations` on `[trip_id, visit_order]`), all non-prime attributes depend on the entire composite key.
- **3NF:** No transitive dependencies exist. Attributes depend directly on primary keys.

---

## 13. Security and Reliability Rules Followed

1. **Parameterized Queries:** All SQL statements utilize `%s` placeholders; zero string concatenation is used.
2. **Safe Transaction Handling:** Multi-table writes (adding destinations, reordering stops, importing CSVs) execute within explicit transactions and rollback on failure.
3. **No Credential Leaks:** Database passwords and raw database stack traces are never exposed in user-facing pages or templates.
4. **Referential Integrity:** `ON DELETE RESTRICT` protects destinations referenced by active itineraries from accidental deletion.
5. **Original Datasets Preserved:** The three CSV files in the project root are read using `utf-8-sig` and remain permanently unmodified.

---

## 14. Troubleshooting Common Issues

| Issue | Cause | Solution |
|---|---|---|
| **HTTP 503 "MySQL Database Connection Needed"** | MySQL Server is stopped or password in `.env` is incorrect. | Start MySQL service via PowerShell (`Start-Service MySQL80`) and verify `MYSQL_PASSWORD` in `.env`. |
| **`Access denied for user 'root'@'localhost'`** | Incorrect root password in `.env`. | Open `.env` and verify the password matches your MySQL root account password. |
| **`Can't connect to MySQL server on '127.0.0.1'`** | MySQL is running on a different port or service is not started. | Verify in MySQL Workbench which port is active (default 3306) and update `MYSQL_PORT` in `.env`. |
| **BOM Character `\ufeff` in column names** | Standard Windows UTF-8 CSV exports include a 3-byte BOM. | YatraSetu's importer reads with `utf-8-sig`, which automatically strips BOM. |
