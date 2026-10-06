import math
import unittest

from wombmodels.state_estimation import prospective_forecast


class ForecastUncertaintyTests(unittest.TestCase):
    def test_equilibrium_point_forecast_has_no_interval_without_covariance(self):
        rows = [{"time": float(i), "power": "wall", "reading": 1.0, "sampled": True}
                for i in range(11)]
        result = prospective_forecast(rows, [], split_time=7.0, noise_sd=0.1)
        self.assertTrue(result["estimable"])
        self.assertFalse(result["state_fit"]["local_parameter_covariance_available"])
        self.assertFalse(result["prediction_interval_available"])
        self.assertIsNone(result["coverage_95"])
        self.assertIsNone(result["mean_95_interval_width"])
        self.assertIsNone(result["uncertainty_method"])
        self.assertIn("covariance", result["prediction_interval_reason"])
        self.assertLess(result["fixture_scale_rmse"], 1e-5)

    def test_excited_analytic_trajectory_retains_approximate_intervals(self):
        rows = []
        state = 2.0
        for i in range(11):
            powered = i not in {3, 4, 5}
            rows.append({"time": float(i), "power": "wall" if powered else "none",
                         "reading": state, "sampled": True})
            state = state * math.exp(-0.5) + (2.0 * (1 - math.exp(-0.5)) if powered else 0.0)
        result = prospective_forecast(rows, [], split_time=7.0, noise_sd=0.1)
        self.assertTrue(result["estimable"])
        self.assertTrue(result["prediction_interval_available"])
        self.assertTrue(result["state_fit"]["local_parameter_covariance_available"])
        self.assertIsNone(result["prediction_interval_reason"])
        self.assertGreater(result["mean_95_interval_width"], 0)
        self.assertEqual(result["coverage_95"], 1.0)
        self.assertLess(result["fixture_scale_rmse"], 1e-5)


if __name__ == "__main__":
    unittest.main()
