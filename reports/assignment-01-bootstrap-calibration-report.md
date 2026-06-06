# Assignment 01 Public Calibration Report

## Summary

Assignment 01 is the beginning-of-year assessment in the synthetic math department model.

The public generator uses grade-specific public-safe score anchors and jittered sampling to create present-student scores. It then applies an independent attendance process. Students who are absent receive an observed score of `0`.

## Public-Safe Method

The generator does not read private source files. It uses generalized calibration anchors stored in the public generator code.

Generation order:

```text
student grade level
-> present-student score draw from grade-specific anchors
-> attendance category draw
-> attendance probability draw
-> present/absent draw
-> observed Assignment 01 score
```

If present:

```text
observed score = present-student synthetic score
```

If absent:

```text
observed score = 0
```

## Interpretation

Under the current model, a zero on Assignment 01 is a non-participation/admin outcome, not evidence of academic readiness.

Assignment 02 is populated by the reusable longitudinal score engine as the end-of-year transition. Assignments 03-14 remain blank until later transitions are implemented and validated.

## Validation

Run:

```bash
make all
```

The validator confirms:

- Assignment 01 is populated for every synthetic student
- score bounds are within `[0, 100]`
- Assignment 02 is populated for every synthetic student
- Assignments 03-14 remain blank
- public artifacts do not contain banned private/source strings
