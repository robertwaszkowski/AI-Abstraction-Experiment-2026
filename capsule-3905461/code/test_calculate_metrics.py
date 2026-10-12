import unittest
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import calculate_metrics


class MetricsTests(unittest.TestCase):
    def test_expected_publication_corpus_is_balanced_7_plus_7(self):
        self.assertEqual(
            calculate_metrics.EXPECTED["Code"],
            ["code_01", "code_02", "code_03", "code_04", "code_05", "code_06", "code_07"],
        )
        self.assertEqual(
            calculate_metrics.EXPECTED["Model"],
            ["model_01", "model_02", "model_03", "model_04", "model_05", "model_06", "model_07"],
        )

    def test_matched_team_design_contains_seven_two_person_pairs(self):
        specs = []
        for number in range(1, 8):
            for condition, prefix in (("Code", "code"), ("Model", "model")):
                code_first = number % 2 == 1
                specs.append(
                    calculate_metrics.ExperimentSpec(
                        experiment_id=f"{prefix}_{number:02d}",
                        team_id=f"T{number:02d}",
                        team_size=2,
                        sequence_order="Code -> Model" if code_first else "Model -> Code",
                        condition_position=(
                            1 if (condition == "Code") == code_first else 2
                        ),
                        condition=condition,
                        documented_success=True,
                        technology="test",
                        time_method="reported_total",
                        reported_active_minutes=1.0,
                        turn_method="user_headings",
                    )
                )
        calculate_metrics.validate_matched_team_design(specs)

    def test_matched_team_design_rejects_misaligned_pair(self):
        specs = []
        for number in range(1, 8):
            for condition, prefix in (("Code", "code"), ("Model", "model")):
                team_number = 2 if number == 1 and condition == "Model" else number
                code_first = number % 2 == 1
                specs.append(
                    calculate_metrics.ExperimentSpec(
                        experiment_id=f"{prefix}_{number:02d}",
                        team_id=f"T{team_number:02d}",
                        team_size=2,
                        sequence_order="Code -> Model" if code_first else "Model -> Code",
                        condition_position=(
                            1 if (condition == "Code") == code_first else 2
                        ),
                        condition=condition,
                        documented_success=True,
                        technology="test",
                        time_method="reported_total",
                        reported_active_minutes=1.0,
                        turn_method="user_headings",
                    )
                )
        with self.assertRaises(calculate_metrics.ValidationError):
            calculate_metrics.validate_matched_team_design(specs)

    def test_sessionizer_excludes_breaks_over_thirty_minutes(self):
        start = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
        timestamps = [
            start,
            start + timedelta(minutes=5),
            start + timedelta(minutes=45),
            start + timedelta(minutes=52),
        ]
        self.assertEqual(
            calculate_metrics.sessionized_seconds(timestamps, break_minutes=30), 12 * 60
        )

    def test_primary_threshold_excludes_45_minutes_and_longer_breaks(self):
        start = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
        for seconds, expected in ((44 * 60, 44 * 60), (45 * 60, 0), (45 * 60 + 1, 0)):
            with self.subTest(seconds=seconds):
                self.assertEqual(
                    calculate_metrics.sessionized_seconds(
                        [start, start + timedelta(seconds=seconds)]
                    ),
                    expected,
                )

    def test_docx_clock_rollover_is_monotonic(self):
        values = calculate_metrics.timestamps_from_docx(["23:58", "00:03"])
        self.assertEqual((values[1] - values[0]).total_seconds(), 5 * 60)

    def test_iso_timestamp_normalizes_to_utc(self):
        value = calculate_metrics.parse_iso("2026-04-01T12:00:00+02:00")
        self.assertEqual(value.hour, 10)
        self.assertEqual(value.tzinfo, timezone.utc)

    def test_markdown_timestamp_formats(self):
        values = calculate_metrics.timestamps_from_text(
            [
                "## [Entry] - 2026-07-27 08:05:03 (+02:00)",
                "**AI Response Timestamp**: `2026-07-27T08:10:03+02:00`",
            ]
        )
        self.assertEqual((values[1] - values[0]).total_seconds(), 5 * 60)

    def test_runtime_testing_marker_closes_interval_and_counts_as_work_event(self):
        payload = {
            "exportedAt": "2026-04-02T10:09:00+02:00",
            "conversation": [
                {
                    "role": "user",
                    "content": "Generate the form",
                    "timestamp": "2026-04-02T10:00:00+02:00",
                },
                {
                    "role": "assistant",
                    "content": "Done",
                    "timestamp": "2026-04-02T10:03:00+02:00",
                },
                {
                    "role": "user",
                    "content": calculate_metrics.RUNTIME_TEST_MARKER,
                    "timestamp": "2026-04-02T10:08:00+02:00",
                },
            ]
        }
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / "history.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            (
                timestamps,
                turns,
                markers,
                final_is_marker,
                all_messages_timestamped,
                exported_after_last_message,
                marker_timestamps,
            ) = calculate_metrics.json_conversation(path)
        self.assertEqual((timestamps[-1] - timestamps[0]).total_seconds(), 8 * 60)
        self.assertEqual(turns, 2)
        self.assertEqual(markers, 1)
        self.assertTrue(final_is_marker)
        self.assertTrue(all_messages_timestamped)
        self.assertTrue(exported_after_last_message)
        self.assertEqual(marker_timestamps, [timestamps[-1]])

    def test_sessionizer_supports_threshold_sensitivity(self):
        start = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
        timestamps = [
            start,
            start + timedelta(minutes=20),
            start + timedelta(minutes=65),
        ]
        self.assertEqual(
            calculate_metrics.sessionized_seconds(timestamps, break_minutes=15), 0
        )
        self.assertEqual(
            calculate_metrics.sessionized_seconds(timestamps, break_minutes=30),
            20 * 60,
        )
        self.assertEqual(
            calculate_metrics.sessionized_seconds(timestamps, break_minutes=60),
            65 * 60,
        )

    def test_model_time_uses_one_team_boundary_across_six_histories(self):
        with TemporaryDirectory() as temporary:
            prompt_dir = Path(temporary)
            for number in range(6):
                minute = number * 2
                conversation = [
                    {
                        "role": "user",
                        "content": f"Generate artifact {number}",
                        "timestamp": f"2026-04-02T10:{minute:02d}:00+02:00",
                    },
                    {
                        "role": "assistant",
                        "content": "Done",
                        "timestamp": f"2026-04-02T10:{minute + 1:02d}:00+02:00",
                    },
                ]
                if number == 5:
                    conversation.append(
                        {
                            "role": "user",
                            "content": calculate_metrics.RUNTIME_TEST_MARKER,
                            "timestamp": "2026-04-02T10:20:00+02:00",
                        }
                    )
                payload = {
                    "exportedAt": "2026-04-02T10:21:00+02:00",
                    "conversation": conversation,
                }
                (prompt_dir / f"history-{number}.json").write_text(
                    json.dumps(payload), encoding="utf-8"
                )
            spec = calculate_metrics.ExperimentSpec(
                experiment_id="model_01",
                team_id="T01",
                team_size=2,
                sequence_order="Code -> Model",
                condition_position=2,
                condition="Model",
                documented_success=True,
                technology="test",
                time_method="team_elapsed_to_runtime_test_json",
                reported_active_minutes=None,
                turn_method="json_user_event",
            )
            minutes, turns, files, markers = calculate_metrics.measure_prompts(
                spec, prompt_dir
            )
        self.assertEqual(minutes, 20.0)
        self.assertEqual(turns, 7)
        self.assertEqual(files, 6)
        self.assertEqual(markers, 1)


if __name__ == "__main__":
    unittest.main()
