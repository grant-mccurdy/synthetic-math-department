# Synthetic Math Department Methodology

## Purpose

This project generates a public-safe synthetic math department environment. The output is intended to behave like a plausible math department data system without exposing real students, real course rosters, real LMS exports, or private institutional records.

The generator is designed around one canonical state object:

```text
data/synthetic/synthetic_school_state.json
```

CSV outputs are rendered from that state rather than generated as unrelated files.

Canvas-style course profile JSON files are also rendered from that state:

```text
data/synthetic/canvas_course_profiles/
```

## Baseline Environment

The current baseline simulates one school year:

```text
2025-2026
```

The current environment includes:

- 287 synthetic students
- 5 synthetic teachers
- 9 course entries
- 25 sections
- one active math enrollment per student
- 8 current-year Canvas-style course JSON profiles
- 14 all-school math assessment assignment fields

The baseline is intentionally a compact math department rather than a full-school simulation.

## Downstream Analysis Use

The current dataset is ready for one-academic-year analysis. It includes a beginning-of-year assessment, an end-of-year assessment, one active math enrollment per student, synthetic teacher/section context, course/track placement, and Canvas-style course profile JSONs.

The downstream analysis project can use this dataset to model:

- BOY-to-EOY growth
- score distributions by grade, course, track, teacher, and section
- attendance/non-participation effects
- Canvas gradebook joins to course profile JSONs
- public-safe reporting and dashboard workflows

## Course Catalog

The course catalog focuses on the core high-school math sequence:

| Course ID | Course | Track |
| --- | --- | --- |
| `MATH-ALG1` | Algebra 1 | regular |
| `MATH-GEOM` | Geometry | regular |
| `MATH-ALG2` | Algebra 2 | regular |
| `MATH-ALG2-H` | Honors Algebra 2 | honors |
| `MATH-PRECALC` | Precalculus | regular |
| `MATH-AP-PRECALC` | AP Precalculus | ap |
| `MATH-AP-CALC-AB` | AP Calculus AB | ap |
| `MATH-AP-CALC-BC` | AP Calculus BC | ap |
| `MATH-BEYOND-CORE` | Beyond Core Math Sequence | beyond_core |

Geometry has no honors equivalent in the baseline. Honors/AP differentiation begins after Geometry. Statistics courses are excluded from the baseline.

## Assignment 01 Score Generation

`Assignment 01` models a beginning-of-year all-school math assessment.

The generator separates two processes:

```text
present-student academic score
attendance / non-participation outcome
```

The present-student academic score is drawn from grade-specific public-safe calibration anchors. These anchors are generalized distribution parameters, not raw private scores.

Then the generator draws attendance status:

| Attendance category | Student share | Distribution |
| --- | ---: | --- |
| `high` | 40% | `Beta(98, 2)` |
| `normal` | 50% | `Beta(92, 8)` |
| `at_risk` | 10% | `Beta(70, 30)` |

If the student is present, the observed `Assignment 01` score is the synthetic academic score. If the student is absent, the observed score is `0`.

Under this model, a zero on Assignment 01 means non-participation. It is not academic evidence.

## Reusable Longitudinal Score Engine

The longitudinal model is implemented as a reusable next-assessment score engine. `Assignment 02` is the first application because it is the next assessment window, not because the model is specific to Assignment 02.

Conceptual contract:

```text
student state
+ prior assessment history
+ assessment context
-> observed score
-> updated academic/attendance state
```

The engine separates:

```text
latent readiness
school-year growth or summer transition
assessment observation noise
attendance / non-participation
```

If a student is absent, the observed score is `0` and academic readiness is not updated.

## Assignment 02-14

Assignments 02-14 represent future longitudinal assessment windows:

| Assignment | Intended window |
| --- | --- |
| `Assignment 01` | beginning of year |
| `Assignment 02` | end of year |
| `Assignment 03` | beginning of next year |
| `Assignment 04` | end of next year |

`Assignment 02` is populated as the first end-of-year transition. Assignments 03-14 remain blank until later transition rules are implemented and validated.

The intended transition pattern is:

```text
Assignment 01 -> Assignment 02: school-year growth
Assignment 02 -> Assignment 03: summer atrophy / retention loss
Assignment 03 -> Assignment 04: school-year growth
Assignment 04 -> Assignment 05: summer atrophy / retention loss
```

Summer atrophy is part of the same longitudinal model as a distinct transition type. It should update latent readiness between an end-of-year assessment and the next beginning-of-year assessment rather than acting as a separate score adjustment outside the model.

## Assignment 02 Score Generation

`Assignment 02` models an end-of-year assessment for the same school year as Assignment 01.

The implemented transition cases are:

| Case | Generation mode | Rule |
| --- | --- | --- |
| Assignment 01 present, Assignment 02 present | `growth_from_assignment_01` | update readiness from Assignment 01, apply school-year growth, observe Assignment 02 |
| Assignment 01 absent, Assignment 02 present | `first_evidence_assignment_02` | draw first academic evidence from an end-of-year grade/window distribution |
| Assignment 02 absent | `absent_no_update` | observed score is `0`; academic readiness is unchanged |

The Assignment 02 growth model includes grade-level prior shift, course/track context, synthetic instructor effect, section effect, regression-to-mean behavior, growth noise, and observation noise.

The grade-level prior shift is intentionally weak. It comes from public-safe aggregate calibration diagnostics and should not dominate a student's observed present-score history.

## Canonical State

The state object contains:

- students
- teachers
- courses
- sections
- enrollments
- assessment shell metadata
- assignment definitions
- assignment scores currently populated

The state does not contain private calibration details, private paths, real identifiers, real emails, real teacher names, real section labels, raw source rows, or private LMS records.

## Canvas Course Profiles

The generator writes one Canvas-style JSON profile per current-year eligible math course. These files simulate the course-profile artifacts that downstream analysis can join to the all-school assessment gradebook.

Each profile includes:

- course metadata
- synthetic Canvas course ID
- sections for that course
- fake teacher metadata per section
- enrolled synthetic students
- synthetic email join keys

`MATH-BEYOND-CORE` does not receive a current-year profile because it has zero active enrollments in the baseline dataset.

## Validation

The validator checks:

- expected row counts
- one active math enrollment per student
- enrollments reference existing courses, sections, and teachers
- public CSV fields match the current schema
- `Assignment 01` is populated
- `Assignment 02` is populated by the reusable score engine
- Assignments 03-14 are blank
- score bounds are valid
- Assignment 02 presence/absence and academic-profile update rules are coherent
- banned private/source strings do not appear in public artifacts
- Canvas course profiles cover every active enrollment exactly once
