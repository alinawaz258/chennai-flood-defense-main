import unittest

from backend.main import healthcheck


class ApiTests(unittest.TestCase):
    def test_health_includes_compute_profile(self):
        payload = healthcheck()

        self.assertEqual(payload.status, "ok")
        self.assertIn("EPYC", payload.compute_profile)


if __name__ == "__main__":
    unittest.main()
