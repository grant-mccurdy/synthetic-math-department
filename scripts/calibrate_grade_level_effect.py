#!/usr/bin/env python3
"""Calibrate the grade-level prior shift from a private Canvas gradebook.

The script writes public-safe aggregate diagnostics only. It never writes source
rows, identifiers, emails, section labels, or private paths to public outputs.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PUBLIC_OUTPUT_DIR = ROOT / "reports/grade-level-calibration"

GRADE_BY_GRADUATION_YEAR = {"29": 9, "28": 10, "27": 11, "26": 12}
QUANTILES = (0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95)
SUMMARY_METRICS = ("mean", "median", "sd", "iqr", "q05", "q10", "q25", "q50", "q75", "q90", "q95", "min", "max")
PUBLIC_SUMMARY_METRICS = ("mean", "median", "sd", "iqr", "q05", "q10", "q25", "q50", "q75", "q90", "q95")
GRADE_GAPS = ((10, 9), (11, 10), (12, 11), (12, 9))


def clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))


def quantile(values: list[float], probability: float) -> float:
    if not values:
        raise ValueError("Cannot calculate a quantile from an empty list.")
    ordered = sorted(values)
    probability = clamp(probability, 0.0, 1.0)
    position = probability * (len(ordered) - 1)
    lower_idx = math.floor(position)
    upper_idx = math.ceil(position)
    if lower_idx == upper_idx:
        return ordered[lower_idx]
    fraction = position - lower_idx
    return ordered[lower_idx] * (1 - fraction) + ordered[upper_idx] * fraction


def infer_grade_from_email(email: str) -> int | None:
    local_part = email.strip().split("@", 1)[0]
    if len(local_part) < 2:
        return None
    return GRADE_BY_GRADUATION_YEAR.get(local_part[-2:])


def parse_score(value: str) -> float | None:
    value = value.strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def read_grade_score_pools(path: Path) -> dict[int, list[float]]:
    pools: dict[int, list[float]] = {grade: [] for grade in sorted(GRADE_BY_GRADUATION_YEAR.values())}
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.reader(file)
        header = next(reader)
        try:
            email_idx = header.index("Email")
            score_idx = header.index("Unposted Final Score")
        except ValueError as exc:
            raise ValueError("Expected source gradebook fields 'Email' and 'Unposted Final Score'.") from exc

        for row in reader:
            if max(email_idx, score_idx) >= len(row):
                continue
            grade = infer_grade_from_email(row[email_idx])
            score = parse_score(row[score_idx])
            if grade is None or score is None or score == 0:
                continue
            pools[grade].append(score)

    empty_grades = [grade for grade, values in pools.items() if not values]
    if empty_grades:
        raise ValueError(f"No nonzero scores found for grade(s): {empty_grades}")
    return pools


def draw_calibrated_score(rng: random.Random, source_pool: list[float]) -> float:
    draw = rng.random()
    base_score = quantile(source_pool, draw)
    lower_score = quantile(source_pool, max(draw - 0.05, 0.0))
    upper_score = quantile(source_pool, min(draw + 0.05, 1.0))
    jitter_sd = clamp((upper_score - lower_score) * 0.12, 0.75, 3.0)
    return clamp(base_score + rng.gauss(0, jitter_sd), min(source_pool), 100.0)


def summarize(values: list[float]) -> dict[str, float]:
    return {
        "mean": mean(values),
        "median": median(values),
        "sd": pstdev(values),
        "iqr": quantile(values, 0.75) - quantile(values, 0.25),
        "q05": quantile(values, 0.05),
        "q10": quantile(values, 0.10),
        "q25": quantile(values, 0.25),
        "q50": quantile(values, 0.50),
        "q75": quantile(values, 0.75),
        "q90": quantile(values, 0.90),
        "q95": quantile(values, 0.95),
        "min": min(values),
        "max": max(values),
    }


def ks_statistic(left: list[float], right: list[float]) -> float:
    left_sorted = sorted(left)
    right_sorted = sorted(right)
    left_idx = 0
    right_idx = 0
    max_distance = 0.0
    values = sorted(set(left_sorted + right_sorted))
    for value in values:
        while left_idx < len(left_sorted) and left_sorted[left_idx] <= value:
            left_idx += 1
        while right_idx < len(right_sorted) and right_sorted[right_idx] <= value:
            right_idx += 1
        max_distance = max(max_distance, abs(left_idx / len(left_sorted) - right_idx / len(right_sorted)))
    return max_distance


def wasserstein_distance(left: list[float], right: list[float]) -> float:
    probabilities = [idx / 100 for idx in range(101)]
    distances = [abs(quantile(left, probability) - quantile(right, probability)) for probability in probabilities]
    return mean(distances)


def fit_regression(rows: list[tuple[int, float]]) -> dict[str, float]:
    x_values = [grade for grade, _score in rows]
    y_values = [score for _grade, score in rows]
    x_mean = mean(x_values)
    y_mean = mean(y_values)
    ss_xx = sum((x - x_mean) ** 2 for x in x_values)
    if ss_xx == 0:
        raise ValueError("Cannot fit grade regression with zero grade variance.")
    ss_xy = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
    slope = ss_xy / ss_xx
    intercept = y_mean - slope * x_mean
    predictions = [intercept + slope * x for x in x_values]
    ss_residual = sum((y - y_hat) ** 2 for y, y_hat in zip(y_values, predictions))
    ss_total = sum((y - y_mean) ** 2 for y in y_values)
    r_squared = 1 - ss_residual / ss_total if ss_total else 0.0
    return {"slope": slope, "intercept": intercept, "r_squared": r_squared}


def interval(values: list[float], low: float, high: float) -> tuple[float, float]:
    return quantile(values, low), quantile(values, high)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, sort_keys=True)
        file.write("\n")


def svg_text(x: float, y: float, text: str, size: int = 12, anchor: str = "start") -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" font-family="Arial, sans-serif">{text}</text>'


def write_slope_distribution_svg(path: Path, slopes: list[float]) -> None:
    width = 760
    height = 420
    margin = 58
    bins = 28
    low = min(slopes)
    high = max(slopes)
    if low == high:
        low -= 1
        high += 1
    counts = [0 for _ in range(bins)]
    for slope in slopes:
        idx = min(bins - 1, int((slope - low) / (high - low) * bins))
        counts[idx] += 1
    max_count = max(counts)
    plot_width = width - 2 * margin
    plot_height = height - 2 * margin
    bars = []
    for idx, count in enumerate(counts):
        bar_width = plot_width / bins
        bar_height = plot_height * (count / max_count)
        x = margin + idx * bar_width
        y = height - margin - bar_height
        bars.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_width - 1:.2f}" height="{bar_height:.2f}" fill="#4977b8"/>')
    median_slope = median(slopes)
    median_x = margin + ((median_slope - low) / (high - low)) * plot_width
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        svg_text(width / 2, 28, "Bootstrap Regression Slope Distribution", 18, "middle"),
        f'<line x1="{margin}" y1="{height - margin}" x2="{width - margin}" y2="{height - margin}" stroke="#222"/>',
        f'<line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height - margin}" stroke="#222"/>',
        *bars,
        f'<line x1="{median_x:.2f}" y1="{margin}" x2="{median_x:.2f}" y2="{height - margin}" stroke="#b84747" stroke-width="2"/>',
        svg_text(median_x + 6, margin + 18, f"median {median_slope:.2f}", 12),
        svg_text(margin, height - 18, f"{low:.2f}", 11, "middle"),
        svg_text(width - margin, height - 18, f"{high:.2f}", 11, "middle"),
        svg_text(width / 2, height - 18, "grade-level slope", 12, "middle"),
        "</svg>",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(svg) + "\n", encoding="utf-8")


def write_quantile_calibration_svg(path: Path, source_summaries: dict[int, dict[str, float]], repeated_metric_values: dict[tuple[int, str], list[float]]) -> None:
    width = 760
    height = 520
    margin = 64
    plot_width = width - 2 * margin
    plot_height = height - 2 * margin
    colors = {9: "#4977b8", 10: "#43a66f", 11: "#c08a2a", 12: "#a64d79"}

    def px(score: float) -> float:
        return margin + (score / 100) * plot_width

    def py(score: float) -> float:
        return height - margin - (score / 100) * plot_height

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        svg_text(width / 2, 28, "Quantile Calibration By Grade", 18, "middle"),
        f'<line x1="{margin}" y1="{height - margin}" x2="{width - margin}" y2="{height - margin}" stroke="#222"/>',
        f'<line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height - margin}" stroke="#222"/>',
        f'<line x1="{margin}" y1="{height - margin}" x2="{width - margin}" y2="{margin}" stroke="#999" stroke-dasharray="4 4"/>',
    ]
    for tick in range(0, 101, 20):
        lines.append(f'<line x1="{px(tick):.1f}" y1="{height - margin}" x2="{px(tick):.1f}" y2="{height - margin + 5}" stroke="#222"/>')
        lines.append(f'<line x1="{margin - 5}" y1="{py(tick):.1f}" x2="{margin}" y2="{py(tick):.1f}" stroke="#222"/>')
        lines.append(svg_text(px(tick), height - margin + 20, str(tick), 10, "middle"))
        lines.append(svg_text(margin - 10, py(tick) + 4, str(tick), 10, "end"))

    for grade in sorted(source_summaries):
        points = []
        for probability in QUANTILES:
            metric = f"q{int(probability * 100):02d}"
            source_score = source_summaries[grade][metric]
            repeated_score = median(repeated_metric_values[(grade, metric)])
            points.append(f"{px(source_score):.2f},{py(repeated_score):.2f}")
        lines.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{colors[grade]}" stroke-width="2"/>')
        for point in points:
            x_value, y_value = point.split(",")
            lines.append(f'<circle cx="{x_value}" cy="{y_value}" r="3" fill="{colors[grade]}"/>')
        legend_y = margin + (grade - 9) * 20
        lines.append(f'<rect x="{width - margin - 110}" y="{legend_y - 10}" width="12" height="12" fill="{colors[grade]}"/>')
        lines.append(svg_text(width - margin - 92, legend_y, f"Grade {grade}", 12))

    lines.append(svg_text(width / 2, height - 18, "source quantile", 12, "middle"))
    lines.append(svg_text(16, height / 2, "repeated-sample median quantile", 12, "start"))
    lines.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_calibration(source_pools: dict[int, list[float]], replicate_count: int, seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    source_summaries = {grade: summarize(values) for grade, values in source_pools.items()}
    repeated_metric_values: dict[tuple[int, str], list[float]] = {(grade, metric): [] for grade in source_pools for metric in SUMMARY_METRICS}
    repeated_distance_values: dict[tuple[int, str], list[float]] = {(grade, metric): [] for grade in source_pools for metric in ("ks", "wasserstein", "normalized_wasserstein")}
    repeated_gap_values: dict[str, list[float]] = {}
    regression_replicates = []

    for replicate_idx in range(1, replicate_count + 1):
        sample_by_grade = {
            grade: [draw_calibrated_score(rng, source_pools[grade]) for _ in range(len(source_pools[grade]))]
            for grade in source_pools
        }

        for grade, sample in sample_by_grade.items():
            sample_summary = summarize(sample)
            for metric in SUMMARY_METRICS:
                repeated_metric_values[(grade, metric)].append(sample_summary[metric])
            ks_value = ks_statistic(source_pools[grade], sample)
            wasserstein_value = wasserstein_distance(source_pools[grade], sample)
            source_iqr = source_summaries[grade]["iqr"]
            repeated_distance_values[(grade, "ks")].append(ks_value)
            repeated_distance_values[(grade, "wasserstein")].append(wasserstein_value)
            repeated_distance_values[(grade, "normalized_wasserstein")].append(wasserstein_value / source_iqr if source_iqr else 0.0)

        for upper_grade, lower_grade in GRADE_GAPS:
            for metric in ("mean", "median"):
                key = f"grade_{upper_grade}_{metric}_minus_grade_{lower_grade}_{metric}"
                upper_value = summarize(sample_by_grade[upper_grade])[metric]
                lower_value = summarize(sample_by_grade[lower_grade])[metric]
                repeated_gap_values.setdefault(key, []).append(upper_value - lower_value)

        regression_rows = [(grade, score) for grade, values in sample_by_grade.items() for score in values]
        regression = fit_regression(regression_rows)
        regression_replicates.append(
            {
                "replicate": replicate_idx,
                "slope": regression["slope"],
                "intercept": regression["intercept"],
                "r_squared": regression["r_squared"],
            }
        )

    slopes = [row["slope"] for row in regression_replicates]
    r_squared_values = [row["r_squared"] for row in regression_replicates]
    slope_80 = interval(slopes, 0.10, 0.90)
    slope_95 = interval(slopes, 0.025, 0.975)

    return {
        "source_summaries": source_summaries,
        "repeated_metric_values": repeated_metric_values,
        "repeated_distance_values": repeated_distance_values,
        "repeated_gap_values": repeated_gap_values,
        "regression_replicates": regression_replicates,
        "regression_summary": {
            "slope_median": median(slopes),
            "slope_mean": mean(slopes),
            "slope_80_low": slope_80[0],
            "slope_80_high": slope_80[1],
            "slope_95_low": slope_95[0],
            "slope_95_high": slope_95[1],
            "p_slope_positive": sum(1 for slope in slopes if slope > 0) / len(slopes),
            "r_squared_median": median(r_squared_values),
            "r_squared_mean": mean(r_squared_values),
            "recommended_grade_prior_shift_per_grade": median(slopes) * 0.5,
        },
    }


def public_validation_rows(results: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    source_summaries = results["source_summaries"]
    repeated_metric_values = results["repeated_metric_values"]
    repeated_distance_values = results["repeated_distance_values"]
    for grade in sorted(source_summaries):
        for metric in PUBLIC_SUMMARY_METRICS:
            values = repeated_metric_values[(grade, metric)]
            rows.append(
                {
                    "grade": grade,
                    "metric": metric,
                    "source_value": round(source_summaries[grade][metric], 4),
                    "repeated_median": round(median(values), 4),
                    "repeated_p05": round(quantile(values, 0.05), 4),
                    "repeated_p95": round(quantile(values, 0.95), 4),
                }
            )
        for metric in ("ks", "wasserstein", "normalized_wasserstein"):
            values = repeated_distance_values[(grade, metric)]
            rows.append(
                {
                    "grade": grade,
                    "metric": metric,
                    "source_value": "",
                    "repeated_median": round(median(values), 4),
                    "repeated_p05": round(quantile(values, 0.05), 4),
                    "repeated_p95": round(quantile(values, 0.95), 4),
                }
            )
    return rows


def public_regression_rows(results: dict[str, Any]) -> list[dict[str, Any]]:
    summary = results["regression_summary"]
    return [{"metric": key, "value": round(value, 6)} for key, value in sorted(summary.items())]


def write_public_report(path: Path, source_pools: dict[int, list[float]], results: dict[str, Any]) -> None:
    summary = results["regression_summary"]
    source_summaries = results["source_summaries"]
    lines = [
        "# Grade-Level Calibration Report",
        "",
        "This report summarizes public-safe aggregate calibration diagnostics for the reusable longitudinal score engine.",
        "",
        "The private source path is intentionally omitted. Source rows, identifiers, emails, section labels, and exact source rows are not written here.",
        "",
        "## Source Pool Summary",
        "",
        "| Grade | Nonzero n | Mean | Median | SD | IQR |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for grade in sorted(source_pools):
        stats = source_summaries[grade]
        lines.append(
            f"| {grade} | {len(source_pools[grade])} | {stats['mean']:.2f} | {stats['median']:.2f} | {stats['sd']:.2f} | {stats['iqr']:.2f} |"
        )

    lines.extend(
        [
            "",
            "## Regression Calibration Summary",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
            f"| Slope median | {summary['slope_median']:.4f} |",
            f"| Slope mean | {summary['slope_mean']:.4f} |",
            f"| Slope 80% interval | [{summary['slope_80_low']:.4f}, {summary['slope_80_high']:.4f}] |",
            f"| Slope 95% interval | [{summary['slope_95_low']:.4f}, {summary['slope_95_high']:.4f}] |",
            f"| P(slope > 0) | {summary['p_slope_positive']:.4f} |",
            f"| R-squared median | {summary['r_squared_median']:.4f} |",
            f"| Recommended grade prior shift per grade | {summary['recommended_grade_prior_shift_per_grade']:.4f} |",
            "",
            "## Interpretation",
            "",
            "The recommended grade prior shift is a weak prior input for the longitudinal model. It should not be treated as a direct score formula or as evidence from additional real observations.",
            "",
            "Generated calibration distributions are accepted only if repeated same-size samples preserve grade-specific source summaries, quantiles, distribution distances, grade gaps, and regression behavior.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_outputs(source_pools: dict[int, list[float]], results: dict[str, Any], public_output_dir: Path, private_output_dir: Path | None, source_path: Path, seed: int, replicate_count: int) -> None:
    public_output_dir.mkdir(parents=True, exist_ok=True)
    write_public_report(public_output_dir / "grade-level-calibration-report.md", source_pools, results)
    write_csv(
        public_output_dir / "grade-level-validation-summary.csv",
        ["grade", "metric", "source_value", "repeated_median", "repeated_p05", "repeated_p95"],
        public_validation_rows(results),
    )
    write_csv(public_output_dir / "grade-level-regression-summary.csv", ["metric", "value"], public_regression_rows(results))
    write_slope_distribution_svg(public_output_dir / "grade-level-slope-distribution.svg", [row["slope"] for row in results["regression_replicates"]])
    write_quantile_calibration_svg(public_output_dir / "grade-level-quantile-calibration.svg", results["source_summaries"], results["repeated_metric_values"])

    if private_output_dir is not None:
        write_json(
            private_output_dir / "grade-level-calibration-profile.json",
            {
                "source_gradebook": str(source_path),
                "random_seed": seed,
                "replicate_count": replicate_count,
                "source_pool_counts": {str(grade): len(values) for grade, values in source_pools.items()},
                "regression_summary": results["regression_summary"],
            },
        )
        write_csv(
            private_output_dir / "grade-level-regression-replicates.csv",
            ["replicate", "slope", "intercept", "r_squared"],
            [
                {
                    "replicate": row["replicate"],
                    "slope": round(row["slope"], 8),
                    "intercept": round(row["intercept"], 8),
                    "r_squared": round(row["r_squared"], 8),
                }
                for row in results["regression_replicates"]
            ],
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calibrate grade-level effect for the synthetic longitudinal score engine.")
    parser.add_argument("--source-gradebook", default=os.environ.get("SOURCE_GRADEBOOK"), help="Path to a private Canvas gradebook CSV. May also be set with SOURCE_GRADEBOOK.")
    parser.add_argument("--public-output-dir", type=Path, default=DEFAULT_PUBLIC_OUTPUT_DIR, help="Public-safe aggregate output directory.")
    parser.add_argument("--private-output-dir", type=Path, default=None, help="Optional private output directory for calibration profile and replicate CSV.")
    parser.add_argument("--replicates", type=int, default=1000, help="Number of repeated validation/regression samples.")
    parser.add_argument("--seed", type=int, default=20260604, help="Random seed.")
    args = parser.parse_args()
    if not args.source_gradebook:
        parser.error("Provide --source-gradebook or set SOURCE_GRADEBOOK.")
    if args.replicates <= 0:
        parser.error("--replicates must be positive.")
    return args


def main() -> None:
    args = parse_args()
    source_path = Path(args.source_gradebook)
    source_pools = read_grade_score_pools(source_path)
    results = run_calibration(source_pools, args.replicates, args.seed)
    write_outputs(source_pools, results, args.public_output_dir, args.private_output_dir, source_path, args.seed, args.replicates)
    public_report = args.public_output_dir / "grade-level-calibration-report.md"
    print(f"Wrote public-safe grade calibration diagnostics to {public_report}")


if __name__ == "__main__":
    main()
