"""
import_data.py - Robust CSV Validation and Atomic Importer for YatraSetu
Safely validates and imports:
1. destination_core.csv
2. destination_details.csv
3. budget_estimates.csv

Preserves existing records and original CSV files.
Handles UTF-8 BOM, verifies cost arithmetic, checks date formats,
and rejects conflicting records while skipping identical ones.
"""

import os
import sys
import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from db import get_db_connection, DatabaseConnectionError
from config import Config

EXPECTED_CORE_COLUMNS = [
    'destination_id', 'place_name', 'locality_city', 'district', 'state_ut', 'category'
]

EXPECTED_DETAILS_COLUMNS = [
    'destination_id', 'description', 'best_time_to_visit', 'how_to_reach',
    'major_attractions', 'entry_fee_text', 'opening_hours_text',
    'primary_official_source_url', 'supporting_source_urls', 'local_languages'
]

EXPECTED_BUDGET_COLUMNS = [
    'budget_id', 'destination_id', 'starting_city', 'trip_duration_days',
    'accommodation_nights', 'transport_mode', 'transport_class',
    'target_travel_period', 'long_distance_round_trip_cost_inr',
    'onward_transport_cost_inr', 'local_transport_cost_inr',
    'accommodation_cost_inr', 'food_and_water_cost_inr',
    'entry_and_mandatory_fees_inr', 'other_essential_cost_inr',
    'contingency_cost_inr', 'estimated_total_budget_inr',
    'calculation_methodology', 'confidence_level', 'date_checked',
    'data_status', 'limitations', 'source_urls'
]

COST_COMPONENTS = [
    'long_distance_round_trip_cost_inr',
    'onward_transport_cost_inr',
    'local_transport_cost_inr',
    'accommodation_cost_inr',
    'food_and_water_cost_inr',
    'entry_and_mandatory_fees_inr',
    'other_essential_cost_inr',
    'contingency_cost_inr'
]


def load_and_validate_csv(filepath, expected_cols, file_label):
    """
    Reads a CSV file using utf-8-sig and performs structural validation.
    Returns (rows, errors_list).
    """
    if not os.path.exists(filepath):
        return None, [f"File not found: {filepath}"]

    errors = []
    rows = []

    with open(filepath, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []

        # Validate headers
        missing_cols = set(expected_cols) - set(header)
        if missing_cols:
            errors.append(f"{file_label}: Missing required columns: {sorted(list(missing_cols))}")
            return None, errors

        for row_idx, row in enumerate(reader, start=2):  # line 2 is first data row
            # Strip whitespace
            clean_row = {k.strip(): (v.strip() if v else '') for k, v in row.items()}
            rows.append((row_idx, clean_row))

    return rows, errors


def validate_all_datasets(base_dir='.'):
    """
    Performs comprehensive pre-import validation of all three datasets.
    Returns (valid: bool, data_dict, all_errors, all_warnings).
    """
    core_path = os.path.join(base_dir, 'destination_core.csv')
    details_path = os.path.join(base_dir, 'destination_details.csv')
    budget_path = os.path.join(base_dir, 'budget_estimates.csv')

    all_errors = []
    all_warnings = []

    # 1. Load CSVs
    core_rows, core_errs = load_and_validate_csv(core_path, EXPECTED_CORE_COLUMNS, "destination_core.csv")
    details_rows, details_errs = load_and_validate_csv(details_path, EXPECTED_DETAILS_COLUMNS, "destination_details.csv")
    budget_rows, budget_errs = load_and_validate_csv(budget_path, EXPECTED_BUDGET_COLUMNS, "budget_estimates.csv")

    all_errors.extend(core_errs or [])
    all_errors.extend(details_errs or [])
    all_errors.extend(budget_errs or [])

    if all_errors:
        return False, {}, all_errors, all_warnings

    # 2. Validate destination_core
    core_ids = set()
    for row_num, row in core_rows:
        d_id_str = row.get('destination_id')
        if not d_id_str or not d_id_str.isdigit():
            all_errors.append(f"destination_core.csv (Row {row_num}): Invalid or missing destination_id '{d_id_str}'")
            continue
        d_id = int(d_id_str)
        if d_id in core_ids:
            all_errors.append(f"destination_core.csv (Row {row_num}): Duplicate destination_id '{d_id}'")
        core_ids.add(d_id)

        # Check required text fields
        for field in ['place_name', 'locality_city', 'district', 'state_ut', 'category']:
            if not row.get(field):
                all_errors.append(f"destination_core.csv (Row {row_num}): Missing required field '{field}'")

    # 3. Validate destination_details
    details_ids = set()
    for row_num, row in details_rows:
        d_id_str = row.get('destination_id')
        if not d_id_str or not d_id_str.isdigit():
            all_errors.append(f"destination_details.csv (Row {row_num}): Invalid destination_id '{d_id_str}'")
            continue
        d_id = int(d_id_str)
        if d_id in details_ids:
            all_errors.append(f"destination_details.csv (Row {row_num}): Duplicate destination_id '{d_id}'")
        details_ids.add(d_id)

        # Cross-reference destination_core
        if d_id not in core_ids:
            all_errors.append(f"destination_details.csv (Row {row_num}): References destination_id {d_id} not found in destination_core.csv")

        # Required fields check
        for field in ['description', 'best_time_to_visit', 'how_to_reach', 'major_attractions', 'entry_fee_text', 'opening_hours_text', 'primary_official_source_url', 'local_languages']:
            if not row.get(field):
                all_errors.append(f"destination_details.csv (Row {row_num}): Missing required field '{field}'")

    # 4. Validate budget_estimates
    budget_ids = set()
    dest_city_pairs = set()

    for row_num, row in budget_rows:
        b_id_str = row.get('budget_id')
        if not b_id_str or not b_id_str.isdigit():
            all_errors.append(f"budget_estimates.csv (Row {row_num}): Invalid budget_id '{b_id_str}'")
            continue
        b_id = int(b_id_str)
        if b_id in budget_ids:
            all_errors.append(f"budget_estimates.csv (Row {row_num}): Duplicate budget_id '{b_id}'")
        budget_ids.add(b_id)

        d_id_str = row.get('destination_id')
        if not d_id_str or not d_id_str.isdigit():
            all_errors.append(f"budget_estimates.csv (Row {row_num}): Invalid destination_id '{d_id_str}'")
            continue
        d_id = int(d_id_str)

        # Cross-reference destination_core
        if d_id not in core_ids:
            all_errors.append(f"budget_estimates.csv (Row {row_num}): References destination_id {d_id} not found in destination_core.csv")

        city = row.get('starting_city')
        if not city:
            all_errors.append(f"budget_estimates.csv (Row {row_num}): Missing starting_city")
        else:
            pair = (d_id, city)
            if pair in dest_city_pairs:
                all_errors.append(f"budget_estimates.csv (Row {row_num}): Duplicate (destination_id, starting_city) pair: {pair}")
            dest_city_pairs.add(pair)

        # Validate integers
        for int_field in ['trip_duration_days', 'accommodation_nights']:
            val = row.get(int_field, '')
            if not val.isdigit() or int(val) < 0:
                all_errors.append(f"budget_estimates.csv (Row {row_num}): Invalid integer for '{int_field}': '{val}'")

        # Validate date format (YYYY-MM-DD)
        date_val = row.get('date_checked', '')
        try:
            datetime.strptime(date_val, '%Y-%m-%d')
        except ValueError:
            all_errors.append(f"budget_estimates.csv (Row {row_num}): Invalid date_checked format '{date_val}' (expected YYYY-MM-DD)")

        # Validate costs and arithmetic sum
        try:
            component_sum = sum(Decimal(row.get(c, '0')) for c in COST_COMPONENTS)
            total_budget = Decimal(row.get('estimated_total_budget_inr', '0'))
            if component_sum != total_budget:
                all_warnings.append(
                    f"budget_estimates.csv (Row {row_num}): Discrepancy detected for budget_id {b_id} "
                    f"({city} -> Dest {d_id}): Sum of components ({component_sum}) != stated total ({total_budget})"
                )
        except (InvalidOperation, TypeError):
            all_errors.append(f"budget_estimates.csv (Row {row_num}): Non-numeric monetary value detected")

    is_valid = len(all_errors) == 0
    data_dict = {
        'core': [r[1] for r in core_rows],
        'details': [r[1] for r in details_rows],
        'budget': [r[1] for r in budget_rows]
    }
    return is_valid, data_dict, all_errors, all_warnings


def import_all_data(base_dir='.'):
    """
    Executes the validated, atomic import into MySQL.
    Skips identical records and reports conflicting records without overwriting.
    """
    print("=" * 60)
    print("YatraSetu: CSV Validation & Atomic Importer")
    print("=" * 60)

    # Step 1: Pre-validation
    print("[*] Performing pre-import validation on CSV datasets...")
    is_valid, datasets, errors, warnings = validate_all_datasets(base_dir)

    if warnings:
        print(f"\n[WARN] Warnings ({len(warnings)}):")
        for w in warnings[:10]:
            print(f"    - {w}")

    if not is_valid:
        print(f"\n[ERROR] Validation failed with {len(errors)} errors:")
        for e in errors[:20]:
            print(f"    - {e}")
        return False, {"error": "Validation failed", "errors": errors}

    print(f"[OK] Validation passed: {len(datasets['core'])} destinations, "
          f"{len(datasets['details'])} details, {len(datasets['budget'])} budget estimates.")

    # Step 2: Connect to database
    try:
        conn = get_db_connection(include_database=True)
        cursor = conn.cursor(dictionary=True)
    except DatabaseConnectionError as e:
        print(f"\n[ERROR] Cannot connect to database: {e}")
        print("    Please start MySQL and run 'python init_db.py' first.")
        return False, {"error": str(e)}

    stats = {
        'core': {'inserted': 0, 'skipped': 0, 'rejected': 0},
        'details': {'inserted': 0, 'skipped': 0, 'rejected': 0},
        'budget': {'inserted': 0, 'skipped': 0, 'rejected': 0}
    }

    try:
        # Step 3: Import destination_core
        print("\n[*] Processing destination_core...")
        for row in datasets['core']:
            d_id = int(row['destination_id'])
            cursor.execute("SELECT * FROM destination_core WHERE destination_id = %s", (d_id,))
            existing = cursor.fetchone()

            if existing:
                # Check for identical vs conflict
                is_identical = (
                    existing['place_name'] == row['place_name'] and
                    existing['locality_city'] == row['locality_city'] and
                    existing['district'] == row['district'] and
                    existing['state_ut'] == row['state_ut'] and
                    existing['category'] == row['category']
                )
                if is_identical:
                    stats['core']['skipped'] += 1
                else:
                    print(f"[!] Conflict in destination_core id={d_id}: existing '{existing['place_name']}' != incoming '{row['place_name']}'")
                    stats['core']['rejected'] += 1
            else:
                cursor.execute("""
                    INSERT INTO destination_core (destination_id, place_name, locality_city, district, state_ut, category)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (d_id, row['place_name'], row['locality_city'], row['district'], row['state_ut'], row['category']))
                stats['core']['inserted'] += 1

        # Step 4: Import destination_details
        print("[*] Processing destination_details...")
        for row in datasets['details']:
            d_id = int(row['destination_id'])
            cursor.execute("SELECT * FROM destination_details WHERE destination_id = %s", (d_id,))
            existing = cursor.fetchone()

            if existing:
                is_identical = (
                    existing['description'] == row['description'] and
                    existing['best_time_to_visit'] == row['best_time_to_visit'] and
                    existing['how_to_reach'] == row['how_to_reach'] and
                    existing['major_attractions'] == row['major_attractions'] and
                    existing['entry_fee_text'] == row['entry_fee_text'] and
                    existing['opening_hours_text'] == row['opening_hours_text'] and
                    existing['primary_official_source_url'] == row['primary_official_source_url'] and
                    (existing['supporting_source_urls'] or '') == (row['supporting_source_urls'] or '') and
                    existing['local_languages'] == row['local_languages']
                )
                if is_identical:
                    stats['details']['skipped'] += 1
                else:
                    print(f"[!] Conflict in destination_details for destination_id={d_id}")
                    stats['details']['rejected'] += 1
            else:
                cursor.execute("""
                    INSERT INTO destination_details (
                        destination_id, description, best_time_to_visit, how_to_reach,
                        major_attractions, entry_fee_text, opening_hours_text,
                        primary_official_source_url, supporting_source_urls, local_languages
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    d_id, row['description'], row['best_time_to_visit'], row['how_to_reach'],
                    row['major_attractions'], row['entry_fee_text'], row['opening_hours_text'],
                    row['primary_official_source_url'], row['supporting_source_urls'], row['local_languages']
                ))
                stats['details']['inserted'] += 1

        # Step 5: Import budget_estimates
        print("[*] Processing budget_estimates...")
        for row in datasets['budget']:
            b_id = int(row['budget_id'])
            d_id = int(row['destination_id'])
            city = row['starting_city']

            cursor.execute("SELECT * FROM budget_estimates WHERE destination_id = %s AND starting_city = %s", (d_id, city))
            existing = cursor.fetchone()

            if existing:
                # Compare total and components
                is_identical = (
                    Decimal(str(existing['estimated_total_budget_inr'])) == Decimal(row['estimated_total_budget_inr']) and
                    int(existing['trip_duration_days']) == int(row['trip_duration_days']) and
                    existing['transport_mode'] == row['transport_mode']
                )
                if is_identical:
                    stats['budget']['skipped'] += 1
                else:
                    print(f"[!] Conflict in budget_estimates for dest={d_id}, city='{city}'")
                    stats['budget']['rejected'] += 1
            else:
                cursor.execute("""
                    INSERT INTO budget_estimates (
                        budget_id, destination_id, starting_city, trip_duration_days,
                        accommodation_nights, transport_mode, transport_class,
                        target_travel_period, long_distance_round_trip_cost_inr,
                        onward_transport_cost_inr, local_transport_cost_inr,
                        accommodation_cost_inr, food_and_water_cost_inr,
                        entry_and_mandatory_fees_inr, other_essential_cost_inr,
                        contingency_cost_inr, estimated_total_budget_inr,
                        calculation_methodology, confidence_level, date_checked,
                        data_status, limitations, source_urls
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    b_id, d_id, city, int(row['trip_duration_days']),
                    int(row['accommodation_nights']), row['transport_mode'], row['transport_class'],
                    row['target_travel_period'], Decimal(row['long_distance_round_trip_cost_inr']),
                    Decimal(row['onward_transport_cost_inr']), Decimal(row['local_transport_cost_inr']),
                    Decimal(row['accommodation_cost_inr']), Decimal(row['food_and_water_cost_inr']),
                    Decimal(row['entry_and_mandatory_fees_inr']), Decimal(row['other_essential_cost_inr']),
                    Decimal(row['contingency_cost_inr']), Decimal(row['estimated_total_budget_inr']),
                    row['calculation_methodology'], row['confidence_level'], row['date_checked'],
                    row['data_status'], row['limitations'], row['source_urls']
                ))
                stats['budget']['inserted'] += 1

        # Check if any rejections occurred
        total_rejected = sum(s['rejected'] for s in stats.values())
        if total_rejected > 0:
            print(f"\n[!] {total_rejected} conflicting records were encountered. Rolling back changes.")
            conn.rollback()
            return False, stats

        conn.commit()
        print("\n" + "=" * 60)
        print("IMPORT SUMMARY:")
        print(f"  destination_core:     Inserted {stats['core']['inserted']}, Skipped {stats['core']['skipped']}, Rejected {stats['core']['rejected']}")
        print(f"  destination_details:  Inserted {stats['details']['inserted']}, Skipped {stats['details']['skipped']}, Rejected {stats['details']['rejected']}")
        print(f"  budget_estimates:     Inserted {stats['budget']['inserted']}, Skipped {stats['budget']['skipped']}, Rejected {stats['budget']['rejected']}")
        print("=" * 60)
        print("[OK] Import transaction successfully committed.")
        return True, stats

    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Error during database transaction: {e}")
        return False, {"error": str(e)}
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    success, summary = import_all_data('.')
    sys.exit(0 if success else 1)
