import unittest

from simple_openai.models import open_ai_models
from simple_openai.usage import estimate_sol_short_context_usd


class UsageEstimateTests(unittest.TestCase):
    def test_sol_short_context_estimate_matches_the_design_fixture(self) -> None:
        # input 75, cached 0, output 1186 (includes 1024 reasoning)
        self.assertAlmostEqual(
            estimate_sol_short_context_usd(75, 0, 1186),
            0.02402,
            places=6,
        )

    def test_cached_input_uses_the_discounted_rate(self) -> None:
        self.assertAlmostEqual(
            estimate_sol_short_context_usd(1000, 800, 100),
            0.00312,
            places=6,
        )

    def test_usage_object_exposes_cached_and_reasoning_tokens(self) -> None:
        usage = open_ai_models.ResponsesUsage.model_validate(
            {
                "input_tokens": 75,
                "input_tokens_details": {"cached_tokens": 10},
                "output_tokens": 1186,
                "output_tokens_details": {"reasoning_tokens": 1024},
                "total_tokens": 1261,
            }
        )

        self.assertEqual(usage.cached_tokens, 10)
        self.assertEqual(usage.reasoning_tokens, 1024)


if __name__ == "__main__":
    unittest.main()
