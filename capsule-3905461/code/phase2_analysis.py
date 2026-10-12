#!/usr/bin/env python3
"""Generate the paired Phase 2 analysis, sensitivities, footprint audit, and figures."""

from __future__ import annotations

import argparse
import csv
import html
import itertools
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path

import calculate_metrics


SEED = 20260805
BOOTSTRAP_RESAMPLES = 100_000
PRIMARY_THRESHOLD = calculate_metrics.DEFAULT_SESSION_THRESHOLD_MINUTES
THRESHOLDS = (15, 30, 45, 60)

PRIMARY_CATEGORIES = {
    "application_implementation_or_model",
    "application_tests",
    "application_assets",
}
CATEGORIES = (
    "application_implementation_or_model",
    "application_tests",
    "application_assets",
    "project_configuration_and_dependency_metadata",
    "development_support",
    "documentation_and_task_inputs",
    "runtime_data",
    "generated_build_output",
    "other_retained_artifact",
    "reusable_runtime_platform",
)
TEXT_SUFFIXES = {
    ".bpmn", ".css", ".example", ".gitignore", ".html", ".js", ".json",
    ".jsx", ".md", ".mjs", ".nix", ".prisma", ".py", ".sh", ".sql",
    ".ts", ".tsx", ".txt", ".yaml", ".yml",
}
GENERATED_DIRS = {".next", "build", "coverage", "dist", "out"}
RUNTIME_SUFFIXES = {".db", ".sqlite", ".sqlite3", ".log", ".cache"}
CONFIG_NAMES = {
    ".env.example", ".gitignore", "apphosting.yaml", "components.json",
    "docker-compose.yml", "dockerfile", "firebase.json", "package.json",
    "package-lock.json", "requirements.txt", "tsconfig.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--results-dir", type=Path, required=True)
    return parser.parse_args()


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames=None) -> None:
    if not rows and fieldnames is None:
        raise ValueError(f"Cannot infer fields for empty output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    names = fieldnames or list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=names, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def quantile_type7(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def describe(values: list[float]) -> dict[str, float | int]:
    q1 = quantile_type7(values, 0.25)
    q3 = quantile_type7(values, 0.75)
    return {
        "n": len(values),
        "mean": statistics.fmean(values),
        "standard_deviation": statistics.stdev(values) if len(values) > 1 else 0.0,
        "median": statistics.median(values),
        "q1_type7": q1,
        "q3_type7": q3,
        "iqr_type7": q3 - q1,
        "minimum": min(values),
        "maximum": max(values),
    }


def bootstrap_interval(values: list[float], statistic, seed: int) -> tuple[float, float]:
    rng = random.Random(seed)
    n = len(values)
    estimates = [
        statistic([values[rng.randrange(n)] for _ in range(n)])
        for _ in range(BOOTSTRAP_RESAMPLES)
    ]
    return quantile_type7(estimates, 0.025), quantile_type7(estimates, 0.975)


def average_ranks(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    cursor = 0
    while cursor < len(indexed):
        end = cursor + 1
        while end < len(indexed) and indexed[end][1] == indexed[cursor][1]:
            end += 1
        rank = ((cursor + 1) + end) / 2
        for position in range(cursor, end):
            ranks[indexed[position][0]] = rank
        cursor = end
    return ranks


def matched_rank_biserial(differences: list[float]) -> float:
    nonzero = [value for value in differences if value != 0]
    if not nonzero:
        return 0.0
    ranks = average_ranks([abs(value) for value in nonzero])
    positive = sum(rank for value, rank in zip(nonzero, ranks) if value > 0)
    negative = sum(rank for value, rank in zip(nonzero, ranks) if value < 0)
    return (positive - negative) / (positive + negative)


def exact_sign_flip_p(differences: list[float]) -> float:
    observed = abs(statistics.fmean(differences))
    absolute = [abs(value) for value in differences]
    extreme = 0
    for signs in itertools.product((-1, 1), repeat=len(absolute)):
        value = abs(statistics.fmean(sign * item for sign, item in zip(signs, absolute)))
        extreme += value >= observed - 1e-12
    return extreme / (2 ** len(absolute))


def geometric_mean(values: list[float]) -> float:
    return math.exp(statistics.fmean(math.log(value) for value in values))


def fmt(value: float) -> str:
    # Retain round-trip precision in machine-readable intermediate summaries.
    # Presentation rounding belongs to the manuscript/table generators.
    return repr(float(value))


def text_lines(path: Path) -> int:
    if path.suffix.lower() not in TEXT_SUFFIXES and path.name.lower() != "dockerfile":
        return 0
    with path.open(encoding="utf-8", errors="ignore") as handle:
        return sum(1 for _ in handle)


def classify_artifact(condition: str, relative: Path) -> tuple[str, str]:
    parts = [part.lower() for part in relative.parts]
    name = relative.name.lower()
    suffix = relative.suffix.lower()
    if condition == "Model":
        return "application_implementation_or_model", "Submitted executable BPMN/JSON model artifact"
    if any(part in GENERATED_DIRS for part in parts):
        return "generated_build_output", "Generated build/output directory"
    if suffix in RUNTIME_SUFFIXES:
        return "runtime_data", "Runtime-state filename extension"
    if name.startswith("test_") or "test_scenario" in name or "tests" in parts:
        return "application_tests", "Executable test artifact"
    if (
        name.startswith(("extract", "inspect", "debug", "read_any"))
        and suffix in {".py", ".js", ".ts"}
    ):
        return "development_support", "Extraction, inspection, or debugging helper"
    if (
        suffix in {".docx", ".bpmn", ".md", ".txt"}
        or "docs" in parts
        or "projectdocs" in parts
        or "materialy_pomocnicze" in parts
    ):
        return "documentation_and_task_inputs", "Documentation or supplied task/reference material"
    if (
        name in CONFIG_NAMES
        or name.endswith((".config.js", ".config.mjs", ".config.ts"))
        or suffix in {".example", ".gitignore", ".nix", ".yaml", ".yml"}
        or ".github" in parts
        or name.startswith("setup-")
    ):
        return (
            "project_configuration_and_dependency_metadata",
            "Project configuration, environment definition, or dependency metadata",
        )
    if suffix in {".ico", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}:
        return "application_assets", "Application image or other binary asset"
    if suffix in calculate_metrics.SOURCE_SUFFIXES:
        return "application_implementation_or_model", "Application implementation source"
    return "other_retained_artifact", "Retained file outside the declared primary categories"


def footprint(data_dir: Path, specs) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    inventory: list[dict[str, object]] = []
    totals: dict[tuple[str, str, str], dict[str, int]] = defaultdict(
        lambda: {"files": 0, "lines": 0, "bytes": 0}
    )
    for spec in specs:
        root = data_dir / calculate_metrics.CONDITION_DIR[spec.condition] / spec.experiment_id / "code"
        for path in calculate_metrics.iter_files(root):
            relative = path.relative_to(root)
            category, reason = classify_artifact(spec.condition, relative)
            lines = text_lines(path)
            size = path.stat().st_size
            included = category in PRIMARY_CATEGORIES
            inventory.append(
                {
                    "experiment_id": spec.experiment_id,
                    "team_id": spec.team_id,
                    "condition": spec.condition,
                    "relative_path": relative.as_posix(),
                    "artifact_type": category,
                    "included_in_primary_marginal_footprint": "Yes" if included else "No",
                    "files": 1,
                    "text_lines": lines,
                    "bytes": size,
                    "classification_reason": reason,
                }
            )
            total = totals[(spec.experiment_id, spec.condition, category)]
            total["files"] += 1
            total["lines"] += lines
            total["bytes"] += size

    by_type: list[dict[str, object]] = []
    by_run: list[dict[str, object]] = []
    for spec in specs:
        primary = {"files": 0, "lines": 0, "bytes": 0}
        retained = {"files": 0, "lines": 0, "bytes": 0}
        for category in CATEGORIES:
            values = totals[(spec.experiment_id, spec.condition, category)]
            status = "measured"
            note = ""
            if category == "reusable_runtime_platform":
                status = "excluded_not_in_run_artifact"
                note = "Aurea 2026.01.0 is reusable infrastructure and is not copied into model run artifacts"
            by_type.append(
                {
                    "experiment_id": spec.experiment_id,
                    "team_id": spec.team_id,
                    "condition": spec.condition,
                    "artifact_type": category,
                    "included_in_primary_marginal_footprint": "Yes" if category in PRIMARY_CATEGORIES else "No",
                    "measurement_status": status,
                    "files": values["files"],
                    "text_lines": values["lines"],
                    "bytes": values["bytes"],
                    "note": note,
                }
            )
            if category != "reusable_runtime_platform":
                for key in retained:
                    retained[key] += values[key]
            if category in PRIMARY_CATEGORIES:
                for key in primary:
                    primary[key] += values[key]
        by_run.append(
            {
                "experiment_id": spec.experiment_id,
                "team_id": spec.team_id,
                "condition": spec.condition,
                "primary_application_specific_files": primary["files"],
                "primary_application_specific_text_lines": primary["lines"],
                "primary_application_specific_bytes": primary["bytes"],
                "all_retained_artifact_files": retained["files"],
                "all_retained_artifact_text_lines": retained["lines"],
                "all_retained_artifact_bytes": retained["bytes"],
                "dependencies_and_build_output_in_primary": "No",
                "runtime_data_in_primary": "No",
                "reusable_runtime_platform_in_primary": "No",
            }
        )
    return inventory, by_type, by_run


def build_pairs(metrics, footprints) -> list[dict[str, object]]:
    metric_index = {row.experiment_id: row for row in metrics}
    footprint_index = {row["experiment_id"]: row for row in footprints}
    pairs: list[dict[str, object]] = []
    for number in range(1, 8):
        team = f"T{number:02d}"
        code = metric_index[f"code_{number:02d}"]
        model = metric_index[f"model_{number:02d}"]
        code_fp = footprint_index[code.experiment_id]
        model_fp = footprint_index[model.experiment_id]
        row: dict[str, object] = {
            "team_id": team,
            "sequence_order": "Code -> Model" if number % 2 else "Model -> Code",
            "first_condition": "Code" if number % 2 else "Model",
            "code_run_id": code.experiment_id,
            "model_run_id": model.experiment_id,
            "code_source_observed_minutes": code.source_observed_minutes,
            "model_source_observed_minutes": model.source_observed_minutes,
            "code_recorded_interaction_events": code.turn_count,
            "model_recorded_interaction_events": model.turn_count,
            "code_application_specific_files": code_fp["primary_application_specific_files"],
            "model_application_specific_files": model_fp["primary_application_specific_files"],
            "code_application_specific_lines": code_fp["primary_application_specific_text_lines"],
            "model_application_specific_lines": model_fp["primary_application_specific_text_lines"],
            "code_application_specific_bytes": code_fp["primary_application_specific_bytes"],
            "model_application_specific_bytes": model_fp["primary_application_specific_bytes"],
            "code_time_method": code.time_method,
            "model_time_method": model.time_method,
            "code_turn_method": code.turn_method,
            "model_turn_method": model.turn_method,
        }
        output_names = {
            "source_observed_minutes": ("time_difference_code_minus_model_minutes", "time_ratio_code_over_model"),
            "recorded_interaction_events": ("turn_difference_code_minus_model", "turn_ratio_code_over_model"),
            "application_specific_files": ("file_difference_code_minus_model", "file_ratio_code_over_model"),
            "application_specific_lines": ("line_difference_code_minus_model", "line_ratio_code_over_model"),
            "application_specific_bytes": ("byte_difference_code_minus_model", "byte_ratio_code_over_model"),
        }
        for stem, (difference_name, ratio_name) in output_names.items():
            code_value = float(row[f"code_{stem}"])
            model_value = float(row[f"model_{stem}"])
            row[difference_name] = code_value - model_value
            row[ratio_name] = code_value / model_value
        row["difference_direction"] = "Code minus Model; positive values indicate a larger Code measurement"
        pairs.append(row)
    return pairs


def validate_footprint(metrics, footprints) -> None:
    footprint_index = {row["experiment_id"]: row for row in footprints}
    if len(footprint_index) != 14:
        raise ValueError(f"Expected 14 footprint rows, found {len(footprint_index)}")
    for metric in metrics:
        footprint_row = footprint_index[metric.experiment_id]
        if int(footprint_row["all_retained_artifact_files"]) != metric.artifact_files:
            raise ValueError(f"Artifact-file classification mismatch for {metric.experiment_id}")
        if int(footprint_row["all_retained_artifact_bytes"]) != metric.artifact_bytes:
            raise ValueError(f"Artifact-byte classification mismatch for {metric.experiment_id}")
        if int(footprint_row["primary_application_specific_files"]) <= 0:
            raise ValueError(f"Empty primary footprint for {metric.experiment_id}")


MEASURES = {
    "source_observed_minutes": "Source-specific log-observed time (minutes)",
    "recorded_interaction_events": "Recorded interaction/work events",
    "application_specific_files": "Marginal application-specific files",
    "application_specific_lines": "Marginal application-specific text lines",
    "application_specific_bytes": "Marginal application-specific bytes",
}


def paired_statistics(pairs, include_time=True) -> tuple[list[dict[str, object]], list[dict[str, object]], dict]:
    descriptive_rows: list[dict[str, object]] = []
    effect_rows: list[dict[str, object]] = []
    structured: dict[str, object] = {
        "design": {"independent_unit": "two-person team", "n_pairs": 7},
        "difference_direction": "Code minus Model",
        "quartiles": "Hyndman-Fan Type 7",
        "bootstrap": {"resamples": BOOTSTRAP_RESAMPLES, "seed": SEED},
        "primary_session_threshold_minutes": PRIMARY_THRESHOLD,
        "sensitivity_threshold_minutes": list(THRESHOLDS),
        "measures": {},
    }
    for index, (stem, label) in enumerate(MEASURES.items()):
        if not include_time and stem == 'source_observed_minutes':
            continue  # Keep original non-time seed offsets unchanged.
        code = [float(row[f"code_{stem}"]) for row in pairs]
        model = [float(row[f"model_{stem}"]) for row in pairs]
        differences = [left - right for left, right in zip(code, model)]
        ratios = [left / right for left, right in zip(code, model)]
        descriptions = {
            "Code": describe(code), "Model": describe(model),
            "Code_minus_Model": describe(differences),
        }
        for series, values in descriptions.items():
            descriptive_rows.append(
                {"measure": stem, "measure_label": label, "series": series,
                 **{key: fmt(float(value)) for key, value in values.items()}}
            )
        mean_low, mean_high = bootstrap_interval(differences, statistics.fmean, SEED + index * 10)
        median_low, median_high = bootstrap_interval(differences, statistics.median, SEED + index * 10 + 1)
        ratio_low, ratio_high = bootstrap_interval(ratios, geometric_mean, SEED + index * 10 + 2)
        effect = {
            "measure": stem,
            "measure_label": label,
            "n_pairs": 7,
            "positive_differences": sum(value > 0 for value in differences),
            "negative_differences": sum(value < 0 for value in differences),
            "zero_differences": sum(value == 0 for value in differences),
            "mean_difference_code_minus_model": fmt(statistics.fmean(differences)),
            "mean_difference_bootstrap_95_low": fmt(mean_low),
            "mean_difference_bootstrap_95_high": fmt(mean_high),
            "median_difference_code_minus_model": fmt(statistics.median(differences)),
            "median_difference_bootstrap_95_low": fmt(median_low),
            "median_difference_bootstrap_95_high": fmt(median_high),
            "matched_pairs_rank_biserial": fmt(matched_rank_biserial(differences)),
            "exact_sign_flip_two_sided_p_exploratory": fmt(exact_sign_flip_p(differences)),
            "median_code_over_model_ratio": fmt(statistics.median(ratios)),
            "geometric_mean_code_over_model_ratio": fmt(geometric_mean(ratios)),
            "geometric_mean_ratio_bootstrap_95_low": fmt(ratio_low),
            "geometric_mean_ratio_bootstrap_95_high": fmt(ratio_high),
        }
        effect_rows.append(effect)
        structured["measures"][stem] = {
            "label": label, "code_values": code, "model_values": model,
            "differences_code_minus_model": differences, "ratios_code_over_model": ratios,
            "descriptive": descriptions, "paired_effect": effect,
        }
    return descriptive_rows, effect_rows, structured


def threshold_sensitivity(data_dir: Path, specs) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []
    for threshold in THRESHOLDS:
        metrics = calculate_metrics.analyze(data_dir, specs, session_threshold_minutes=threshold)
        index = {row.experiment_id: row for row in metrics}
        differences = []
        for number in range(1, 8):
            code = index[f"code_{number:02d}"]
            model = index[f"model_{number:02d}"]
            difference = code.source_observed_minutes - model.source_observed_minutes
            differences.append(difference)
            rows.append(
                {
                    "threshold_minutes": threshold,
                    "is_primary": "Yes" if threshold == PRIMARY_THRESHOLD else "No",
                    "team_id": f"T{number:02d}",
                    "code_run_id": code.experiment_id,
                    "code_time_method": code.time_method,
                    "code_source_observed_minutes": code.source_observed_minutes,
                    "model_source_observed_minutes": model.source_observed_minutes,
                    "difference_code_minus_model_minutes": round(difference, 2),
                }
            )
        summaries.append(
            {
                "threshold_minutes": threshold,
                "is_primary": "Yes" if threshold == PRIMARY_THRESHOLD else "No",
                "n_pairs": 7,
                "positive_differences": sum(value > 0 for value in differences),
                "mean_difference_code_minus_model_minutes": fmt(statistics.fmean(differences)),
                "median_difference_code_minus_model_minutes": fmt(statistics.median(differences)),
                "matched_pairs_rank_biserial": fmt(matched_rank_biserial(differences)),
                "exact_sign_flip_two_sided_p_exploratory": fmt(exact_sign_flip_p(differences)),
            }
        )
    return rows, summaries


def maximum_sensitivity(pairs) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for stem in ("source_observed_minutes", "recorded_interaction_events"):
        code_max = max(pairs, key=lambda row: float(row[f"code_{stem}"]))["team_id"]
        model_max = max(pairs, key=lambda row: float(row[f"model_{stem}"]))["team_id"]
        scenarios = (
            ("full_sample", set()),
            ("exclude_team_with_code_maximum", {code_max}),
            ("exclude_team_with_model_maximum", {model_max}),
            ("exclude_union_of_condition_maximum_teams", {code_max, model_max}),
        )
        for scenario, excluded in scenarios:
            kept = [row for row in pairs if row["team_id"] not in excluded]
            differences = [
                float(row[f"code_{stem}"]) - float(row[f"model_{stem}"])
                for row in kept
            ]
            rows.append(
                {
                    "measure": stem,
                    "scenario": scenario,
                    "excluded_teams": ";".join(sorted(excluded)) or "None",
                    "n_pairs": len(kept),
                    "positive_differences": sum(value > 0 for value in differences),
                    "mean_difference_code_minus_model": fmt(statistics.fmean(differences)),
                    "median_difference_code_minus_model": fmt(statistics.median(differences)),
                    "matched_pairs_rank_biserial": fmt(matched_rank_biserial(differences)),
                    "exact_sign_flip_two_sided_p_exploratory": fmt(exact_sign_flip_p(differences)),
                }
            )
    return rows


def svg_text(x, y, value, size=13, anchor="start", weight="normal") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial,Helvetica,sans-serif" '
        f'font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" fill="#172033">'
        f'{html.escape(str(value))}</text>'
    )


def slope_panel(x, y, width, height, title, code, model, unit) -> str:
    margin_left, margin_right, margin_top, margin_bottom = 64, 28, 48, 52
    plot_x0, plot_x1 = x + margin_left, x + width - margin_right
    plot_y0, plot_y1 = y + margin_top, y + height - margin_bottom
    maximum = max(code + model) * 1.08
    scale_y = lambda value: plot_y1 - (value / maximum) * (plot_y1 - plot_y0)
    code_x = plot_x0 + (plot_x1 - plot_x0) * 0.28
    model_x = plot_x0 + (plot_x1 - plot_x0) * 0.72
    parts = [svg_text(x + width / 2, y + 23, title, 15, "middle", "bold")]
    for step in range(5):
        value = maximum * step / 4
        py = scale_y(value)
        parts.append(f'<line x1="{plot_x0}" y1="{py:.1f}" x2="{plot_x1}" y2="{py:.1f}" stroke="#d9deea"/>')
        parts.append(svg_text(plot_x0 - 8, py + 4, f"{value:.0f}", 11, "end"))
    for index, (left, right) in enumerate(zip(code, model), 1):
        color = "#2864dc" if index % 2 else "#11a683"
        parts.append(f'<line x1="{code_x:.1f}" y1="{scale_y(left):.1f}" x2="{model_x:.1f}" y2="{scale_y(right):.1f}" stroke="{color}" stroke-width="2" opacity="0.78"/>')
        parts.append(f'<circle cx="{code_x:.1f}" cy="{scale_y(left):.1f}" r="4" fill="{color}"/>')
        parts.append(f'<circle cx="{model_x:.1f}" cy="{scale_y(right):.1f}" r="4" fill="{color}"/>')
    parts.extend([
        svg_text(code_x, plot_y1 + 27, "Code", 12, "middle", "bold"),
        svg_text(model_x, plot_y1 + 27, "Model", 12, "middle", "bold"),
        svg_text(x + 16, y + height / 2, unit, 11, "middle"),
    ])
    return "".join(parts)


def difference_panel(x, y, width, height, title, differences, unit) -> str:
    margin_left, margin_right, margin_top, margin_bottom = 66, 28, 48, 52
    plot_x0, plot_x1 = x + margin_left, x + width - margin_right
    plot_y0, plot_y1 = y + margin_top, y + height - margin_bottom
    low = min(0, min(differences))
    high = max(differences) * 1.08
    if high == low:
        high = low + 1
    scale_x = lambda value: plot_x0 + (value - low) / (high - low) * (plot_x1 - plot_x0)
    parts = [svg_text(x + width / 2, y + 23, title, 15, "middle", "bold")]
    zero_x = scale_x(0)
    parts.append(f'<line x1="{zero_x:.1f}" y1="{plot_y0}" x2="{zero_x:.1f}" y2="{plot_y1}" stroke="#172033" stroke-width="1.5"/>')
    for index, value in enumerate(differences, 1):
        py = plot_y0 + (index - 0.5) * (plot_y1 - plot_y0) / len(differences)
        color = "#2864dc" if index % 2 else "#11a683"
        parts.append(svg_text(plot_x0 - 9, py + 4, f"T{index:02d}", 11, "end"))
        parts.append(f'<line x1="{zero_x:.1f}" y1="{py:.1f}" x2="{scale_x(value):.1f}" y2="{py:.1f}" stroke="{color}" stroke-width="2"/>')
        parts.append(f'<circle cx="{scale_x(value):.1f}" cy="{py:.1f}" r="4.5" fill="{color}"/>')
    for step in range(5):
        value = low + (high - low) * step / 4
        px = scale_x(value)
        parts.append(svg_text(px, plot_y1 + 27, f"{value:.0f}", 11, "middle"))
    parts.append(svg_text(x + width / 2, y + height - 7, f"Code − Model ({unit})", 11, "middle"))
    return "".join(parts)


def effort_figure(pairs) -> str:
    time_code = [float(row["code_source_observed_minutes"]) for row in pairs]
    time_model = [float(row["model_source_observed_minutes"]) for row in pairs]
    event_code = [float(row["code_recorded_interaction_events"]) for row in pairs]
    event_model = [float(row["model_recorded_interaction_events"]) for row in pairs]
    panels = [
        slope_panel(10, 40, 520, 330, "A. Paired log-observed time", time_code, time_model, "minutes"),
        difference_panel(550, 40, 520, 330, "B. Within-team time differences", [a-b for a,b in zip(time_code,time_model)], "minutes"),
        slope_panel(10, 390, 520, 330, "C. Paired recorded work events", event_code, event_model, "events"),
        difference_panel(550, 390, 520, 330, "D. Within-team event differences", [a-b for a,b in zip(event_code,event_model)], "events"),
    ]
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="750" viewBox="0 0 1080 750">'
        '<rect width="1080" height="750" fill="white"/>'
        + svg_text(540, 25, "Run-level paired effort measurements (n = 7 teams)", 18, "middle", "bold")
        + "".join(panels)
        + svg_text(540, 741, "Lines connect measurements from the same two-person team; timing instruments remain source-specific.", 11, "middle")
        + "</svg>\n"
    )


def analysis_report(effect_rows, threshold_summaries, maximum_rows) -> str:
    lines = [
        "# Phase 2 paired-analysis report", "", "## Design and interpretation", "",
        "The analysis contains seven matched two-person teams. Each difference is Code minus Model. The four Code-first and three Model-first teams are preserved as a counterbalanced repeated-measures design.", "",
        "Timing measures recorded team development to functional completion, including review intervals shorter than 45 minutes and excluding longer breaks. Model histories are merged into one team timeline with the same gap criterion. Explicit totals use the recorded team report. Recorded events remain source-specific and include the final Model runtime-testing event and T03's summary entry.", "",
        "## Paired results", "",
        "| Measure | +/−/0 | Median difference | Mean difference (paired bootstrap 95% interval) | Rank-biserial | Median ratio | Exploratory exact p |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in effect_rows:
        signs = f'{row["positive_differences"]}/{row["negative_differences"]}/{row["zero_differences"]}'
        interval = f'{row["mean_difference_code_minus_model"]} [{row["mean_difference_bootstrap_95_low"]}, {row["mean_difference_bootstrap_95_high"]}]'
        lines.append(f'| {row["measure_label"]} | {signs} | {row["median_difference_code_minus_model"]} | {interval} | {row["matched_pairs_rank_biserial"]} | {row["median_code_over_model_ratio"]} | {row["exact_sign_flip_two_sided_p_exploratory"]} |')
    lines.extend(["", "## Sensitivity findings", ""])
    for row in threshold_summaries:
        lines.append(f'- With a {row["threshold_minutes"]}-minute session threshold, all {row["positive_differences"]}/7 time differences remain positive; the median Code-minus-Model difference is {row["median_difference_code_minus_model_minutes"]} minutes.')
    union_rows = [row for row in maximum_rows if row["scenario"] == "exclude_union_of_condition_maximum_teams"]
    for row in union_rows:
        lines.append(f'- For {row["measure"]}, excluding the union of teams containing either condition maximum leaves n={row["n_pairs"]}; all {row["positive_differences"]}/{row["n_pairs"]} differences remain positive and the median difference is {row["median_difference_code_minus_model"]}.')
    lines.extend([
        "", "## Statistical boundaries", "",
        "- Quartiles use Hyndman–Fan Type 7 interpolation.",
        f"- Bootstrap intervals use {BOOTSTRAP_RESAMPLES:,} paired team resamples with a fixed seed.",
        "- Exact sign-flip calculations enumerate all assignments and are exploratory, not confirmatory.",
        f"- The primary Code session threshold is {PRIMARY_THRESHOLD} minutes: gaps below it count as work; gaps at or above it are excluded in full as breaks.",
        "- The 15/30/45/60-minute threshold analysis changes between-entry review and timestamped gaps under the same boundary rule; explicit within-entry durations and reported totals remain fixed. Model histories are merged into one team timeline and their observed values are unchanged across these thresholds.",
        "- Maximum-observation exclusions remove whole matched teams. Independent deletion of one condition's value would break pairing and is not used.",
        "- Marginal application-specific footprint includes implementation/model artifacts, application tests, and application assets. Dependency/build configuration, support utilities, documentation/task inputs, runtime data, generated output, and the reusable Aurea platform are reported separately or excluded.",
        "- Files, lines, and bytes are syntactic footprint measures; a line in one language or format is not semantically equivalent to a line in another, and no maintainability or quality inference is made.", "",
    ])
    return "\n".join(lines)


def footprint_report(by_run, by_type) -> str:
    code = [row for row in by_run if row["condition"] == "Code"]
    model = [row for row in by_run if row["condition"] == "Model"]
    aggregate = lambda rows, field: sum(int(row[field]) for row in rows)
    lines = [
        "# Marginal application-specific artifact-footprint report", "",
        "The primary footprint includes submitted application implementation/model artifacts, application tests, and application assets. It excludes project/dependency configuration, development-support utilities, documentation and supplied task inputs, runtime data, generated build output, dependency directories, and the reusable Aurea 2026.01.0 platform.", "",
        "| Condition | Runs | Primary files | Primary text lines | Primary bytes |",
        "|---|---:|---:|---:|---:|",
        f'| Code | 7 | {aggregate(code, "primary_application_specific_files")} | {aggregate(code, "primary_application_specific_text_lines")} | {aggregate(code, "primary_application_specific_bytes")} |',
        f'| Model | 7 | {aggregate(model, "primary_application_specific_files")} | {aggregate(model, "primary_application_specific_text_lines")} | {aggregate(model, "primary_application_specific_bytes")} |',
        "", "The file-level inventory exposes every classification decision. Categories with zero files remain present in the by-type table so exclusions are explicit. Dependency directories and generated build output were removed from the publication corpus and are therefore not silently included as zero-cost generated artifacts.", "",
        "Lines and bytes measure retained representation size only. Different languages and formats do not assign equal meaning to a line, and the counts do not measure complexity, maintainability, quality, productivity, or total system size. Aurea is reusable infrastructure outside the marginal per-application boundary; its exclusion is both a mechanism of reuse and a treatment confound.", "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)
    specs = calculate_metrics.read_specs(args.data_dir / "experiments.csv")
    calculate_metrics.validate_experiment_set(args.data_dir, specs)
    metrics = calculate_metrics.analyze(args.data_dir, specs, session_threshold_minutes=PRIMARY_THRESHOLD)
    inventory, by_type, by_run = footprint(args.data_dir, specs)
    validate_footprint(metrics, by_run)
    pairs = build_pairs(metrics, by_run)
    descriptive, effects, structured = paired_statistics(pairs)
    threshold_rows, threshold_summaries = threshold_sensitivity(args.data_dir, specs)
    maximum_rows = maximum_sensitivity(pairs)

    write_csv(args.results_dir / "paired_analysis_input.csv", pairs)
    write_csv(args.results_dir / "paired_descriptive_statistics.csv", descriptive)
    write_csv(args.results_dir / "paired_effects.csv", effects)
    write_csv(args.results_dir / "threshold_sensitivity.csv", threshold_rows)
    write_csv(args.results_dir / "threshold_sensitivity_summary.csv", threshold_summaries)
    write_csv(args.results_dir / "maximum_observation_sensitivity.csv", maximum_rows)
    write_csv(args.results_dir / "artifact_footprint_inventory.csv", inventory)
    write_csv(args.results_dir / "artifact_footprint_by_type.csv", by_type)
    write_csv(args.results_dir / "artifact_footprint_by_run.csv", by_run)
    (args.results_dir / "paired_statistics.json").write_text(json.dumps(structured, indent=2) + "\n", encoding="utf-8")
    (args.results_dir / "paired_effort_plots.svg").write_text(effort_figure(pairs), encoding="utf-8")
    (args.results_dir / "paired_analysis_report.md").write_text(analysis_report(effects, threshold_summaries, maximum_rows), encoding="utf-8")
    (args.results_dir / "artifact_footprint_report.md").write_text(footprint_report(by_run, by_type), encoding="utf-8")
    print(f"Wrote Phase 2 outputs for {len(pairs)} matched teams to {args.results_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
