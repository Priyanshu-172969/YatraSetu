"""
init_db.py - Safe Database Initialization for YatraSetu
Creates yatrasetu_db and the 5 required application tables if they do not exist.
Never drops tables or erases existing records.
"""

import sys
import os
import mysql.connector
from config import Config

def init_database():
    """Initializes the MySQL database and five tables safely."""
    print("=" * 60)
    print("YatraSetu: Safe Database Initialization")
    print(f"Target Server: {Config.MYSQL_HOST}:{Config.MYSQL_PORT}")
    print(f"Database:      {Config.MYSQL_DATABASE}")
    print(f"User:          {Config.MYSQL_USER}")
    print("=" * 60)

    # Step 1: Connect to MySQL server without selecting database
    try:
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        print("[OK] Connected to MySQL Server successfully.")
    except mysql.connector.Error as err:
        print(f"[ERROR] Error connecting to MySQL Server ({err.errno}): {err.msg}")
        print("\nTroubleshooting tips:")
        print("1. Ensure MySQL Server is running locally (e.g., in Services or via command line).")
        print("2. Check credentials in .env file (copy from .env.example).")
        print("3. Verify MYSQL_PORT (default 3306) and MYSQL_USER/PASSWORD.")
        return False

    try:
        # Step 2: Create Database if not exists
        print(f"[*] Ensuring database '{Config.MYSQL_DATABASE}' exists...")
        cursor.execute(f"""
            CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DATABASE}`
            CHARACTER SET utf8mb4
            COLLATE utf8mb4_unicode_ci;
        """)
        cursor.execute(f"USE `{Config.MYSQL_DATABASE}`;")
        print(f"[OK] Database '{Config.MYSQL_DATABASE}' is active.")

        # Step 3: Read and execute sql/schema.sql
        schema_path = os.path.join(os.path.dirname(__file__), 'sql', 'schema.sql')
        if not os.path.exists(schema_path):
            print(f"[ERROR] Schema file not found at: {schema_path}")
            return False

        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        # Split SQL statements safely by semicolon (ignoring comments)
        statements = []
        current = []
        for line in schema_sql.splitlines():
            clean_line = line.strip()
            if clean_line.startswith('--') or not clean_line:
                continue
            current.append(line)
            if clean_line.endswith(';'):
                stmt = '\n'.join(current).strip()
                if stmt:
                    statements.append(stmt)
                current = []

        print(f"[*] Executing {len(statements)} schema statements...")
        for stmt in statements:
            cursor.execute(stmt)

        conn.commit()

        # Step 4: Verify the 5 tables
        cursor.execute("SHOW TABLES;")
        tables = [row[0] for row in cursor.fetchall()]
        expected_tables = {
            'destination_core',
            'destination_details',
            'budget_estimates',
            'trip_plans',
            'trip_plan_destinations'
        }

        print("\nExisting Tables in database:")
        for t in tables:
            marker = "[OK]" if t in expected_tables else "[?]"
            print(f"  {marker} {t}")

        missing = expected_tables - set(tables)
        if missing:
            print(f"[WARN] Missing tables: {missing}")
            return False

        print("\n[OK] All 5 required YatraSetu tables verified successfully!")
        return True

    except mysql.connector.Error as err:
        print(f"[ERROR] Database execution error ({err.errno}): {err.msg}")
        return False
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    success = init_database()
    sys.exit(0 if success else 1)
