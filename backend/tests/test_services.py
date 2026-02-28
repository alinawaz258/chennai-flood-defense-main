import unittest

from backend.app.models.schemas import EmergencyUnit
from backend.app.services.system_service import FloodDefenseService


class FloodDefenseServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = FloodDefenseService()

    def test_forecast_has_7_days(self):
        df = self.service.forecast()
        self.assertGreaterEqual(len(df), 7)
        self.assertIn('predicted_rainfall', df.columns)

    def test_zone_risk_schema(self):
        zones = self.service.zone_risk()
        expected = {'zone_id', 'predicted_rainfall', 'flood_probability', 'risk_level', 'estimated_water_depth'}
        self.assertTrue(expected.issubset(set(zones.columns)))

    def test_route_returns_algorithm(self):
        route, _, _ = self.service.route('T_Nagar', 'Adyar')
        self.assertIn(route['algorithm'], {'astar', 'dijkstra', 'none'})

    def test_simulation_runs(self):
        units = [EmergencyUnit(unit_id='E1', current_zone='Guindy', speed_kmph=35)]
        multiplier, zones, blocked, dispatch, route, clearance = self.service.simulate(25, 'T_Nagar', 'Adyar', units)
        self.assertGreater(multiplier, 1.0)
        self.assertGreater(len(zones), 0)
        self.assertIsInstance(blocked, list)
        self.assertIsInstance(dispatch, list)
        self.assertIsNotNone(route)
        self.assertIsInstance(clearance, list)


if __name__ == '__main__':
    unittest.main()
