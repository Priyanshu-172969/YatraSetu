"""
test_csv_validation.py - Comprehensive Unit Tests for YatraSetu CSV Datasets
Verifies structure, BOM encoding, row counts, cross-referencing,
data types, date formats, and cost calculation arithmetic.
"""

import unittest
import os
import csv
from decimal import Decimal
from datetime import datetime
from import_data import (
    validate_all_datasets,
    EXPECTED_CORE_COLUMNS,
    EXPECTED_DETAILS_COLUMNS,
    EXPECTED_BUDGET_COLUMNS,
    COST_COMPONENTS
)

class TestCSVValidation(unittest.TestCase):

    def setUp(self):
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.core_file = os.path.join(self.base_dir, 'destination_core.csv')
        self.details_file = os.path.join(self.base_dir, 'destination_details.csv')
        self.budget_file = os.path.join(self.base_dir, 'budget_estimates.csv')

    def test_files_exist_and_unmodified(self):
        """Verifies that all three source CSV files exist in the project root."""
        self.assertTrue(os.path.exists(self.core_file), "destination_core.csv missing")
        self.assertTrue(os.path.exists(self.details_file), "destination_details.csv missing")
        self.assertTrue(os.path.exists(self.budget_file), "budget_estimates.csv missing")

    def test_utf8_bom_handling_and_columns(self):
        """Verifies that utf-8-sig correctly reads headers without leading BOM artifacts."""
        for filepath, expected_cols in [
            (self.core_file, EXPECTED_CORE_COLUMNS),
            (self.details_file, EXPECTED_DETAILS_COLUMNS),
            (self.budget_file, EXPECTED_BUDGET_COLUMNS)
        ]:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                self.assertEqual(headers, expected_cols, f"Mismatch in headers for {os.path.basename(filepath)}")

    def test_row_counts(self):
        """Verifies initial dataset counts: 30 core, 30 details, 90 budget records."""
        with open(self.core_file, 'r', encoding='utf-8-sig') as f:
            core_count = sum(1 for _ in csv.DictReader(f))
        with open(self.details_file, 'r', encoding='utf-8-sig') as f:
            details_count = sum(1 for _ in csv.DictReader(f))
        with open(self.budget_file, 'r', encoding='utf-8-sig') as f:
            budget_count = sum(1 for _ in csv.DictReader(f))

        self.assertEqual(core_count, 30, "destination_core.csv must have 30 records")
        self.assertEqual(details_count, 30, "destination_details.csv must have 30 records")
        self.assertEqual(budget_count, 90, "budget_estimates.csv must have 90 records")

    def test_cross_file_destination_ids(self):
        """Verifies 1:1 match between core and details, and 1:3 match in budget estimates."""
        with open(self.core_file, 'r', encoding='utf-8-sig') as f:
            core_ids = [int(r['destination_id']) for r in csv.DictReader(f)]
        with open(self.details_file, 'r', encoding='utf-8-sig') as f:
            details_ids = [int(r['destination_id']) for r in csv.DictReader(f)]
        with open(self.budget_file, 'r', encoding='utf-8-sig') as f:
            budget_rows = list(csv.DictReader(f))

        # Check unique IDs in core and details
        self.assertEqual(len(core_ids), len(set(core_ids)), "Core IDs contain duplicates")
        self.assertEqual(len(details_ids), len(set(details_ids)), "Details IDs contain duplicates")
        self.assertEqual(set(core_ids), set(details_ids), "Core IDs do not match Details IDs")

        # Check budget foreign key references
        budget_dest_ids = set(int(r['destination_id']) for r in budget_rows)
        self.assertEqual(set(core_ids), budget_dest_ids, "Budget destinations do not match core IDs")

    def test_starting_cities_coverage(self):
        """Verifies that every destination has estimates for Bengaluru, Kolkata, and New Delhi."""
        expected_cities = {'Bengaluru', 'Kolkata (Howrah Junction)', 'New Delhi'}
        with open(self.budget_file, 'r', encoding='utf-8-sig') as f:
            rows = list(csv.DictReader(f))

        cities_found = set(r['starting_city'] for r in rows)
        self.assertEqual(cities_found, expected_cities, "Starting cities differ from expected set")

        # Each destination should have all 3 cities
        dest_city_map = {}
        for r in rows:
            d_id = int(r['destination_id'])
            dest_city_map.setdefault(d_id, set()).add(r['starting_city'])

        for d_id, cities in dest_city_map.items():
            self.assertEqual(cities, expected_cities, f"Destination {d_id} does not have all 3 starting cities")

    def test_budget_arithmetic_integrity(self):
        """Verifies that estimated_total_budget_inr equals the exact sum of the 8 cost components."""
        with open(self.budget_file, 'r', encoding='utf-8-sig') as f:
            rows = list(csv.DictReader(f))

        for idx, r in enumerate(rows, start=2):
            component_sum = sum(Decimal(r[col]) for col in COST_COMPONENTS)
            stated_total = Decimal(r['estimated_total_budget_inr'])
            self.assertEqual(
                component_sum,
                stated_total,
                f"Row {idx} (budget_id {r['budget_id']}): component sum {component_sum} != stated total {stated_total}"
            )

    def test_date_format_validation(self):
        """Verifies that date_checked matches YYYY-MM-DD ISO format."""
        with open(self.budget_file, 'r', encoding='utf-8-sig') as f:
            rows = list(csv.DictReader(f))

        for idx, r in enumerate(rows, start=2):
            date_str = r['date_checked']
            try:
                parsed = datetime.strptime(date_str, '%Y-%m-%d')
                self.assertIsNotNone(parsed)
            except ValueError:
                self.fail(f"Row {idx}: Invalid date format '{date_str}', expected YYYY-MM-DD")

    def test_validate_all_datasets_function(self):
        """Tests the importer's pre-validation function directly."""
        valid, datasets, errors, warnings = validate_all_datasets(self.base_dir)
        self.assertTrue(valid, f"validate_all_datasets returned False with errors: {errors}")
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(datasets['core']), 30)
        self.assertEqual(len(datasets['details']), 30)
        self.assertEqual(len(datasets['budget']), 90)

if __name__ == '__main__':
    unittest.main()
