import os
import unittest

from backend.app.core.config import get_settings


class SettingsTests(unittest.TestCase):
    def setUp(self):
        get_settings.cache_clear()

    def tearDown(self):
        get_settings.cache_clear()

    def test_amd_epyc_defaults(self):
        os.environ.pop("COMPUTE_CPU_VENDOR", None)
        os.environ.pop("COMPUTE_CPU_FAMILY", None)
        os.environ.pop("COMPUTE_OPTIMIZED", None)

        settings = get_settings()

        self.assertEqual(settings.compute_cpu_vendor, "AMD")
        self.assertEqual(settings.compute_cpu_family, "EPYC")
        self.assertTrue(settings.compute_optimized)

    def test_optimization_flag_parsing(self):
        os.environ["COMPUTE_OPTIMIZED"] = "no"
        settings = get_settings()
        self.assertFalse(settings.compute_optimized)


if __name__ == "__main__":
    unittest.main()
