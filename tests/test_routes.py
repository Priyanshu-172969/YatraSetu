"""
test_routes.py - Flask Route and Template Integration Tests
Tests HTTP endpoints, error handlers (404, 503 DB unavailable),
CRUD operations, and parameter validation.
"""

import unittest
from unittest.mock import patch, MagicMock
from app import app

class TestFlaskRoutes(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_404_handler(self):
        """Verifies that non-existent routes return 404 and render the 404 error template."""
        response = self.client.get('/non-existent-destination-route')
        self.assertEqual(response.status_code, 404)
        self.assertIn(b"404", response.data)
        self.assertIn(b"Destination Not Found", response.data)

    def test_db_unavailable_graceful_handling(self):
        """Verifies that when MySQL is unreachable, app renders db_unavailable.html with 503 status."""
        with patch('app.check_db_connection', return_value=(False, "Connection to 127.0.0.1:3306 refused")):
            response = self.client.get('/')
            self.assertEqual(response.status_code, 503)
            self.assertIn(b"MySQL Database Connection Needed", response.data)
            self.assertIn(b"127.0.0.1:3306", response.data)

    def test_home_route_with_mocked_db(self):
        """Verifies that the home page renders stats and highlights correctly when DB returns data."""
        mock_stats_dest = {'c': 30}
        mock_stats_states = {'c': 18}
        mock_stats_cats = {'c': 6}
        mock_stats_budgets = {'c': 90}
        mock_highlights = [
            {
                'destination_id': 1,
                'place_name': 'Taj Mahal',
                'locality_city': 'Agra',
                'state_ut': 'Uttar Pradesh',
                'category': 'Heritage',
                'description': 'Iconic white marble mausoleum built by Mughal emperor Shah Jahan.'
            }
        ]

        def mock_fetch_one(query, params=None):
            if "destination_core" in query and "category" in query:
                return mock_stats_cats
            elif "destination_core" in query and "state_ut" in query:
                return mock_stats_states
            elif "destination_core" in query:
                return mock_stats_dest
            elif "budget_estimates" in query:
                return mock_stats_budgets
            return {'c': 0}

        with patch('app.check_db_connection', return_value=(True, "Connected")):
            with patch('app.fetch_one', side_effect=mock_fetch_one):
                with patch('app.fetch_all', return_value=mock_highlights):
                    response = self.client.get('/')
                    self.assertEqual(response.status_code, 200)
                    self.assertIn(b"YatraSetu", response.data)
                    self.assertIn(b"Taj Mahal", response.data)
                    self.assertIn(b"Uttar Pradesh", response.data)

    def test_destination_explorer_route_with_mocked_db(self):
        """Verifies destination explorer rendering, filters, and pagination parameters."""
        mock_destinations = [
            {
                'destination_id': 1,
                'place_name': 'Taj Mahal',
                'locality_city': 'Agra',
                'district': 'Agra',
                'state_ut': 'Uttar Pradesh',
                'category': 'Heritage',
                'description': 'Iconic mausoleum.'
            }
        ]
        mock_states = [{'state_ut': 'Uttar Pradesh'}, {'state_ut': 'Rajasthan'}]
        mock_cats = [{'category': 'Heritage'}, {'category': 'Wildlife'}]

        def mock_fetch_all(query, params=None):
            if "DISTINCT state_ut" in query:
                return mock_states
            if "DISTINCT category" in query:
                return mock_cats
            return mock_destinations

        with patch('app.fetch_all', side_effect=mock_fetch_all):
            with patch('app.fetch_one', return_value={'total': 1}):
                response = self.client.get('/destinations?q=Taj&state=Uttar+Pradesh')
                self.assertEqual(response.status_code, 200)
                self.assertIn(b"Destination Explorer", response.data)
                self.assertIn(b"Taj Mahal", response.data)

    def test_destination_detail_route_with_mocked_db(self):
        """Verifies destination detail page renders comprehensive information."""
        mock_dest = {
            'destination_id': 1,
            'place_name': 'Taj Mahal',
            'locality_city': 'Agra',
            'district': 'Agra',
            'state_ut': 'Uttar Pradesh',
            'category': 'Heritage',
            'description': 'Mughal masterpiece.',
            'best_time_to_visit': 'October to March',
            'how_to_reach': 'Nearest airport Agra / Delhi',
            'major_attractions': 'Main mausoleum, gardens, Yamuna riverfront',
            'entry_fee_text': 'INR 50 for Indians',
            'opening_hours_text': 'Sunrise to Sunset',
            'primary_official_source_url': 'https://www.tajmahal.gov.in',
            'supporting_source_urls': 'https://asi.nic.in',
            'local_languages': 'Hindi, Urdu, English'
        }
        with patch('app.fetch_one', return_value=mock_dest):
            with patch('app.fetch_all', return_value=[]):
                response = self.client.get('/destinations/1')
                self.assertEqual(response.status_code, 200)
                self.assertIn(b"Taj Mahal", response.data)
                self.assertIn(b"Mughal masterpiece", response.data)
                self.assertIn(b"https://www.tajmahal.gov.in", response.data)

    def test_budget_compare_route_with_mocked_db(self):
        """Verifies budget comparison route renders and lists estimates when destination selected."""
        mock_dest = {'destination_id': 1, 'place_name': 'Taj Mahal', 'locality_city': 'Agra', 'state_ut': 'Uttar Pradesh', 'category': 'Heritage'}
        mock_estimates = [
            {
                'budget_id': 1,
                'destination_id': 1,
                'starting_city': 'New Delhi',
                'trip_duration_days': 1,
                'accommodation_nights': 0,
                'transport_mode': 'Train',
                'transport_class': 'Chair Car',
                'target_travel_period': 'Winter',
                'long_distance_round_trip_cost_inr': 600.0,
                'onward_transport_cost_inr': 100.0,
                'local_transport_cost_inr': 300.0,
                'accommodation_cost_inr': 0.0,
                'food_and_water_cost_inr': 400.0,
                'entry_and_mandatory_fees_inr': 50.0,
                'other_essential_cost_inr': 50.0,
                'contingency_cost_inr': 100.0,
                'estimated_total_budget_inr': 1600.0,
                'calculation_methodology': 'Day trip rail formula',
                'confidence_level': 'Prototype',
                'date_checked': '2026-10-25',
                'data_status': 'Verified',
                'limitations': 'Fares may vary'
            }
        ]

        with patch('app.fetch_all', side_effect=lambda q, p=None: [mock_dest] if "ORDER BY place_name" in q else mock_estimates):
            with patch('app.fetch_one', return_value=mock_dest):
                response = self.client.get('/budgets?destination_id=1')
                self.assertEqual(response.status_code, 200)
                self.assertIn(b"Budget Comparison Explorer", response.data)
                self.assertIn(b"New Delhi", response.data)
                self.assertIn(b"1,600.00", response.data)

    def test_trip_create_validation(self):
        """Verifies server-side validation rejects empty trip names."""
        response = self.client.post('/trips/create', data={
            'trip_name': '',
            'starting_city': 'New Delhi',
            'planned_duration_days': '5'
        }, follow_redirects=True)
        self.assertIn(b"Trip name and starting city are required", response.data)

    def test_reports_dashboard_rendering(self):
        """Verifies SQL reports page renders queries output properly."""
        with patch('app.fetch_all', return_value=[]):
            response = self.client.get('/reports')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"SQL Analytics & Reports Dashboard", response.data)
            self.assertIn(b"State Distribution", response.data)
            self.assertIn(b"Category Counts", response.data)

if __name__ == '__main__':
    unittest.main()
