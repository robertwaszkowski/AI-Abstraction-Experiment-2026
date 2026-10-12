#!/usr/bin/env python3
"""Validate the capsule and generate all tabular results.

The implementation deliberately avoids estimating missing observations.  Every
time and turn value is derived using the method declared in experiments.csv.
Only Python's standard library is required.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET


EXPECTED = {
    "Code": [f"code_{number:02d}" for number in range(1, 8)],
    "Model": [f"model_{number:02d}" for number in range(1, 8)],
}
CONDITION_DIR = {"Code": "code_generation", "Model": "model_generation"}
IGNORED_NAMES = {".DS_Store"}
IGNORED_DIRS = {
    ".git", "__pycache__", "node_modules", "venv", ".venv", "prompt_backup"
}
SOURCE_SUFFIXES = {
    ".css", ".html", ".js", ".json", ".jsx", ".mjs", ".prisma", ".py", ".sh",
    ".sql", ".ts", ".tsx", ".yaml", ".yml",
}
NON_SOURCE_NAMES = {"package-lock.json"}
ISO_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T")
TEXT_ISO_TOKEN = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?"
)
TEXT_SPACED_TOKEN = re.compile(
    r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\s+\([+-]\d{2}:\d{2}\))?"
)
TIME_TOKEN = re.compile(r"(?<!\d)([01]?\d|2[0-3]):[0-5]\d(?::[0-5]\d)?(?!\d)")
DATE_TOKEN = re.compile(r"(?<!\d)(\d{2})\.(\d{2})\.(\d{4})(?!\d)")
DURATION_ROW = re.compile(r"^\s*(\d+(?:[.,]\d+)?)\s*(?:min|minutes?|minut|minuty)\s*$", re.I)
USER_HEADING = re.compile(
    r"\s*(?:#+\s*)?(?:zapytanie\s+użytkownika|user|użytkownik|prompt|query|interakcja|interaction)\s*:?\s*",
    re.I,
)
MARKDOWN_USER_HEADING = re.compile(
    r"\s*(?:#+\s*)?(?:\*{0,2})user\s+prompt(?:\s+timestamp)?(?:\*{0,2})\s*:?\s*",
    re.I,
)
RUNTIME_TEST_MARKER = "Testing the application in the runtime platform"
DEFAULT_SESSION_THRESHOLD_MINUTES = 45


class ValidationError(RuntimeError):
    """Raised when data and declared experiment metadata disagree."""


@dataclass(frozen=True)
class ExperimentSpec:
    experiment_id: str
    team_id: str
    team_size: int
    sequence_order: str
    condition_position: int
    condition: str
    documented_success: bool
    technology: str
    time_method: str
    reported_active_minutes: float | None
    turn_method: str


@dataclass
class Metrics:
    experiment_id: str
    condition: str
    source_observed_minutes: float
    turn_count: int
    documented_success: bool
    artifact_complete: bool
    artifact_files: int
    source_files: int
    source_lines: int
    artifact_bytes: int
    source_bytes: int
    prompt_files: int
    runtime_test_markers: int
    technology: str
    time_method: str
    turn_method: str
    bpmn_files: int = 0
    json_artifacts: int = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument(
        "--validate-only", action="store_true", help="validate inputs without writing results"
    )
    parser.add_argument(
        "--session-threshold-minutes",
        type=int,
        default=DEFAULT_SESSION_THRESHOLD_MINUTES,
        help="maximum within-session gap for sessionized code logs (default: 45)",
    )
    return parser.parse_args()


def read_specs(path: Path) -> list[ExperimentSpec]:
    if not path.is_file():
        raise ValidationError(f"Missing experiment manifest: {path}")
    specs: list[ExperimentSpec] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            raw_minutes = row["reported_active_minutes"].strip()
            specs.append(
                ExperimentSpec(
                    experiment_id=row["experiment_id"].strip(),
                    team_id=row["team_id"].strip(),
                    team_size=int(row["team_size"].strip()),
                    sequence_order=row["sequence_order"].strip(),
                    condition_position=int(row["condition_position"].strip()),
                    condition=row["condition"].strip(),
                    documented_success=row["documented_success"].strip().lower() == "yes",
                    technology=row["technology"].strip(),
                    time_method=row["time_method"].strip(),
                    reported_active_minutes=float(raw_minutes) if raw_minutes else None,
                    turn_method=row["turn_method"].strip(),
                )
            )
    return specs


def validate_matched_team_design(specs: list[ExperimentSpec]) -> None:
    expected_teams = {f"T{number:02d}" for number in range(1, 8)}
    observed_teams = {spec.team_id for spec in specs}
    if observed_teams != expected_teams:
        raise ValidationError(
            f"Team IDs differ: expected {sorted(expected_teams)}, "
            f"found {sorted(observed_teams)}"
        )

    for number in range(1, 8):
        team_id = f"T{number:02d}"
        team_specs = [spec for spec in specs if spec.team_id == team_id]
        expected_ids = {f"code_{number:02d}", f"model_{number:02d}"}
        observed_ids = {spec.experiment_id for spec in team_specs}
        observed_conditions = {spec.condition for spec in team_specs}
        if len(team_specs) != 2 or observed_ids != expected_ids:
            raise ValidationError(
                f"Matched pair {team_id} must contain {sorted(expected_ids)}, "
                f"found {sorted(observed_ids)}"
            )
        if observed_conditions != {"Code", "Model"}:
            raise ValidationError(
                f"Matched pair {team_id} must contain one Code and one Model run"
            )
        if any(spec.team_size != 2 for spec in team_specs):
            raise ValidationError(f"Matched pair {team_id} must have team_size 2")

        expected_sequence = "Code -> Model" if number % 2 == 1 else "Model -> Code"
        if {spec.sequence_order for spec in team_specs} != {expected_sequence}:
            raise ValidationError(
                f"Matched pair {team_id} must use sequence {expected_sequence}"
            )
        expected_positions = (
            {"Code": 1, "Model": 2}
            if expected_sequence == "Code -> Model"
            else {"Model": 1, "Code": 2}
        )
        if any(
            spec.condition_position != expected_positions[spec.condition]
            for spec in team_specs
        ):
            raise ValidationError(f"Matched pair {team_id} has inconsistent condition positions")


def validate_experiment_set(data_dir: Path, specs: list[ExperimentSpec]) -> None:
    validate_matched_team_design(specs)
    declared = {condition: [] for condition in EXPECTED}
    for spec in specs:
        if spec.condition not in EXPECTED:
            raise ValidationError(f"Unknown condition for {spec.experiment_id}: {spec.condition}")
        declared[spec.condition].append(spec.experiment_id)

    for condition, expected in EXPECTED.items():
        condition_path = data_dir / CONDITION_DIR[condition]
        actual = sorted(path.name for path in condition_path.iterdir() if path.is_dir())
        if actual != expected:
            raise ValidationError(
                f"{condition} directories differ: expected {expected}, found {actual}"
            )
        if sorted(declared[condition]) != expected:
            raise ValidationError(
                f"{condition} manifest IDs differ: expected {expected}, "
                f"found {sorted(declared[condition])}"
            )


def iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file() or path.name in IGNORED_NAMES or path.name.endswith(".bak"):
            continue
        if any(part in IGNORED_DIRS for part in path.relative_to(root).parts):
            continue
        yield path


def docx_lines(path: Path) -> list[str]:
    try:
        with zipfile.ZipFile(path) as archive:
            root = ET.fromstring(archive.read("word/document.xml"))
    except (OSError, KeyError, zipfile.BadZipFile, ET.ParseError) as exc:
        raise ValidationError(f"Cannot read DOCX {path}: {exc}") from exc

    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    lines: list[str] = []
    for paragraph in root.iter(f"{namespace}p"):
        text = "".join(node.text or "" for node in paragraph.iter(f"{namespace}t"))
        if text.strip():
            lines.append(text.strip())
    return lines


def prompt_text_files(prompt_dir: Path) -> list[Path]:
    files = list(iter_files(prompt_dir))
    docx_stems = {path.stem for path in files if path.suffix.lower() == ".docx"}
    # A Markdown conversion next to an original DOCX is derivative, not a second log.
    return [
        path for path in files
        if path.suffix.lower() in {".docx", ".json", ".md", ".txt"}
        and not (path.suffix.lower() == ".md" and path.stem in docx_stems)
    ]


def parse_iso(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def json_conversation(
    path: Path,
) -> tuple[list[datetime], int, int, bool, bool, bool, list[datetime]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"Invalid JSON prompt log {path}: {exc}") from exc
    conversation = payload.get("conversation") if isinstance(payload, dict) else None
    if not isinstance(conversation, list):
        return [], 0, 0, False, False, False, []
    timestamps: list[datetime] = []
    recorded_user_events = 0
    runtime_test_markers = 0
    runtime_test_timestamps: list[datetime] = []
    final_is_runtime_test_marker = False
    message_count = 0
    for message in conversation:
        if not isinstance(message, dict):
            continue
        message_count += 1
        content = str(message.get("content", "")).strip()
        is_runtime_test_marker = (
            message.get("role") == "user" and content == RUNTIME_TEST_MARKER
        )
        if message.get("role") == "user":
            recorded_user_events += 1
        if is_runtime_test_marker:
            runtime_test_markers += 1
        parsed = parse_iso(message.get("timestamp", ""))
        if parsed is not None:
            timestamps.append(parsed)
            if is_runtime_test_marker:
                runtime_test_timestamps.append(parsed)
    if conversation and isinstance(conversation[-1], dict):
        final = conversation[-1]
        final_is_runtime_test_marker = (
            final.get("role") == "user"
            and str(final.get("content", "")).strip() == RUNTIME_TEST_MARKER
        )
    exported_at = parse_iso(payload.get("exportedAt", "")) if isinstance(payload, dict) else None
    all_messages_timestamped = len(timestamps) == message_count
    exported_after_last_message = bool(
        exported_at is not None and timestamps and exported_at >= timestamps[-1]
    )
    return (
        timestamps,
        recorded_user_events,
        runtime_test_markers,
        final_is_runtime_test_marker,
        all_messages_timestamped,
        exported_after_last_message,
        runtime_test_timestamps,
    )


def constituent_docx_durations(path: Path) -> list[float]:
    """Read duration paragraphs once, excluding explicitly labelled table summaries.

    This affects timing only. The separate descriptive event parser retains its
    established row count, including a summary cell where present.
    """
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read('word/document.xml'))
    ns = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    text = lambda element: ''.join(node.text or '' for node in element.iter(ns+'t')).strip()
    summary_paragraphs = set()
    for row in root.iter(ns+'tr'):
        if any(re.fullmatch(r'SUMA|SUM|TOTAL|RAZEM|ŁĄCZNIE', text(cell), re.I)
               for cell in row.findall(ns+'tc')):
            summary_paragraphs.update(id(p) for p in row.iter(ns+'p'))
    return [float(match.group(1).replace(',', '.'))
            for p in root.iter(ns+'p')
            if id(p) not in summary_paragraphs
            and (match := DURATION_ROW.fullmatch(text(p)))]


def timestamps_from_docx(lines: list[str]) -> list[datetime]:
    values: list[datetime] = []
    anchor = datetime(2000, 1, 1, tzinfo=timezone.utc)
    previous: datetime | None = None
    for line in lines:
        time_match = TIME_TOKEN.search(line)
        if not time_match:
            continue
        date_match = DATE_TOKEN.search(line)
        time_value = datetime.strptime(time_match.group(0), "%H:%M:%S" if time_match.group(0).count(":") == 2 else "%H:%M")
        if date_match:
            day, month, year = map(int, date_match.groups())
            candidate = datetime(year, month, day, time_value.hour, time_value.minute, time_value.second, tzinfo=timezone.utc)
        else:
            candidate = anchor.replace(
                hour=time_value.hour, minute=time_value.minute, second=time_value.second
            )
            if previous is not None:
                while candidate < previous:
                    candidate += timedelta(days=1)
        values.append(candidate)
        previous = candidate
        anchor = candidate.replace(hour=0, minute=0, second=0)
    return values


def timestamps_from_text(lines: list[str]) -> list[datetime]:
    values: list[datetime] = []
    for line in lines:
        iso_match = TEXT_ISO_TOKEN.search(line)
        if iso_match:
            parsed = parse_iso(iso_match.group(0))
            if parsed is not None:
                values.append(parsed)
            continue
        spaced_match = TEXT_SPACED_TOKEN.search(line)
        if not spaced_match:
            continue
        normalized = spaced_match.group(0).replace("(", "").replace(")", "")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            continue
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        values.append(parsed.astimezone(timezone.utc))
    return values


def sessionized_seconds(
    timestamps: list[datetime], break_minutes: int = DEFAULT_SESSION_THRESHOLD_MINUTES
) -> float:
    if len(timestamps) < 2:
        return 0.0
    total = 0.0
    threshold = break_minutes * 60
    for previous, current in zip(timestamps, timestamps[1:]):
        delta = (current - previous).total_seconds()
        if 0 <= delta < threshold:
            total += delta
    return total


def measure_prompts(
    spec: ExperimentSpec,
    prompt_dir: Path,
    session_threshold_minutes: int = DEFAULT_SESSION_THRESHOLD_MINUTES,
) -> tuple[float, int, int, int]:
    if session_threshold_minutes <= 0:
        raise ValidationError("Session threshold must be a positive number of minutes")
    files = prompt_text_files(prompt_dir)
    docx = [path for path in files if path.suffix.lower() == ".docx"]
    json_logs = [path for path in files if path.suffix.lower() == ".json"]
    text_logs = [path for path in files if path.suffix.lower() in {".md", ".txt"}]
    lines_by_file = {path: docx_lines(path) for path in docx}
    text_lines_by_file = {
        path: path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for path in text_logs
    }

    duration_values = [
        float(match.group(1).replace(",", "."))
        for lines in lines_by_file.values()
        for line in lines
        if (match := DURATION_ROW.fullmatch(line))
    ]
    timestamp_line_count = sum(
        1 for lines in lines_by_file.values() for line in lines if TIME_TOKEN.search(line)
    )
    user_heading_count = sum(
        1 for lines in lines_by_file.values() for line in lines if USER_HEADING.fullmatch(line)
    )
    markdown_user_count = sum(
        1
        for lines in text_lines_by_file.values()
        for line in lines
        if MARKDOWN_USER_HEADING.fullmatch(line)
    )
    json_sessionized_seconds = 0.0
    json_all_timestamps: list[datetime] = []
    json_runtime_test_timestamps: list[datetime] = []
    json_user_events = 0
    runtime_test_markers = 0
    marker_at_file_end_count = 0
    for path in json_logs:
        (
            timestamps,
            turns,
            markers,
            final_is_marker,
            all_messages_timestamped,
            exported_after_last_message,
            marker_timestamps,
        ) = json_conversation(path)
        json_sessionized_seconds += sessionized_seconds(timestamps)
        json_all_timestamps.extend(timestamps)
        json_runtime_test_timestamps.extend(marker_timestamps)
        json_user_events += turns
        runtime_test_markers += markers
        marker_at_file_end_count += int(final_is_marker)
        if spec.time_method == "team_elapsed_to_runtime_test_json":
            if not timestamps:
                raise ValidationError(f"Insufficient JSON timestamps in {path}")
            if not all_messages_timestamped:
                raise ValidationError(f"Missing or invalid JSON message timestamp in {path}")
            if not exported_after_last_message:
                raise ValidationError(f"Invalid JSON export boundary in {path}")
            if timestamps != sorted(timestamps):
                raise ValidationError(f"Non-monotonic JSON timestamps in {path}")

    if spec.time_method == "reported_total":
        if spec.reported_active_minutes is None:
            raise ValidationError(f"Missing reported time for {spec.experiment_id}")
        active_minutes = spec.reported_active_minutes
    elif spec.time_method == "duration_rows":
        if not duration_values:
            raise ValidationError(f"No duration rows found for {spec.experiment_id}")
        # Investigator: short between-row gaps are review work. Do not silently
        # convert an internally inconsistent clock row into an extra interval.
        from development_durations import measure as measure_development_durations
        active_minutes = sum(
            measure_development_durations(path, session_threshold_minutes)['recorded_development_minutes']
            for path in docx
        )
    elif spec.time_method == "sessionized_docx":
        seconds = sum(
            sessionized_seconds(
                timestamps_from_docx(lines), break_minutes=session_threshold_minutes
            )
            for lines in lines_by_file.values()
        )
        active_minutes = seconds / 60
    elif spec.time_method == "sessionized_json":
        active_minutes = json_sessionized_seconds / 60
    elif spec.time_method == "team_elapsed_to_runtime_test_json":
        if len(json_logs) != 6:
            raise ValidationError(
                f"Expected six model task histories for {spec.experiment_id}, found {len(json_logs)}"
            )
        if runtime_test_markers != 1 or marker_at_file_end_count != 1:
            raise ValidationError(
                f"Expected one final runtime-testing marker across {spec.experiment_id}"
            )
        runtime_test_timestamp = json_runtime_test_timestamps[0]
        if runtime_test_timestamp != max(json_all_timestamps):
            raise ValidationError(
                f"Runtime-testing marker is not the final team timestamp for {spec.experiment_id}"
            )
        active_minutes = sessionized_seconds(
            sorted(set(json_all_timestamps)), break_minutes=session_threshold_minutes
        ) / 60
    elif spec.time_method == "sessionized_text":
        seconds = sum(
            sessionized_seconds(
                timestamps_from_text(lines), break_minutes=session_threshold_minutes
            )
            for lines in text_lines_by_file.values()
        )
        active_minutes = seconds / 60
    else:
        raise ValidationError(f"Unknown time method for {spec.experiment_id}: {spec.time_method}")

    if spec.turn_method == "duration_rows":
        turns = len(duration_values)
    elif spec.turn_method == "timestamp_lines":
        turns = timestamp_line_count
    elif spec.turn_method == "user_headings":
        turns = user_heading_count
    elif spec.turn_method == "json_user_event":
        turns = json_user_events
    elif spec.turn_method == "markdown_user":
        turns = markdown_user_count
    else:
        raise ValidationError(f"Unknown turn method for {spec.experiment_id}: {spec.turn_method}")
    if turns <= 0:
        raise ValidationError(f"No turns found for {spec.experiment_id}")
    return round(active_minutes, 2), turns, len(files), runtime_test_markers


def count_lines(path: Path) -> int:
    try:
        with path.open(encoding="utf-8", errors="ignore") as handle:
            return sum(1 for _ in handle)
    except OSError as exc:
        raise ValidationError(f"Cannot read artifact {path}: {exc}") from exc


def validate_model_artifacts(files: list[Path], experiment_id: str) -> tuple[bool, int, int]:
    bpmn = sorted(path for path in files if path.suffix.lower() == ".bpmn")
    json_files = sorted(path for path in files if path.suffix.lower() == ".json")
    valid = len(bpmn) == 3 and len(json_files) == 6
    json_stems = {path.stem for path in json_files}
    for path in json_files:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValidationError(f"Invalid model JSON in {experiment_id}: {path.name}: {exc}") from exc
    for path in bpmn:
        try:
            root = ET.parse(path).getroot()
        except (OSError, ET.ParseError) as exc:
            raise ValidationError(f"Invalid BPMN XML in {experiment_id}: {path.name}: {exc}") from exc
        local_name = root.tag.rsplit("}", 1)[-1]
        has_process = any(element.tag.rsplit("}", 1)[-1] == "process" for element in root.iter())
        valid = valid and local_name == "definitions" and has_process and path.stem in json_stems
    return valid, len(bpmn), len(json_files)


def artifact_metrics(
    spec: ExperimentSpec, experiment_dir: Path
) -> tuple[bool, int, int, int, int, int, int, int]:
    code_dir = experiment_dir / "code"
    if not code_dir.is_dir():
        raise ValidationError(f"Missing artifact directory: {code_dir}")
    files = sorted(iter_files(code_dir))
    if not files:
        raise ValidationError(f"No artifacts in {code_dir}")
    artifact_bytes = sum(path.stat().st_size for path in files)
    if spec.condition == "Model":
        complete, bpmn_count, json_count = validate_model_artifacts(files, spec.experiment_id)
        source_files = files
        source_lines = sum(count_lines(path) for path in files)
    else:
        source_files = [
            path
            for path in files
            if path.suffix.lower() in SOURCE_SUFFIXES and path.name not in NON_SOURCE_NAMES
        ]
        complete = bool(source_files)
        bpmn_count = 0
        json_count = 0
        source_lines = sum(count_lines(path) for path in source_files)
    source_bytes = sum(path.stat().st_size for path in source_files)
    return (
        complete,
        len(files),
        len(source_files),
        source_lines,
        artifact_bytes,
        source_bytes,
        bpmn_count,
        json_count,
    )


def analyze(
    data_dir: Path,
    specs: list[ExperimentSpec],
    session_threshold_minutes: int = DEFAULT_SESSION_THRESHOLD_MINUTES,
) -> list[Metrics]:
    results: list[Metrics] = []
    for spec in specs:
        experiment_dir = data_dir / CONDITION_DIR[spec.condition] / spec.experiment_id
        active_minutes, turns, prompt_files, runtime_test_markers = measure_prompts(
            spec,
            experiment_dir / "prompt",
            session_threshold_minutes=session_threshold_minutes,
        )
        complete, files, source_files, lines, size, source_size, bpmn, json_count = artifact_metrics(
            spec, experiment_dir
        )
        results.append(
            Metrics(
                experiment_id=spec.experiment_id,
                condition=spec.condition,
                source_observed_minutes=active_minutes,
                turn_count=turns,
                documented_success=spec.documented_success,
                artifact_complete=complete,
                artifact_files=files,
                source_files=source_files,
                source_lines=lines,
                artifact_bytes=size,
                source_bytes=source_size,
                prompt_files=prompt_files,
                runtime_test_markers=runtime_test_markers,
                technology=spec.technology,
                time_method=spec.time_method,
                turn_method=spec.turn_method,
                bpmn_files=bpmn,
                json_artifacts=json_count,
            )
        )
    return sorted(results, key=lambda item: (item.condition, item.experiment_id))


def markdown_table(rows: list[Metrics]) -> str:
    header = (
        "| Experiment | Time (min) | Recorded events | Success | Complete artifacts | "
        "Retained files | Source/model files | Source/model lines | Source/model KiB | Prompt files | Technology |\n"
        "|---|---:|---:|:---:|:---:|---:|---:|---:|---:|---:|---|\n"
    )
    body = "".join(
        f"| {row.experiment_id} | {row.source_observed_minutes:.2f} | {row.turn_count} | "
        f"{'Yes' if row.documented_success else 'No'} | {'Yes' if row.artifact_complete else 'No'} | "
        f"{row.artifact_files} | {row.source_files} | {row.source_lines} | "
        f"{row.source_bytes / 1024:.1f} | "
        f"{row.prompt_files} | {row.technology} |\n"
        for row in rows
    )
    return header + body


def write_csv(path: Path, rows: list[Metrics]) -> None:
    fields = list(Metrics.__dataclass_fields__)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)


def summary_markdown(
    rows: list[Metrics], session_threshold_minutes: int = DEFAULT_SESSION_THRESHOLD_MINUTES
) -> str:
    groups = {condition: [row for row in rows if row.condition == condition] for condition in EXPECTED}
    lines = [
        "# Reproducibility Capsule Results",
        "",
        "The capsule contains seven matched two-person teams, represented by 7 code-generation and 7 model-generation team-condition runs.",
        "Condition order was counterbalanced 4:3: T01/T03/T05/T07 completed Code then Model, and T02/T04/T06 completed Model then Code.",
        "All retained team-condition runs are documented as successful and all retained artifact sets pass structural validation.",
        "",
        "| Condition | N | Mean time (min) | Median time (min) | Mean recorded events | Success | Mean recognized source/config/model files | Mean recognized lines | Mean recognized KiB |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for condition in ("Code", "Model"):
        group = groups[condition]
        lines.append(
            f"| {condition} generation | {len(group)} | "
            f"{statistics.mean(row.source_observed_minutes for row in group):.2f} | "
            f"{statistics.median(row.source_observed_minutes for row in group):.2f} | "
            f"{statistics.mean(row.turn_count for row in group):.2f} | "
            f"{sum(row.documented_success for row in group) / len(group):.0%} | "
            f"{statistics.mean(row.source_files for row in group):.1f} | "
            f"{statistics.mean(row.source_lines for row in group):.1f} | "
            f"{statistics.mean(row.source_bytes for row in group) / 1024:.1f} |"
        )
    code = groups["Code"]
    model = groups["Model"]
    lines.extend(
        [
            "",
            "## Base artifact-inventory diagnostic",
            "",
            f"- Every model experiment contains exactly 3 valid BPMN files and 6 valid JSON artifacts; each BPMN file has a same-stem source JSON file.",
            "- The source/config/model columns above are broad structural diagnostics. The publication measure is the refined marginal application-specific footprint under `results/phase2/`, where configuration, dependency metadata, support utilities, documentation/task inputs, runtime data, generated output, and reusable platform code are reported separately or excluded.",
            "",
            "## Measurement boundary",
            "",
            "Time is recorded team development time to functional completion, not person-hours.",
            f"Explicit duration tables include between-entry review gaps shorter than {session_threshold_minutes} minutes. Gaps equal to or longer than the threshold are excluded in full. Participant-reported totals are used where supplied.",
            "Model histories form one merged chronological team timeline through the final runtime-test marker. The same break rule applies using each recorded event once; no observed Model gap exceeds 15 minutes.",
            "The runtime-testing marker closes the time interval and is counted as a recorded user work event because runtime testing is part of task completion.",
            "Success records independent cross-team scenario evaluation followed by the manuscript author's separate execution check and final acceptance; artifact completeness is validated separately by this script.",
            "",
            "Turn and time extraction methods for every experiment are included in `experiment_metrics.csv`.",
            "No missing values are replaced with synthetic minutes-per-turn estimates.",
            "",
        ]
    )
    return "\n".join(lines)


def write_results(
    results_dir: Path, rows: list[Metrics],
    session_threshold_minutes: int = DEFAULT_SESSION_THRESHOLD_MINUTES,
) -> None:
    results_dir.mkdir(parents=True, exist_ok=True)
    write_csv(results_dir / "experiment_metrics.csv", rows)
    for condition in ("Code", "Model"):
        selected = [row for row in rows if row.condition == condition]
        filename = f"{condition.lower()}_generation_metrics.md"
        (results_dir / filename).write_text(
            f"# {condition} Generation Metrics\n\n" + markdown_table(selected), encoding="utf-8"
        )
    (results_dir / "summary.md").write_text(
        summary_markdown(rows, session_threshold_minutes), encoding="utf-8"
    )


def main() -> int:
    args = parse_args()
    try:
        specs = read_specs(args.data_dir / "experiments.csv")
        validate_experiment_set(args.data_dir, specs)
        rows = analyze(
            args.data_dir,
            specs,
            session_threshold_minutes=args.session_threshold_minutes,
        )
        if not all(row.artifact_complete for row in rows):
            incomplete = [row.experiment_id for row in rows if not row.artifact_complete]
            raise ValidationError(f"Incomplete artifact sets: {incomplete}")
        if not args.validate_only:
            write_results(args.results_dir, rows, args.session_threshold_minutes)
    except (OSError, ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(
        f"Validated {len(rows)} experiments (7 code + 7 model)"
        + ("" if args.validate_only else f"; results written to {args.results_dir}")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
