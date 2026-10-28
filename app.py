"""
app.py - Main Flask Application for YatraSetu
An Indian Destination Explorer and Trip Planner
College DBMS Individual Academic Project
"""

import math
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from config import Config
from db import (
    get_db_cursor, fetch_all, fetch_one, execute_query,
    DatabaseConnectionError, DatabaseQueryError, check_db_connection
)

app = Flask(__name__)
app.config.from_object(Config)


# ----------------------------------------------------------------------------
# Error Handlers
# ----------------------------------------------------------------------------
@app.errorhandler(DatabaseConnectionError)
def handle_db_connection_error(error):
    return render_template('errors/db_unavailable.html', db_message=str(error)), 503

@app.errorhandler(404)
def handle_not_found(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def handle_internal_error(error):
    return render_template('errors/500.html', error_message="Internal Server Error"), 500


# ----------------------------------------------------------------------------
# 1. Home Page
# ----------------------------------------------------------------------------
@app.route('/')
def home():
    try:
        # Check DB connection
        connected, msg = check_db_connection()
        if not connected:
            raise DatabaseConnectionError(msg)

        # 1. Database-driven summary statistics
        stats = {
            'total_destinations': fetch_one("SELECT COUNT(*) AS c FROM destination_core")['c'],
            'total_states': fetch_one("SELECT COUNT(DISTINCT state_ut) AS c FROM destination_core")['c'],
            'total_categories': fetch_one("SELECT COUNT(DISTINCT category) AS c FROM destination_core")['c'],
            'total_budgets': fetch_one("SELECT COUNT(*) AS c FROM budget_estimates")['c']
        }

        # 2. Selected destination highlights
        highlights = fetch_all("""
            SELECT c.destination_id, c.place_name, c.locality_city, c.state_ut, c.category,
                   d.description
            FROM destination_core c
            LEFT JOIN destination_details d ON c.destination_id = d.destination_id
            ORDER BY c.destination_id ASC
            LIMIT 6
        """)

        return render_template('index.html', stats=stats, highlights=highlights)

    except DatabaseConnectionError as e:
        return render_template('errors/db_unavailable.html', db_message=str(e)), 503


# ----------------------------------------------------------------------------
# 2. Destination Explorer
# ----------------------------------------------------------------------------
@app.route('/destinations')
def destination_list():
    try:
        search_query = request.args.get('q', '').strip()
        selected_state = request.args.get('state', '').strip()
        selected_category = request.args.get('category', '').strip()
        page = max(1, int(request.args.get('page', 1)))
        per_page = 9

        # Dynamic filter dropdown options from database
        states = [row['state_ut'] for row in fetch_all(
            "SELECT DISTINCT state_ut FROM destination_core ORDER BY state_ut ASC"
        )]
        categories = [row['category'] for row in fetch_all(
            "SELECT DISTINCT category FROM destination_core ORDER BY category ASC"
        )]

        # Construct parameterized SQL filter conditions
        where_clauses = []
        params = []

        if search_query:
            where_clauses.append("(c.place_name LIKE %s OR c.locality_city LIKE %s)")
            params.extend([f"%{search_query}%", f"%{search_query}%"])

        if selected_state:
            where_clauses.append("c.state_ut = %s")
            params.append(selected_state)

        if selected_category:
            where_clauses.append("c.category = %s")
            params.append(selected_category)

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        # Total matching records count for pagination
        count_query = f"SELECT COUNT(*) AS total FROM destination_core c {where_sql}"
        total_matches = fetch_one(count_query, params)['total']
        total_pages = max(1, math.ceil(total_matches / per_page))
        offset = (page - 1) * per_page

        # Fetch paginated destinations with details
        dest_query = f"""
            SELECT c.destination_id, c.place_name, c.locality_city, c.district, c.state_ut, c.category,
                   d.description
            FROM destination_core c
            LEFT JOIN destination_details d ON c.destination_id = d.destination_id
            {where_sql}
            ORDER BY c.place_name ASC
            LIMIT %s OFFSET %s
        """
        dest_params = params + [per_page, offset]
        destinations = fetch_all(dest_query, dest_params)

        return render_template(
            'destinations/list.html',
            destinations=destinations,
            states=states,
            categories=categories,
            search_query=search_query,
            selected_state=selected_state,
            selected_category=selected_category,
            current_page=page,
            total_pages=total_pages,
            total_matches=total_matches
        )

    except DatabaseConnectionError as e:
        return render_template('errors/db_unavailable.html', db_message=str(e)), 503


# ----------------------------------------------------------------------------
# 3. Destination Detail Page
# ----------------------------------------------------------------------------
@app.route('/destinations/<int:destination_id>')
def destination_detail(destination_id):
    try:
        destination = fetch_one("""
            SELECT c.destination_id, c.place_name, c.locality_city, c.district, c.state_ut, c.category,
                   d.description, d.best_time_to_visit, d.how_to_reach, d.major_attractions,
                   d.entry_fee_text, d.opening_hours_text, d.primary_official_source_url,
                   d.supporting_source_urls, d.local_languages
            FROM destination_core c
            LEFT JOIN destination_details d ON c.destination_id = d.destination_id
            WHERE c.destination_id = %s
        """, (destination_id,))

        if not destination:
            abort(404)

        # Get existing trips for the quick "Add to Trip" form
        trips = fetch_all("SELECT trip_id, trip_name, starting_city FROM trip_plans ORDER BY trip_name ASC")

        return render_template('destinations/detail.html', destination=destination, trips=trips)

    except DatabaseConnectionError as e:
        return render_template('errors/db_unavailable.html', db_message=str(e)), 503


# ----------------------------------------------------------------------------
# 4. Budget Comparison
# ----------------------------------------------------------------------------
@app.route('/budgets')
def budget_compare():
    try:
        dest_id = request.args.get('destination_id')
        destinations = fetch_all("SELECT destination_id, place_name, locality_city, state_ut, category FROM destination_core ORDER BY place_name ASC")

        selected_dest = None
        estimates = []

        if dest_id and dest_id.isdigit():
            dest_id = int(dest_id)
            selected_dest = fetch_one("SELECT * FROM destination_core WHERE destination_id = %s", (dest_id,))
            if selected_dest:
                estimates = fetch_all("""
                    SELECT * FROM budget_estimates
                    WHERE destination_id = %s
                    ORDER BY estimated_total_budget_inr ASC
                """, (dest_id,))

        return render_template(
            'budgets/compare.html',
            destinations=destinations,
            selected_dest=selected_dest,
            estimates=estimates
        )

    except DatabaseConnectionError as e:
        return render_template('errors/db_unavailable.html', db_message=str(e)), 503


# ----------------------------------------------------------------------------
# 5. Trip Planner (CRUD)
# ----------------------------------------------------------------------------
@app.route('/trips')
def trip_list():
    try:
        # Fetch trips with count of stops
        trips = fetch_all("""
            SELECT t.trip_id, t.trip_name, t.starting_city, t.planned_duration_days, t.notes,
                   t.created_at, COUNT(s.stop_id) AS total_stops
            FROM trip_plans t
            LEFT JOIN trip_plan_destinations s ON t.trip_id = s.trip_id
            GROUP BY t.trip_id, t.trip_name, t.starting_city, t.planned_duration_days, t.notes, t.created_at
            ORDER BY t.created_at DESC
        """)

        # Database-driven starting cities
        city_rows = fetch_all("SELECT DISTINCT starting_city FROM budget_estimates ORDER BY starting_city ASC")
        starting_cities = [r['starting_city'] for r in city_rows]

        return render_template('trips/list.html', trips=trips, starting_cities=starting_cities)

    except DatabaseConnectionError as e:
        return render_template('errors/db_unavailable.html', db_message=str(e)), 503


@app.route('/trips/create', methods=['POST'])
def trip_create():
    try:
        trip_name = request.form.get('trip_name', '').strip()
        starting_city = request.form.get('starting_city', '').strip()
        planned_duration_days = request.form.get('planned_duration_days', '1').strip()
        notes = request.form.get('notes', '').strip()

        if not trip_name or not starting_city:
            flash("Trip name and starting city are required.", "error")
            return redirect(url_for('trip_list'))

        days = int(planned_duration_days) if planned_duration_days.isdigit() else 1

        trip_id = execute_query("""
            INSERT INTO trip_plans (trip_name, starting_city, planned_duration_days, notes)
            VALUES (%s, %s, %s, %s)
        """, (trip_name, starting_city, days, notes if notes else None))

        flash(f"Trip plan '{trip_name}' created successfully!", "success")
        return redirect(url_for('trip_detail', trip_id=trip_id))

    except Exception as e:
        flash(f"Error creating trip plan: {e}", "error")
        return redirect(url_for('trip_list'))


@app.route('/trips/<int:trip_id>')
def trip_detail(trip_id):
    try:
        trip = fetch_one("SELECT * FROM trip_plans WHERE trip_id = %s", (trip_id,))
        if not trip:
            abort(404)

        # Fetch stops ordered by sequence
        stops = fetch_all("""
            SELECT s.stop_id, s.trip_id, s.destination_id, s.visit_order, s.planned_days, s.stop_notes,
                   c.place_name, c.locality_city, c.state_ut, c.category
            FROM trip_plan_destinations s
            INNER JOIN destination_core c ON s.destination_id = c.destination_id
            WHERE s.trip_id = %s
            ORDER BY s.visit_order ASC
        """, (trip_id,))

        all_destinations = fetch_all("SELECT destination_id, place_name, state_ut FROM destination_core ORDER BY place_name ASC")

        return render_template('trips/detail.html', trip=trip, stops=stops, all_destinations=all_destinations)

    except DatabaseConnectionError as e:
        return render_template('errors/db_unavailable.html', db_message=str(e)), 503


@app.route('/trips/<int:trip_id>/edit', methods=['GET', 'POST'])
def trip_edit(trip_id):
    try:
        trip = fetch_one("SELECT * FROM trip_plans WHERE trip_id = %s", (trip_id,))
        if not trip:
            abort(404)

        if request.method == 'POST':
            trip_name = request.form.get('trip_name', '').strip()
            starting_city = request.form.get('starting_city', '').strip()
            planned_duration_days = request.form.get('planned_duration_days', '1').strip()
            notes = request.form.get('notes', '').strip()

            if not trip_name or not starting_city:
                flash("Trip name and starting city are required.", "error")
                return redirect(url_for('trip_edit', trip_id=trip_id))

            days = int(planned_duration_days) if planned_duration_days.isdigit() else 1

            execute_query("""
                UPDATE trip_plans
                SET trip_name = %s, starting_city = %s, planned_duration_days = %s, notes = %s
                WHERE trip_id = %s
            """, (trip_name, starting_city, days, notes if notes else None, trip_id))

            flash("Trip plan details updated.", "success")
            return redirect(url_for('trip_detail', trip_id=trip_id))

        city_rows = fetch_all("SELECT DISTINCT starting_city FROM budget_estimates ORDER BY starting_city ASC")
        starting_cities = [r['starting_city'] for r in city_rows]

        return render_template('trips/edit.html', trip=trip, starting_cities=starting_cities)

    except DatabaseConnectionError as e:
        return render_template('errors/db_unavailable.html', db_message=str(e)), 503


@app.route('/trips/<int:trip_id>/delete', methods=['POST'])
def trip_delete(trip_id):
    try:
        trip = fetch_one("SELECT trip_name FROM trip_plans WHERE trip_id = %s", (trip_id,))
        if trip:
            execute_query("DELETE FROM trip_plans WHERE trip_id = %s", (trip_id,))
            flash(f"Trip '{trip['trip_name']}' and its scheduled stops were deleted.", "success")
        return redirect(url_for('trip_list'))
    except Exception as e:
        flash(f"Error deleting trip: {e}", "error")
        return redirect(url_for('trip_list'))


@app.route('/trips/<int:trip_id>/stops/add', methods=['POST'])
def trip_add_stop(trip_id):
    try:
        destination_id = int(request.form.get('destination_id'))
        planned_days = int(request.form.get('planned_days', 1))
        stop_notes = request.form.get('stop_notes', '').strip()

        # Calculate next visit_order
        max_order_row = fetch_one("SELECT MAX(visit_order) AS m FROM trip_plan_destinations WHERE trip_id = %s", (trip_id,))
        next_order = (max_order_row['m'] or 0) + 1

        execute_query("""
            INSERT INTO trip_plan_destinations (trip_id, destination_id, visit_order, planned_days, stop_notes)
            VALUES (%s, %s, %s, %s, %s)
        """, (trip_id, destination_id, next_order, planned_days, stop_notes if stop_notes else None))

        flash("Destination stop added to itinerary.", "success")
        return redirect(url_for('trip_detail', trip_id=trip_id))

    except Exception as e:
        flash(f"Error adding stop: {e}", "error")
        return redirect(url_for('trip_detail', trip_id=trip_id))


@app.route('/destinations/<int:destination_id>/add-to-trip', methods=['POST'])
def trip_add_stop_from_dest(destination_id):
    try:
        trip_id = int(request.form.get('trip_id'))
        planned_days = int(request.form.get('planned_days', 1))

        max_order_row = fetch_one("SELECT MAX(visit_order) AS m FROM trip_plan_destinations WHERE trip_id = %s", (trip_id,))
        next_order = (max_order_row['m'] or 0) + 1

        execute_query("""
            INSERT INTO trip_plan_destinations (trip_id, destination_id, visit_order, planned_days, stop_notes)
            VALUES (%s, %s, %s, %s, %s)
        """, (trip_id, destination_id, next_order, planned_days, None))

        flash("Destination added to your selected itinerary!", "success")
        return redirect(url_for('trip_detail', trip_id=trip_id))

    except Exception as e:
        flash(f"Error adding to trip: {e}", "error")
        return redirect(url_for('destination_detail', destination_id=destination_id))


@app.route('/trips/<int:trip_id>/stops/<int:stop_id>/delete', methods=['POST'])
def trip_delete_stop(trip_id, stop_id):
    try:
        with get_db_cursor(commit=True) as cursor:
            # Delete the stop
            cursor.execute("DELETE FROM trip_plan_destinations WHERE stop_id = %s AND trip_id = %s", (stop_id, trip_id))

            # Re-sequence remaining stops (1, 2, 3...) to prevent gaps
            cursor.execute("SELECT stop_id FROM trip_plan_destinations WHERE trip_id = %s ORDER BY visit_order ASC", (trip_id,))
            remaining = cursor.fetchall()
            for idx, r in enumerate(remaining, start=1):
                cursor.execute("UPDATE trip_plan_destinations SET visit_order = %s WHERE stop_id = %s", (idx, r['stop_id']))

        flash("Stop removed and sequence re-numbered.", "success")
        return redirect(url_for('trip_detail', trip_id=trip_id))

    except Exception as e:
        flash(f"Error removing stop: {e}", "error")
        return redirect(url_for('trip_detail', trip_id=trip_id))


@app.route('/trips/<int:trip_id>/stops/<int:stop_id>/move/<direction>', methods=['POST'])
def trip_move_stop(trip_id, stop_id, direction):
    try:
        with get_db_cursor(commit=True) as cursor:
            # Fetch current stop's order
            cursor.execute("SELECT visit_order FROM trip_plan_destinations WHERE stop_id = %s AND trip_id = %s", (stop_id, trip_id))
            current = cursor.fetchone()
            if not current:
                return redirect(url_for('trip_detail', trip_id=trip_id))

            curr_order = current['visit_order']
            target_order = curr_order - 1 if direction == 'up' else curr_order + 1

            # Fetch the adjacent stop
            cursor.execute("SELECT stop_id FROM trip_plan_destinations WHERE trip_id = %s AND visit_order = %s", (trip_id, target_order))
            adjacent = cursor.fetchone()

            if adjacent:
                # Swap visit_orders atomically using a temporary placeholder to avoid UNIQUE constraint violation
                adj_id = adjacent['stop_id']
                cursor.execute("UPDATE trip_plan_destinations SET visit_order = 0 WHERE stop_id = %s", (stop_id,))
                cursor.execute("UPDATE trip_plan_destinations SET visit_order = %s WHERE stop_id = %s", (curr_order, adj_id))
                cursor.execute("UPDATE trip_plan_destinations SET visit_order = %s WHERE stop_id = %s", (target_order, stop_id))

        flash("Stop order updated.", "success")
        return redirect(url_for('trip_detail', trip_id=trip_id))

    except Exception as e:
        flash(f"Error moving stop: {e}", "error")
        return redirect(url_for('trip_detail', trip_id=trip_id))


# ----------------------------------------------------------------------------
# 6. Destination Management (CRUD)
# ----------------------------------------------------------------------------
@app.route('/manage/destinations')
def manage_destinations():
    try:
        search_query = request.args.get('q', '').strip()
        where_clause = ""
        params = []

        if search_query:
            where_clause = "WHERE c.place_name LIKE %s OR c.state_ut LIKE %s"
            params = [f"%{search_query}%", f"%{search_query}%"]

        # Destination query with active trip stop count for referential check
        destinations = fetch_all(f"""
            SELECT c.destination_id, c.place_name, c.locality_city, c.district, c.state_ut, c.category,
                   COUNT(s.stop_id) AS active_trip_stops
            FROM destination_core c
            LEFT JOIN trip_plan_destinations s ON c.destination_id = s.destination_id
            {where_clause}
            GROUP BY c.destination_id, c.place_name, c.locality_city, c.district, c.state_ut, c.category
            ORDER BY c.destination_id ASC
        """, params)

        return render_template('destinations/manage.html', destinations=destinations, search_query=search_query)

    except DatabaseConnectionError as e:
        return render_template('errors/db_unavailable.html', db_message=str(e)), 503


@app.route('/destinations/new', methods=['GET', 'POST'])
def destination_create():
    try:
        if request.method == 'POST':
            # Extract Core attributes
            place_name = request.form.get('place_name', '').strip()
            locality_city = request.form.get('locality_city', '').strip()
            district = request.form.get('district', '').strip()
            state_ut = request.form.get('state_ut', '').strip()
            category = request.form.get('category', '').strip()

            # Extract Details attributes
            description = request.form.get('description', '').strip()
            best_time_to_visit = request.form.get('best_time_to_visit', '').strip()
            how_to_reach = request.form.get('how_to_reach', '').strip()
            major_attractions = request.form.get('major_attractions', '').strip()
            entry_fee_text = request.form.get('entry_fee_text', '').strip()
            opening_hours_text = request.form.get('opening_hours_text', '').strip()
            primary_official_source_url = request.form.get('primary_official_source_url', '').strip()
            supporting_source_urls = request.form.get('supporting_source_urls', '').strip()
            local_languages = request.form.get('local_languages', '').strip()

            # Transactional multi-table write
            with get_db_cursor(commit=True) as cursor:
                cursor.execute("""
                    INSERT INTO destination_core (place_name, locality_city, district, state_ut, category)
                    VALUES (%s, %s, %s, %s, %s)
                """, (place_name, locality_city, district, state_ut, category))

                dest_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO destination_details (
                        destination_id, description, best_time_to_visit, how_to_reach,
                        major_attractions, entry_fee_text, opening_hours_text,
                        primary_official_source_url, supporting_source_urls, local_languages
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    dest_id, description, best_time_to_visit, how_to_reach,
                    major_attractions, entry_fee_text, opening_hours_text,
                    primary_official_source_url, supporting_source_urls if supporting_source_urls else None,
                    local_languages
                ))

            flash(f"Destination '{place_name}' successfully created in database!", "success")
            return redirect(url_for('destination_detail', destination_id=dest_id))

        return render_template('destinations/form.html', destination=None, is_edit=False)

    except DatabaseConnectionError as e:
        return render_template('errors/db_unavailable.html', db_message=str(e)), 503
    except Exception as e:
        flash(f"Error creating destination: {e}", "error")
        return render_template('destinations/form.html', destination=request.form, is_edit=False)


@app.route('/destinations/<int:destination_id>/edit', methods=['GET', 'POST'])
def destination_edit(destination_id):
    try:
        destination = fetch_one("""
            SELECT c.*, d.description, d.best_time_to_visit, d.how_to_reach, d.major_attractions,
                   d.entry_fee_text, d.opening_hours_text, d.primary_official_source_url,
                   d.supporting_source_urls, d.local_languages
            FROM destination_core c
            LEFT JOIN destination_details d ON c.destination_id = d.destination_id
            WHERE c.destination_id = %s
        """, (destination_id,))

        if not destination:
            abort(404)

        if request.method == 'POST':
            place_name = request.form.get('place_name', '').strip()
            locality_city = request.form.get('locality_city', '').strip()
            district = request.form.get('district', '').strip()
            state_ut = request.form.get('state_ut', '').strip()
            category = request.form.get('category', '').strip()

            description = request.form.get('description', '').strip()
            best_time_to_visit = request.form.get('best_time_to_visit', '').strip()
            how_to_reach = request.form.get('how_to_reach', '').strip()
            major_attractions = request.form.get('major_attractions', '').strip()
            entry_fee_text = request.form.get('entry_fee_text', '').strip()
            opening_hours_text = request.form.get('opening_hours_text', '').strip()
            primary_official_source_url = request.form.get('primary_official_source_url', '').strip()
            supporting_source_urls = request.form.get('supporting_source_urls', '').strip()
            local_languages = request.form.get('local_languages', '').strip()

            # Transactional multi-table update
            with get_db_cursor(commit=True) as cursor:
                cursor.execute("""
                    UPDATE destination_core
                    SET place_name = %s, locality_city = %s, district = %s, state_ut = %s, category = %s
                    WHERE destination_id = %s
                """, (place_name, locality_city, district, state_ut, category, destination_id))

                # Check if detail record exists, update or insert
                cursor.execute("SELECT destination_id FROM destination_details WHERE destination_id = %s", (destination_id,))
                if cursor.fetchone():
                    cursor.execute("""
                        UPDATE destination_details
                        SET description = %s, best_time_to_visit = %s, how_to_reach = %s,
                            major_attractions = %s, entry_fee_text = %s, opening_hours_text = %s,
                            primary_official_source_url = %s, supporting_source_urls = %s, local_languages = %s
                        WHERE destination_id = %s
                    """, (
                        description, best_time_to_visit, how_to_reach,
                        major_attractions, entry_fee_text, opening_hours_text,
                        primary_official_source_url, supporting_source_urls if supporting_source_urls else None,
                        local_languages, destination_id
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO destination_details (
                            destination_id, description, best_time_to_visit, how_to_reach,
                            major_attractions, entry_fee_text, opening_hours_text,
                            primary_official_source_url, supporting_source_urls, local_languages
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        destination_id, description, best_time_to_visit, how_to_reach,
                        major_attractions, entry_fee_text, opening_hours_text,
                        primary_official_source_url, supporting_source_urls if supporting_source_urls else None,
                        local_languages
                    ))

            flash(f"Destination '{place_name}' successfully updated!", "success")
            return redirect(url_for('destination_detail', destination_id=destination_id))

        return render_template('destinations/form.html', destination=destination, is_edit=True)

    except DatabaseConnectionError as e:
        return render_template('errors/db_unavailable.html', db_message=str(e)), 503


@app.route('/destinations/<int:destination_id>/delete', methods=['POST'])
def destination_delete(destination_id):
    try:
        # Check referential integrity: is destination in any trip plan?
        trip_references = fetch_all("""
            SELECT t.trip_name, s.visit_order
            FROM trip_plan_destinations s
            JOIN trip_plans t ON s.trip_id = t.trip_id
            WHERE s.destination_id = %s
        """, (destination_id,))

        if trip_references:
            trips_str = ", ".join([f"'{r['trip_name']}'" for r in trip_references[:3]])
            flash(
                f"Cannot delete destination: It is currently part of active trip plan(s) ({trips_str}). "
                f"MySQL referential constraint (ON DELETE RESTRICT) prohibits deletion until it is removed from itineraries.",
                "error"
            )
            return redirect(url_for('manage_destinations'))

        # Safe to delete - cascades to details and budget estimates
        dest = fetch_one("SELECT place_name FROM destination_core WHERE destination_id = %s", (destination_id,))
        if dest:
            execute_query("DELETE FROM destination_core WHERE destination_id = %s", (destination_id,))
            flash(f"Destination '{dest['place_name']}' (ID #{destination_id}) was successfully deleted.", "success")

        return redirect(url_for('manage_destinations'))

    except Exception as e:
        flash(f"Error during destination deletion: {e}", "error")
        return redirect(url_for('manage_destinations'))


# ----------------------------------------------------------------------------
# 7. Reports Dashboard
# ----------------------------------------------------------------------------
@app.route('/reports')
def reports_dashboard():
    try:
        # 1. State / UT distribution
        state_counts = fetch_all("""
            SELECT state_ut, COUNT(*) AS dest_count
            FROM destination_core
            GROUP BY state_ut
            ORDER BY dest_count DESC, state_ut ASC
        """)

        # 2. Category counts
        category_counts = fetch_all("""
            SELECT category, COUNT(*) AS cat_count
            FROM destination_core
            GROUP BY category
            ORDER BY cat_count DESC
        """)

        # 3. Budget statistics by starting city
        city_budget_stats = fetch_all("""
            SELECT starting_city,
                   COUNT(*) AS route_count,
                   ROUND(AVG(estimated_total_budget_inr), 2) AS avg_budget,
                   MIN(estimated_total_budget_inr) AS min_budget,
                   MAX(estimated_total_budget_inr) AS max_budget,
                   ROUND(AVG(long_distance_round_trip_cost_inr), 2) AS avg_transit
            FROM budget_estimates
            GROUP BY starting_city
            ORDER BY avg_budget ASC
        """)

        # 4. Subquery: Destinations with above-average budget from New Delhi
        above_avg_routes = fetch_all("""
            SELECT c.place_name, c.state_ut, b.trip_duration_days, b.estimated_total_budget_inr
            FROM budget_estimates b
            INNER JOIN destination_core c ON b.destination_id = c.destination_id
            WHERE b.starting_city = 'New Delhi'
              AND b.estimated_total_budget_inr > (
                  SELECT AVG(estimated_total_budget_inr)
                  FROM budget_estimates
                  WHERE starting_city = 'New Delhi'
              )
            ORDER BY b.estimated_total_budget_inr DESC
            LIMIT 10
        """)

        # 5. Joined destination, visiting logistics, and budget report
        joined_report = fetch_all("""
            SELECT c.place_name, c.state_ut, c.category,
                   d.best_time_to_visit, d.local_languages,
                   b.starting_city, b.estimated_total_budget_inr
            FROM destination_core c
            INNER JOIN destination_details d ON c.destination_id = d.destination_id
            INNER JOIN budget_estimates b ON c.destination_id = b.destination_id
            ORDER BY c.place_name ASC, b.estimated_total_budget_inr ASC
            LIMIT 15
        """)

        return render_template(
            'reports/index.html',
            state_counts=state_counts,
            category_counts=category_counts,
            city_budget_stats=city_budget_stats,
            above_avg_routes=above_avg_routes,
            joined_report=joined_report
        )

    except DatabaseConnectionError as e:
        return render_template('errors/db_unavailable.html', db_message=str(e)), 503


# ----------------------------------------------------------------------------
# Application Entry Point
# ----------------------------------------------------------------------------
if __name__ == '__main__':
    # Local development server on port 5000
    app.run(host='127.0.0.1', port=5000, debug=Config.DEBUG)
