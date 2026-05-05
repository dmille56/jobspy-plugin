from pathlib import Path
import unittest


class JobspySkillDocTest(unittest.TestCase):
    def test_search_result_format_mentions_default_columns_sorting_and_age(self):
        skill = Path(__file__).resolve().parents[1] / "skills" / "jobspy" / "SKILL.md"
        text = skill.read_text(encoding="utf-8")

        self.assertIn("### Result display", text)
        self.assertIn("`title`, `company`, `salary`, `fit`, `age`, `url`", text)
        self.assertIn("human-readable posting age derived from `date_posted`", text)
        self.assertIn("sorted by fit score descending, then recency breaking ties", text)


if __name__ == "__main__":
    unittest.main()
