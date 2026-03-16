import unittest

from backend.app.models.schemas import CitizenReportRequest, DamageEstimateRequest, TrafficRerouteRequest
from backend.app.models.sensor_schema import SensorUpdate
from backend.app.services.deep_flood_model import DeepFloodModelService, build_synthetic_training_data
from backend.main import damage_estimate, sensor_update, submit_report, traffic_reroute


class NewEndpointFunctionTests(unittest.TestCase):
    def test_sensor_update_function(self):
        response = sensor_update(
            [
                SensorUpdate(
                    sensor_id="wl-001",
                    sensor_type="water_level",
                    zone_id="Adyar",
                    value=32.5,
                    unit="cm",
                    timestamp="2026-01-01T00:00:00Z",
                )
            ]
        )
        self.assertEqual(response.status, "processed")
        self.assertGreaterEqual(response.records_ingested, 1)

    def test_report_function(self):
        request = CitizenReportRequest(location="Adyar", water_depth=35.0, photo_url="https://x/y.jpg", road_blocked=True)
        response = submit_report(request)
        self.assertEqual(response.status, "stored")
        self.assertEqual(response.report["location"], "Adyar")

    def test_damage_estimate_function(self):
        response = damage_estimate(DamageEstimateRequest(flood_depth=55, population=12000, infrastructure_density=8.2))
        self.assertGreater(response.estimated_economic_loss_inr, 0)

    def test_traffic_reroute_function(self):
        response = traffic_reroute(TrafficRerouteRequest(source="T_Nagar", destination="Guindy", algorithm="astar"))
        self.assertIn("algorithm", response.model_dump())


class DeepFloodModelTests(unittest.TestCase):
    def test_deep_model_train_and_predict(self):
        train_df = build_synthetic_training_data(64)
        svc = DeepFloodModelService()
        svc.train_model(train_df, epochs=1)
        zone_df = train_df.head(5).copy()
        zone_df["zone_id"] = [f"Z{i}" for i in range(5)]
        preds = svc.predict_zone_risk(zone_df)
        self.assertEqual(len(preds), 5)
        self.assertIn("flood_probability", preds.columns)


if __name__ == "__main__":
    unittest.main()
