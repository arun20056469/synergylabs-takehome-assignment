from __future__ import annotations

import unittest

from problem2_llm_as_judge.src.judge import extract_json
from problem2_llm_as_judge.src.validator import quadratic_weighted_kappa


class JudgePipelineTests(unittest.TestCase):
    def test_fenced_json_parser(self) -> None:
        self.assertEqual(extract_json("```json\n{\"winner\": \"A\"}\n```"), {"winner": "A"})

    def test_embedded_json_parser(self) -> None:
        self.assertEqual(extract_json("Result: {\"winner\": \"B\"} done"), {"winner": "B"})

    def test_kappa_identical(self) -> None:
        self.assertEqual(quadratic_weighted_kappa([1, 2, 5], [1, 2, 5]), 1.0)


if __name__ == "__main__":
    unittest.main()
