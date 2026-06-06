#!/usr/bin/env python3
"""Generate public-safe synthetic math department artifacts."""

from __future__ import annotations

import csv
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_DATA_DIR = ROOT / "data/synthetic"
STATE_PATH = SYNTHETIC_DATA_DIR / "synthetic_school_state.json"
GRADEBOOK_PATH = SYNTHETIC_DATA_DIR / "synthetic_asma_gradebook.csv"
COURSES_PATH = SYNTHETIC_DATA_DIR / "synthetic_math_courses.csv"
SECTIONS_PATH = SYNTHETIC_DATA_DIR / "synthetic_math_sections.csv"
ENROLLMENTS_PATH = SYNTHETIC_DATA_DIR / "synthetic_math_enrollments.csv"
CANVAS_COURSE_PROFILES_DIR = SYNTHETIC_DATA_DIR / "canvas_course_profiles"

SCHOOL_YEAR = "2025-2026"
SEED = 20260604
ROW_COUNT = 287
ASSIGNMENT_COUNT = 14

ATTENDANCE_CATEGORIES = (
    ("high", 0.40, (98, 2)),
    ("normal", 0.50, (92, 8)),
    ("at_risk", 0.10, (70, 30)),
)

FIRST_NAMES = (
    "Avery",
    "Blake",
    "Casey",
    "Devon",
    "Emerson",
    "Finley",
    "Gray",
    "Harper",
    "Indigo",
    "Jordan",
    "Kai",
    "Logan",
    "Morgan",
    "Noel",
    "Parker",
    "Quinn",
    "Riley",
    "Sage",
    "Taylor",
    "Vale",
)

LAST_NAMES = (
    "Stone",
    "Miller",
    "Rivera",
    "Nguyen",
    "Patel",
    "Brooks",
    "Chen",
    "Davis",
    "Evans",
    "Flores",
    "Garcia",
    "Hayes",
    "Ibrahim",
    "Johnson",
    "Kim",
    "Lewis",
    "Martinez",
    "Nelson",
    "Ortiz",
    "Price",
)

GRADE_BY_GRADUATION_YEAR = {"29": 9, "28": 10, "27": 11, "26": 12}
GRADUATION_YEAR_BY_GRADE = {grade: year for year, grade in GRADE_BY_GRADUATION_YEAR.items()}
GRADE_COUNTS = {9: 89, 10: 76, 11: 63, 12: 59}
CANVAS_SECTIONS = ("Section A", "Section B", "Section C", "Section D")

# Public-safe summary anchors for present-student Assignment 01 generation.
# These are generalized calibration parameters, not raw private scores.
ASSIGNMENT_01_SCORE_ANCHORS = {
    9: [(0.00, 7.0), (0.10, 18.0), (0.25, 29.0), (0.50, 42.0), (0.75, 56.0), (0.90, 70.0), (1.00, 90.0)],
    10: [(0.00, 10.0), (0.10, 23.0), (0.25, 34.0), (0.50, 47.0), (0.75, 62.0), (0.90, 76.0), (1.00, 95.0)],
    11: [(0.00, 12.0), (0.10, 26.0), (0.25, 38.0), (0.50, 52.0), (0.75, 68.0), (0.90, 82.0), (1.00, 98.0)],
    12: [(0.00, 14.0), (0.10, 30.0), (0.25, 43.0), (0.50, 58.0), (0.75, 74.0), (0.90, 88.0), (1.00, 100.0)],
}

COURSES = (
    {"course_id": "MATH-ALG1", "course_name": "Algebra 1", "track": "regular", "sequence_order": 1, "current_year_eligible": True},
    {"course_id": "MATH-GEOM", "course_name": "Geometry", "track": "regular", "sequence_order": 2, "current_year_eligible": True},
    {"course_id": "MATH-ALG2", "course_name": "Algebra 2", "track": "regular", "sequence_order": 3, "current_year_eligible": True},
    {"course_id": "MATH-ALG2-H", "course_name": "Honors Algebra 2", "track": "honors", "sequence_order": 3, "current_year_eligible": True},
    {"course_id": "MATH-PRECALC", "course_name": "Precalculus", "track": "regular", "sequence_order": 4, "current_year_eligible": True},
    {"course_id": "MATH-AP-PRECALC", "course_name": "AP Precalculus", "track": "ap", "sequence_order": 4, "current_year_eligible": True},
    {"course_id": "MATH-AP-CALC-AB", "course_name": "AP Calculus AB", "track": "ap", "sequence_order": 5, "current_year_eligible": True},
    {"course_id": "MATH-AP-CALC-BC", "course_name": "AP Calculus BC", "track": "ap", "sequence_order": 5, "current_year_eligible": True},
    {"course_id": "MATH-BEYOND-CORE", "course_name": "Beyond Core Math Sequence", "track": "beyond_core", "sequence_order": 6, "current_year_eligible": False},
)

GRADE_COURSE_COUNTS = {
    9: {"MATH-ALG1": 19, "MATH-GEOM": 49, "MATH-ALG2-H": 18, "MATH-AP-PRECALC": 3},
    10: {"MATH-ALG1": 2, "MATH-GEOM": 17, "MATH-ALG2": 24, "MATH-ALG2-H": 17, "MATH-PRECALC": 2, "MATH-AP-PRECALC": 11, "MATH-AP-CALC-AB": 3},
    11: {"MATH-GEOM": 5, "MATH-ALG2": 11, "MATH-ALG2-H": 8, "MATH-PRECALC": 7, "MATH-AP-PRECALC": 8, "MATH-AP-CALC-AB": 20, "MATH-AP-CALC-BC": 4},
    12: {"MATH-PRECALC": 7, "MATH-AP-PRECALC": 7, "MATH-AP-CALC-AB": 26, "MATH-AP-CALC-BC": 19},
}

SECTION_PLAN = (
    ("MATH-ALG1", 11, "TCH-001"),
    ("MATH-ALG1", 10, "TCH-001"),
    ("MATH-GEOM", 12, "TCH-001"),
    ("MATH-GEOM", 12, "TCH-001"),
    ("MATH-GEOM", 12, "TCH-001"),
    ("MATH-GEOM", 12, "TCH-002"),
    ("MATH-GEOM", 12, "TCH-002"),
    ("MATH-GEOM", 11, "TCH-002"),
    ("MATH-ALG2", 18, "TCH-002"),
    ("MATH-ALG2", 17, "TCH-002"),
    ("MATH-ALG2-H", 11, "TCH-003"),
    ("MATH-ALG2-H", 11, "TCH-003"),
    ("MATH-ALG2-H", 11, "TCH-003"),
    ("MATH-ALG2-H", 10, "TCH-003"),
    ("MATH-PRECALC", 8, "TCH-003"),
    ("MATH-PRECALC", 8, "TCH-004"),
    ("MATH-AP-PRECALC", 10, "TCH-004"),
    ("MATH-AP-PRECALC", 10, "TCH-004"),
    ("MATH-AP-PRECALC", 9, "TCH-004"),
    ("MATH-AP-CALC-AB", 13, "TCH-004"),
    ("MATH-AP-CALC-AB", 12, "TCH-005"),
    ("MATH-AP-CALC-AB", 12, "TCH-005"),
    ("MATH-AP-CALC-AB", 12, "TCH-005"),
    ("MATH-AP-CALC-BC", 12, "TCH-005"),
    ("MATH-AP-CALC-BC", 11, "TCH-005"),
)

TEACHER_GROWTH_EFFECTS = {"TCH-001": -0.25, "TCH-002": 0.10, "TCH-003": 0.20, "TCH-004": -0.10, "TCH-005": 0.05}

LONGITUDINAL_MODEL_VERSION = "longitudinal_score_engine_v1"
GRADE_PRIOR_SHIFT_PER_GRADE = 1.7953
READINESS_PRIOR_BASE_GRADE_9 = 45.0
READINESS_PRIOR_SD = 14.0
MEASUREMENT_ERROR_SD = 6.0
GROWTH_NOISE_SD = 2.5
OBSERVATION_NOISE_SD = 3.0
REGRESSION_TO_MEAN_STRENGTH = 0.08
REGRESSION_TO_MEAN_CAP = 3.0

GRADE_BASE_GROWTH = {9: 6.0, 10: 5.3, 11: 4.6, 12: 3.9}
TRACK_READINESS_EFFECTS = {"regular": 0.0, "honors": 4.0, "ap": 6.0, "beyond_core": 8.0}
TRACK_GROWTH_EFFECTS = {"regular": 0.0, "honors": 0.50, "ap": 0.25, "beyond_core": 0.0}


@dataclass(frozen=True)
class AssessmentContext:
    assignment_label: str
    assessment_window: str
    transition_type: str
    grade_level: int
    course_id: str
    course_track: str
    teacher_id: str
    instructor_effect: float
    section_effect: float


@dataclass(frozen=True)
class AssessmentResult:
    observed_score: float
    potential_score: float
    present: bool
    generation_mode: str
    transition_type: str
    posterior_readiness: float | None
    growth_delta: float | None


def clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))


def build_grade_level_sequence() -> tuple[int, ...]:
    grades = [grade for grade, count in GRADE_COUNTS.items() for _ in range(count)]
    if len(grades) != ROW_COUNT:
        raise ValueError(f"Grade counts produce {len(grades)} rows, expected {ROW_COUNT}.")
    rng = random.Random(SEED + 17)
    rng.shuffle(grades)
    return tuple(grades)


GRADE_LEVEL_SEQUENCE = build_grade_level_sequence()


def interpolate_anchor_score(anchors: list[tuple[float, float]], probability: float) -> float:
    probability = clamp(probability, 0.0, 1.0)
    for idx, (upper_p, upper_score) in enumerate(anchors):
        if probability <= upper_p:
            if idx == 0:
                return upper_score
            lower_p, lower_score = anchors[idx - 1]
            if upper_p == lower_p:
                return upper_score
            fraction = (probability - lower_p) / (upper_p - lower_p)
            return lower_score * (1 - fraction) + upper_score * fraction
    return anchors[-1][1]


def draw_present_assignment_01_score(rng: random.Random, grade_level: int) -> float:
    anchors = ASSIGNMENT_01_SCORE_ANCHORS[grade_level]
    draw = rng.random()
    base_score = interpolate_anchor_score(anchors, draw)
    lower_score = interpolate_anchor_score(anchors, max(draw - 0.05, 0.0))
    upper_score = interpolate_anchor_score(anchors, min(draw + 0.05, 1.0))
    jitter_sd = clamp((upper_score - lower_score) * 0.12, 0.75, 3.0)
    score = base_score + rng.gauss(0, jitter_sd)
    return round(clamp(score, anchors[0][1], 100.0), 2)


def choose_attendance_category(rng: random.Random) -> tuple[str, tuple[int, int]]:
    draw = rng.random()
    cumulative = 0.0
    for name, probability, beta_params in ATTENDANCE_CATEGORIES:
        cumulative += probability
        if draw <= cumulative:
            return name, beta_params
    name, _probability, beta_params = ATTENDANCE_CATEGORIES[-1]
    return name, beta_params


def assignment_01_outcome(rng: random.Random, grade_level: int) -> tuple[float, dict[str, str | float | bool | int]]:
    potential_score = draw_present_assignment_01_score(rng, grade_level)
    category, beta_params = choose_attendance_category(rng)
    attendance_probability = rng.betavariate(*beta_params)
    present = rng.random() < attendance_probability
    observed_score = potential_score if present else 0.0
    return observed_score, {
        "grade_level": grade_level,
        "potential_assignment_01_score": potential_score,
        "attendance_category": category,
        "attendance_probability": round(attendance_probability, 4),
        "present_assignment_01": present,
        "assignment_01_score": observed_score,
    }


def readiness_prior_mean(grade_level: int, course_track: str) -> float:
    grade_shift = (grade_level - 9) * GRADE_PRIOR_SHIFT_PER_GRADE
    track_shift = TRACK_READINESS_EFFECTS[course_track]
    return READINESS_PRIOR_BASE_GRADE_9 + grade_shift + track_shift


def bayesian_readiness_update(prior_mean: float, observed_score: float) -> float:
    prior_precision = 1 / (READINESS_PRIOR_SD**2)
    observation_precision = 1 / (MEASUREMENT_ERROR_SD**2)
    posterior = ((prior_mean * prior_precision) + (observed_score * observation_precision)) / (prior_precision + observation_precision)
    return clamp(posterior, 0.0, 100.0)


def transition_growth(rng: random.Random, posterior_readiness: float, context: AssessmentContext) -> float:
    base_growth = GRADE_BASE_GROWTH[context.grade_level]
    track_growth = TRACK_GROWTH_EFFECTS[context.course_track]
    regression_target = readiness_prior_mean(context.grade_level, context.course_track) + base_growth
    regression_to_mean = clamp(
        (regression_target - posterior_readiness) * REGRESSION_TO_MEAN_STRENGTH,
        -REGRESSION_TO_MEAN_CAP,
        REGRESSION_TO_MEAN_CAP,
    )
    return (
        base_growth
        + track_growth
        + context.instructor_effect
        + context.section_effect
        + regression_to_mean
        + rng.gauss(0, GROWTH_NOISE_SD)
    )


def end_of_year_first_evidence_score(rng: random.Random, context: AssessmentContext) -> float:
    baseline_score = draw_present_assignment_01_score(rng, context.grade_level)
    baseline_readiness = bayesian_readiness_update(readiness_prior_mean(context.grade_level, context.course_track), baseline_score)
    growth = transition_growth(rng, baseline_readiness, context)
    potential_score = baseline_readiness + growth + rng.gauss(0, OBSERVATION_NOISE_SD)
    return round(clamp(potential_score, 0.0, 100.0), 2)


def generate_next_assessment_score(
    rng: random.Random,
    student_profile: dict[str, str | float | bool | int],
    previous_present_score: float | None,
    context: AssessmentContext,
) -> AssessmentResult:
    attendance_probability = float(student_profile["attendance_probability"])
    present = rng.random() < attendance_probability

    if not present:
        return AssessmentResult(
            observed_score=0.0,
            potential_score=0.0,
            present=False,
            generation_mode="absent_no_update",
            transition_type="absent_no_update",
            posterior_readiness=None,
            growth_delta=None,
        )

    prior_mean = readiness_prior_mean(context.grade_level, context.course_track)
    if previous_present_score is None:
        potential_score = end_of_year_first_evidence_score(rng, context)
        posterior_readiness = bayesian_readiness_update(prior_mean, potential_score)
        return AssessmentResult(
            observed_score=potential_score,
            potential_score=potential_score,
            present=True,
            generation_mode="first_evidence_assignment_02",
            transition_type="initialize_readiness",
            posterior_readiness=round(posterior_readiness, 4),
            growth_delta=None,
        )

    posterior_readiness = bayesian_readiness_update(prior_mean, previous_present_score)
    growth = transition_growth(rng, posterior_readiness, context)
    potential_score = round(clamp(posterior_readiness + growth + rng.gauss(0, OBSERVATION_NOISE_SD), 0.0, 100.0), 2)
    return AssessmentResult(
        observed_score=potential_score,
        potential_score=potential_score,
        present=True,
        generation_mode="growth_from_assignment_01",
        transition_type=context.transition_type,
        posterior_readiness=round(bayesian_readiness_update(prior_mean, potential_score), 4),
        growth_delta=round(potential_score - previous_present_score, 4),
    )


def class_size_band(size: int) -> str:
    if 7 <= size <= 12:
        return "small"
    if 13 <= size <= 18:
        return "standard"
    if 19 <= size <= 24:
        return "large"
    raise ValueError(f"Section target enrollment {size} is outside configured class-size bands.")


def teacher_label(teacher_id: str) -> str:
    number = int(teacher_id.split("-")[1])
    return f"Teacher {number:02d}"


def section_growth_effect(section_index: int) -> float:
    pattern = (-0.30, -0.20, -0.10, 0.00, 0.10, 0.20, 0.30)
    return pattern[(section_index - 1) % len(pattern)]


def synthetic_student_profile(idx: int) -> tuple[str, str, str, str]:
    first_name = FIRST_NAMES[(idx - 1) % len(FIRST_NAMES)]
    last_name = LAST_NAMES[((idx - 1) // len(FIRST_NAMES) + idx - 1) % len(LAST_NAMES)]
    graduation_year = GRADUATION_YEAR_BY_GRADE[GRADE_LEVEL_SEQUENCE[idx - 1]]
    section = CANVAS_SECTIONS[(idx - 1) % len(CANVAS_SECTIONS)]
    return first_name, last_name, graduation_year, section


def build_teacher_rows() -> list[dict[str, str | int | float]]:
    return [
        {
            "school_year": SCHOOL_YEAR,
            "teacher_id": teacher_id,
            "teacher_label": teacher_label(teacher_id),
            "target_section_load": 5,
            "teacher_growth_effect": effect,
        }
        for teacher_id, effect in sorted(TEACHER_GROWTH_EFFECTS.items())
    ]


def build_course_rows() -> list[dict[str, str | int | bool]]:
    return [dict(course) for course in COURSES]


def build_section_rows() -> list[dict[str, str | int | float]]:
    course_lookup = {course["course_id"]: course["course_name"] for course in COURSES}
    rows = []
    for idx, (course_id, target_enrollment, teacher_id) in enumerate(SECTION_PLAN, start=1):
        rows.append(
            {
                "school_year": SCHOOL_YEAR,
                "section_id": f"SEC-{idx:03d}",
                "course_id": course_id,
                "section_label": f"{course_lookup[course_id]} - Synthetic Section {idx:02d}",
                "teacher_id": teacher_id,
                "teacher_label": teacher_label(teacher_id),
                "period_label": f"Period {((idx - 1) % 6) + 1}",
                "target_enrollment": target_enrollment,
                "max_capacity": {"small": 12, "standard": 18, "large": 24}[class_size_band(target_enrollment)],
                "class_size_band": class_size_band(target_enrollment),
                "section_growth_effect": section_growth_effect(idx),
                "teacher_growth_effect": TEACHER_GROWTH_EFFECTS[teacher_id],
            }
        )
    return rows


def infer_grade_from_email(email: str) -> int:
    graduation_year = email.strip().split("@", 1)[0][-2:]
    if graduation_year not in GRADE_BY_GRADUATION_YEAR:
        raise ValueError(f"Could not infer grade from synthetic email: {email}")
    return GRADE_BY_GRADUATION_YEAR[graduation_year]


def assign_courses_to_students(rows: list[dict[str, str]]) -> dict[str, str]:
    rng = random.Random(SEED + 31)
    students_by_grade: dict[int, list[dict[str, str]]] = {grade: [] for grade in GRADE_COUNTS}
    for row in rows:
        students_by_grade[infer_grade_from_email(row["Email"])].append(row)

    student_course: dict[str, str] = {}
    for grade, expected_count in GRADE_COUNTS.items():
        students = students_by_grade[grade]
        if len(students) != expected_count:
            raise ValueError(f"Grade {grade} has {len(students)} students, expected {expected_count}.")
        rng.shuffle(students)
        cursor = 0
        for course_id, count in GRADE_COURSE_COUNTS[grade].items():
            for student in students[cursor : cursor + count]:
                student_course[student["SIS User ID"]] = course_id
            cursor += count
        if cursor != len(students):
            raise ValueError(f"Grade {grade} course counts assigned {cursor} students, expected {len(students)}.")
    return student_course


def build_enrollment_rows(rows: list[dict[str, str]], section_rows: list[dict[str, str | int | float]]) -> list[dict[str, str | int]]:
    rng = random.Random(SEED + 43)
    student_course = assign_courses_to_students(rows)
    students_by_course: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        students_by_course.setdefault(student_course[row["SIS User ID"]], []).append(row)

    sections_by_course: dict[str, list[dict[str, str | int | float]]] = {}
    for section in section_rows:
        sections_by_course.setdefault(str(section["course_id"]), []).append(section)

    enrollment_rows = []
    for course_id, students in sorted(students_by_course.items()):
        sections = sections_by_course.get(course_id, [])
        target_total = sum(int(section["target_enrollment"]) for section in sections)
        if target_total != len(students):
            raise ValueError(f"{course_id} has {len(students)} students but section targets sum to {target_total}.")
        rng.shuffle(students)
        cursor = 0
        for section in sections:
            section_size = int(section["target_enrollment"])
            for student in students[cursor : cursor + section_size]:
                enrollment_rows.append(
                    {
                        "school_year": SCHOOL_YEAR,
                        "Student": student["Student"],
                        "SIS User ID": student["SIS User ID"],
                        "grade_level": infer_grade_from_email(student["Email"]),
                        "course_id": course_id,
                        "section_id": section["section_id"],
                        "teacher_id": section["teacher_id"],
                        "enrollment_status": "active",
                    }
                )
            cursor += section_size
    return sorted(enrollment_rows, key=lambda row: str(row["SIS User ID"]))


def build_assignment_definitions() -> list[dict[str, str | int]]:
    assignments = []
    for idx in range(1, ASSIGNMENT_COUNT + 1):
        transition_type = "initialize_readiness" if idx == 1 else "school_year_growth" if idx % 2 == 0 else "summer_atrophy"
        assignments.append(
            {
                "assignment_label": f"Assignment {idx:02d}",
                "sequence_index": idx,
                "school_year_offset": (idx - 1) // 2,
                "assessment_window": "beginning_of_year" if idx % 2 == 1 else "end_of_year",
                "transition_type": transition_type,
                "population_status": "populated" if idx <= 2 else "pending_rules",
            }
        )
    return assignments


def build_assessment_context(
    row: dict[str, str],
    course_rows: list[dict[str, str | int | bool]],
    section_rows: list[dict[str, str | int | float]],
    enrollment_rows: list[dict[str, str | int]],
) -> AssessmentContext:
    course_by_id = {str(course["course_id"]): course for course in course_rows}
    section_by_id = {str(section["section_id"]): section for section in section_rows}
    enrollment_by_student_id = {str(enrollment["SIS User ID"]): enrollment for enrollment in enrollment_rows}
    enrollment = enrollment_by_student_id[row["SIS User ID"]]
    section = section_by_id[str(enrollment["section_id"])]
    course = course_by_id[str(enrollment["course_id"])]
    return AssessmentContext(
        assignment_label="Assignment 02",
        assessment_window="end_of_year",
        transition_type="school_year_growth",
        grade_level=int(enrollment["grade_level"]),
        course_id=str(enrollment["course_id"]),
        course_track=str(course["track"]),
        teacher_id=str(enrollment["teacher_id"]),
        instructor_effect=float(section["teacher_growth_effect"]),
        section_effect=float(section["section_growth_effect"]),
    )


def populate_assignment_02(
    rows: list[dict[str, str]],
    assessment_profiles: dict[str, dict[str, str | float | bool | int | None]],
    course_rows: list[dict[str, str | int | bool]],
    section_rows: list[dict[str, str | int | float]],
    enrollment_rows: list[dict[str, str | int]],
) -> None:
    rng = random.Random(SEED + 59)
    for row in rows:
        profile = assessment_profiles[row["SIS User ID"]]
        context = build_assessment_context(row, course_rows, section_rows, enrollment_rows)
        assignment_01_score = parse_score(row["Assignment 01"])
        previous_present_score = assignment_01_score if bool(profile["present_assignment_01"]) else None
        result = generate_next_assessment_score(rng, profile, previous_present_score, context)
        row["Assignment 02"] = format_score(result.observed_score)
        profile.update(
            {
                "assignment_02_score": result.observed_score,
                "potential_assignment_02_score": result.potential_score,
                "present_assignment_02": result.present,
                "assignment_02_generation_mode": result.generation_mode,
                "assignment_02_transition_type": result.transition_type,
                "assignment_02_growth_delta": result.growth_delta,
                "posterior_readiness_after_assignment_02": result.posterior_readiness,
                "academic_profile_status": (
                    "initialized_assignment_02"
                    if result.generation_mode == "first_evidence_assignment_02"
                    else "updated_assignment_02"
                    if result.generation_mode == "growth_from_assignment_01"
                    else "initialized_assignment_01"
                    if previous_present_score is not None
                    else "pending_no_present_scores"
                ),
                "assignment_02_course_id": context.course_id,
                "assignment_02_course_track": context.course_track,
                "assignment_02_teacher_id": context.teacher_id,
                "assignment_02_window": context.assessment_window,
            }
        )


def build_rows() -> tuple[
    list[dict[str, str]],
    list[dict[str, str | int | bool]],
    list[dict[str, str | int | float]],
    list[dict[str, str | int]],
    dict[str, dict[str, str | float | bool | int | None]],
]:
    rng = random.Random(SEED)
    rows = []
    assessment_profiles: dict[str, dict[str, str | float | bool | int | None]] = {}
    for idx in range(1, ROW_COUNT + 1):
        first_name, last_name, graduation_year, canvas_section = synthetic_student_profile(idx)
        grade_level = GRADE_BY_GRADUATION_YEAR[graduation_year]
        assignment_score, assignment_profile = assignment_01_outcome(rng, grade_level)
        row = {
            "Student": f"Synthetic Student {idx:03d}",
            "ID": f"SYN-EXP-{idx:06d}",
            "SIS User ID": f"SYN-SIS-{idx:06d}",
            "SIS Login ID": f"synthetic{idx:03d}",
            "Email": f"{first_name[0].lower()}{last_name.lower()}{graduation_year}@schoolname.org",
            "Section": canvas_section,
            "Assignment 01": f"{assignment_score:g}",
        }
        for assignment_index in range(2, ASSIGNMENT_COUNT + 1):
            row[f"Assignment {assignment_index:02d}"] = ""
        rows.append(row)
        assignment_profile["academic_profile_status"] = "initialized_assignment_01" if assignment_profile["present_assignment_01"] else "pending_no_present_scores"
        assessment_profiles[row["SIS User ID"]] = assignment_profile

    course_rows = build_course_rows()
    section_rows = build_section_rows()
    enrollment_rows = build_enrollment_rows(rows, section_rows)
    populate_assignment_02(rows, assessment_profiles, course_rows, section_rows, enrollment_rows)
    return rows, course_rows, section_rows, enrollment_rows, assessment_profiles


def parse_score(value: str | float | int | None) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def format_score(value: float | int | str | None) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, str):
        return value
    return f"{value:g}"


def build_synthetic_math_department_state(
    rows: list[dict[str, str]],
    course_rows: list[dict[str, str | int | bool]],
    section_rows: list[dict[str, str | int | float]],
    enrollment_rows: list[dict[str, str | int]],
    assessment_profiles: dict[str, dict[str, str | float | bool | int | None]],
) -> dict[str, Any]:
    students = []
    for row in rows:
        grade_level = infer_grade_from_email(row["Email"])
        assignment_scores = {
            f"Assignment {idx:02d}": parse_score(row[f"Assignment {idx:02d}"])
            for idx in range(1, ASSIGNMENT_COUNT + 1)
            if parse_score(row[f"Assignment {idx:02d}"]) is not None
        }
        students.append(
            {
                "student_key": row["SIS User ID"],
                "student_label": row["Student"],
                "export_id": row["ID"],
                "login_id": row["SIS Login ID"],
                "email": row["Email"],
                "grade_level": grade_level,
                "graduation_year_suffix": GRADUATION_YEAR_BY_GRADE[grade_level],
                "canvas_gradebook_section": row["Section"],
                "assignment_scores": assignment_scores,
                "assessment_profile": assessment_profiles[row["SIS User ID"]],
            }
        )

    canvas_profile_artifacts = [
        f"canvas_course_profiles/{course['course_id']}.json"
        for course in course_rows
        if course["current_year_eligible"]
    ]

    return {
        "schema_version": "synthetic_math_department_state_v2",
        "random_seed": SEED,
        "school_year": SCHOOL_YEAR,
        "longitudinal_model": {
            "model_version": LONGITUDINAL_MODEL_VERSION,
            "generated_assignments": ["Assignment 02"],
            "implemented_transition_types": ["initialize_readiness", "school_year_growth", "absent_no_update"],
            "planned_transition_types": ["summer_atrophy"],
            "grade_prior_shift_per_grade": GRADE_PRIOR_SHIFT_PER_GRADE,
            "readiness_prior_sd": READINESS_PRIOR_SD,
            "measurement_error_sd": MEASUREMENT_ERROR_SD,
            "growth_noise_sd": GROWTH_NOISE_SD,
            "observation_noise_sd": OBSERVATION_NOISE_SD,
        },
        "students": sorted(students, key=lambda student: str(student["student_key"])),
        "teachers": build_teacher_rows(),
        "courses": course_rows,
        "sections": section_rows,
        "enrollments": enrollment_rows,
        "assessment_shells": [
            {
                "assessment_shell_id": "ASMA-ALL-MATH-2025-2026",
                "assessment_shell_label": "All School Math Assessment",
                "school_year": SCHOOL_YEAR,
                "source_system": "synthetic_canvas",
                "join_key": "email",
                "raw_gradebook_artifact": "synthetic_asma_gradebook.csv",
                "student_count": len(rows),
                "assignment_count": ASSIGNMENT_COUNT,
            }
        ],
        "assignments": build_assignment_definitions(),
        "derived_artifacts": [
            "synthetic_asma_gradebook.csv",
            "synthetic_math_courses.csv",
            "synthetic_math_sections.csv",
            "synthetic_math_enrollments.csv",
            *canvas_profile_artifacts,
        ],
    }


def render_canvas_course_profiles_from_state(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    students_by_id = {student["student_key"]: student for student in state["students"]}
    sections_by_course: dict[str, list[dict[str, Any]]] = {}
    for section in state["sections"]:
        sections_by_course.setdefault(section["course_id"], []).append(section)

    enrollments_by_section: dict[str, list[dict[str, Any]]] = {}
    for enrollment in state["enrollments"]:
        enrollments_by_section.setdefault(enrollment["section_id"], []).append(enrollment)

    profiles = {}
    for course in state["courses"]:
        if not course["current_year_eligible"]:
            continue

        course_sections = []
        for section in sorted(sections_by_course.get(course["course_id"], []), key=lambda row: row["section_id"]):
            section_students = []
            for enrollment in sorted(enrollments_by_section.get(section["section_id"], []), key=lambda row: row["SIS User ID"]):
                student = students_by_id[enrollment["SIS User ID"]]
                section_students.append(
                    {
                        "Student": student["student_label"],
                        "SIS User ID": student["student_key"],
                        "Email": student["email"],
                        "grade_level": student["grade_level"],
                        "enrollment_status": enrollment["enrollment_status"],
                    }
                )

            course_sections.append(
                {
                    "section_id": section["section_id"],
                    "section_label": section["section_label"],
                    "period_label": section["period_label"],
                    "teacher": {
                        "teacher_id": section["teacher_id"],
                        "teacher_label": section["teacher_label"],
                    },
                    "students": section_students,
                }
            )

        profiles[f"{course['course_id']}.json"] = {
            "canvas_course_id": f"SYN-CANVAS-{course['course_id']}-{state['school_year']}",
            "course_id": course["course_id"],
            "course_name": course["course_name"],
            "track": course["track"],
            "school_year": state["school_year"],
            "source_system": "synthetic_canvas",
            "sections": course_sections,
        }

    return profiles


def render_gradebook_rows_from_state(state: dict[str, Any]) -> list[dict[str, str]]:
    assignment_labels = [assignment["assignment_label"] for assignment in state["assignments"]]
    return [
        {
            "Student": student["student_label"],
            "ID": student["export_id"],
            "SIS User ID": student["student_key"],
            "SIS Login ID": student["login_id"],
            "Email": student["email"],
            "Section": student["canvas_gradebook_section"],
            **{label: format_score(student["assignment_scores"].get(label)) for label in assignment_labels},
        }
        for student in state["students"]
    ]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str | float | int | bool]]) -> None:
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


def write_canvas_course_profiles(path: Path, profiles: dict[str, dict[str, Any]]) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for old_profile in path.glob("*.json"):
        old_profile.unlink()
    for filename, profile in sorted(profiles.items()):
        write_json(path / filename, profile)


def main() -> None:
    rows, course_rows, section_rows, enrollment_rows, assessment_profiles = build_rows()
    state = build_synthetic_math_department_state(rows, course_rows, section_rows, enrollment_rows, assessment_profiles)
    gradebook_rows = render_gradebook_rows_from_state(state)
    canvas_course_profiles = render_canvas_course_profiles_from_state(state)

    write_json(STATE_PATH, state)
    write_canvas_course_profiles(CANVAS_COURSE_PROFILES_DIR, canvas_course_profiles)
    write_csv(
        GRADEBOOK_PATH,
        ["Student", "ID", "SIS User ID", "SIS Login ID", "Email", "Section", *[f"Assignment {idx:02d}" for idx in range(1, ASSIGNMENT_COUNT + 1)]],
        gradebook_rows,
    )
    write_csv(COURSES_PATH, ["course_id", "course_name", "track", "sequence_order", "current_year_eligible"], course_rows)
    write_csv(
        SECTIONS_PATH,
        [
            "school_year",
            "section_id",
            "course_id",
            "section_label",
            "teacher_id",
            "teacher_label",
            "period_label",
            "target_enrollment",
            "max_capacity",
            "class_size_band",
            "section_growth_effect",
            "teacher_growth_effect",
        ],
        section_rows,
    )
    write_csv(
        ENROLLMENTS_PATH,
        ["school_year", "Student", "SIS User ID", "grade_level", "course_id", "section_id", "teacher_id", "enrollment_status"],
        enrollment_rows,
    )


if __name__ == "__main__":
    main()
