import os
import re
import unittest
from unittest.mock import patch

from simple_openai.models import open_ai_models
from simple_openai.usage import estimate_sol_short_context_usd, format_responses_usage

_ANSI = re.compile(r"\033\[[0-9;]*m")


def _plain(text: str) -> str:
    return _ANSI.sub("", text)


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


class UsageFormatTests(unittest.TestCase):
    def test_each_statistic_is_on_its_own_line_and_values_are_right_aligned(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("NO_COLOR", None)
            block = format_responses_usage(
                model="gpt-5.6-sol",
                chat_id="default",
                input_tokens=75,
                cached_tokens=0,
                output_tokens=1186,
                reasoning_tokens=1024,
                estimated_cost_usd=0.02402,
            )
        lines = _plain(block).splitlines()
        self.assertEqual(lines[0], "OpenAI usage")
        data_lines = [line for line in lines if line.startswith("  ") and "rates" not in line]
        self.assertEqual(len(data_lines), 7)
        self.assertTrue(any("chat_id" in line and "default" in line for line in data_lines))
        self.assertTrue(any("estimated cost" in line and "$0.024020" in line for line in data_lines))
        self.assertEqual(len({len(line.rstrip()) for line in data_lines}), 1)
        self.assertIn("\033[", block)

    def test_no_color_disables_ansi(self) -> None:
        with patch.dict(os.environ, {"NO_COLOR": "1"}, clear=False):
            block = format_responses_usage(
                model="gpt-5.6-sol",
                chat_id="Group 1",
                input_tokens=10,
                cached_tokens=2,
                output_tokens=20,
                reasoning_tokens=5,
                estimated_cost_usd=0.0004,
            )
        self.assertNotIn("\033[", block)
        self.assertIn("chat_id", block)
        self.assertIn("Group 1", block)

    def test_missing_usage_is_flagged_on_its_own_line(self) -> None:
        block = format_responses_usage(model="gpt-5.6-sol", chat_id="default")
        lines = _plain(block).splitlines()
        self.assertTrue(any(line.strip().endswith("missing") for line in lines))
        self.assertFalse(any("estimated cost" in line for line in lines))


if __name__ == "__main__":
    unittest.main()
