"""
test_sql_schema.py - Automated Tests for SQL Schema & Queries
Verifies canonical MySQL 8.0.40 DDL statements, constraint definitions,
InnoDB engine, utf8mb4 encoding, and absence of destructive DROP commands.
"""

import unittest
import os
import re

class TestSQLSchema(unittest.TestCase):

    def setUp(self):
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.schema_file = os.path.join(self.base_dir, 'sql', 'schema.sql')
        self.queries_file = os.path.join(self.base_dir, 'sql', 'sample_queries.sql')

    def test_schema_file_exists(self):
        """Verifies sql/schema.sql and sql/sample_queries.sql exist."""
        self.assertTrue(os.path.exists(self.schema_file))
        self.assertTrue(os.path.exists(self.queries_file))

    def test_no_destructive_statements(self):
        """Verifies schema.sql does NOT contain DROP TABLE or DROP DATABASE."""
        with open(self.schema_file, 'r', encoding='utf-8') as f:
            content = f.read().upper()

        self.assertNotIn("DROP DATABASE", content, "schema.sql must never contain DROP DATABASE")
        self.assertNotIn("DROP TABLE", content, "schema.sql must never contain DROP TABLE")

    def test_exactly_five_tables_defined(self):
        """Verifies that CREATE TABLE IF NOT EXISTS defines exactly the 5 required tables."""
        with open(self.schema_file, 'r', encoding='utf-8') as f:
            content = f.read()

        matches = re.findall(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z0-9_]+)', content, re.IGNORECASE)
        table_names = set(m.lower() for m in matches)
        expected_tables = {
            'destination_core',
            'destination_details',
            'budget_estimates',
            'trip_plans',
            'trip_plan_destinations'
        }
        self.assertEqual(table_names, expected_tables, f"Defined tables differ: {table_names}")

    def test_engine_and_character_set(self):
        """Verifies InnoDB and utf8mb4 are used."""
        with open(self.schema_file, 'r', encoding='utf-8') as f:
            content = f.read().upper()

        self.assertIn("ENGINE=INNODB", content.replace(" ", ""))
        self.assertIn("UTF8MB4", content)

    def test_referential_constraints_present(self):
        """Verifies ON DELETE RESTRICT on trip_plan_destinations -> destination_core and ON DELETE CASCADE on stops -> trip."""
        with open(self.schema_file, 'r', encoding='utf-8') as f:
            content = f.read().upper()

        self.assertIn("ON DELETE RESTRICT", content, "Missing ON DELETE RESTRICT for destination protection")
        self.assertIn("ON DELETE CASCADE", content, "Missing ON DELETE CASCADE for cascading deletions")
        self.assertIn("UQ_DEST_START_CITY", content, "Missing unique constraint on destination and starting city")
        self.assertIn("UQ_TRIP_VISIT_ORDER", content, "Missing unique constraint on trip visit order")

    def test_sample_queries_syntax_coverage(self):
        """Verifies sample_queries.sql covers JOIN, GROUP BY, HAVING, and Subqueries."""
        with open(self.queries_file, 'r', encoding='utf-8') as f:
            content = f.read().upper()

        self.assertIn("INNER JOIN", content)
        self.assertIn("LEFT JOIN", content)
        self.assertIn("GROUP BY", content)
        self.assertIn("HAVING", content)
        self.assertIn("SELECT AVG(", content)
        self.assertIn("NOT IN (", content)

if __name__ == '__main__':
    unittest.main()
