import json
import os
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PortfolioContractTests(unittest.TestCase):
    def test_public_page_uses_truthful_identity_and_prototype_language(self):
        html = (ROOT / "web" / "index.html").read_text()
        self.assertIn("practicing physician and AI-assisted product builder", html)
        self.assertIn("Portfolio prototype", html)
        self.assertIn("fictional", html)
        self.assertNotIn("physician and engineer", html)
        self.assertNotIn("left clinical practice", html)

    def test_public_model_execution_is_not_exposed_in_the_interface(self):
        html = (ROOT / "web" / "index.html").read_text()
        self.assertIn("Public model calls disabled", html)
        self.assertNotIn('onclick="runLiveAI()"', html)

    def test_only_reviewed_case_is_public(self):
        cases = sorted((ROOT / "web" / "cases").glob("*.json"))
        self.assertEqual([path.name for path in cases], ["case1.json"])
        case = json.loads(cases[0].read_text())
        for stage in ("triage", "context", "plan", "note"):
            self.assertIn("SYNTHETIC DEMO", case["stages"][stage])
            self.assertIn("CLINICIAN VERIFICATION", case["stages"][stage])

    def test_public_ai_defaults_to_disabled(self):
        self.assertNotIn(
            os.environ.get("ENABLE_PUBLIC_AI", "").lower(),
            {"1", "true", "yes"},
        )

    def test_readme_states_implementation_boundaries(self):
        readme = (ROOT / "README.md").read_text()
        for statement in (
            "What is live, simulated, and experimental",
            "not connected to a production EHR",
            "disabled by default on the public deployment",
            "Clinical validation | Not completed",
            "No real patient data is included",
        ):
            self.assertIn(statement, readme)


if __name__ == "__main__":
    unittest.main()
