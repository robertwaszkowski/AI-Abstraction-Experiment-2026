import unittest
from pathlib import Path

import phase2_analysis


class Phase2AnalysisTests(unittest.TestCase):
    def test_model_artifacts_are_primary_application_models(self):
        category, _ = phase2_analysis.classify_artifact(
            "Model", Path("Leave Request.bpmn")
        )
        self.assertEqual(category, "application_implementation_or_model")
        self.assertIn(category, phase2_analysis.PRIMARY_CATEGORIES)

    def test_dependency_metadata_is_outside_primary_footprint(self):
        category, _ = phase2_analysis.classify_artifact(
            "Code", Path("web/package-lock.json")
        )
        self.assertEqual(
            category, "project_configuration_and_dependency_metadata"
        )
        self.assertNotIn(category, phase2_analysis.PRIMARY_CATEGORIES)

    def test_tests_are_visible_and_in_primary_footprint(self):
        category, _ = phase2_analysis.classify_artifact(
            "Code", Path("backend/test_scenario.py")
        )
        self.assertEqual(category, "application_tests")
        self.assertIn(category, phase2_analysis.PRIMARY_CATEGORIES)

    def test_maximum_sensitivity_removes_whole_team_pairs(self):
        pairs = []
        for number in range(1, 8):
            pairs.append(
                {
                    "team_id": f"T{number:02d}",
                    "code_source_observed_minutes": 100 + number,
                    "model_source_observed_minutes": 10 + number,
                    "code_recorded_interaction_events": 20 + number,
                    "model_recorded_interaction_events": 5 + number,
                }
            )
        rows = phase2_analysis.maximum_sensitivity(pairs)
        union = [
            row
            for row in rows
            if row["measure"] == "source_observed_minutes"
            and row["scenario"] == "exclude_union_of_condition_maximum_teams"
        ][0]
        self.assertEqual(union["excluded_teams"], "T07")
        self.assertEqual(union["n_pairs"], 6)


if __name__ == "__main__":
    unittest.main()
