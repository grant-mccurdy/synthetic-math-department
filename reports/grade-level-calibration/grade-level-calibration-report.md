# Grade-Level Calibration Report

This report summarizes public-safe aggregate calibration diagnostics for the reusable longitudinal score engine.

The private source path is intentionally omitted. Source rows, identifiers, emails, section labels, and exact source rows are not written here.

## Source Pool Summary

| Grade | Nonzero n | Mean | Median | SD | IQR |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 9 | 52 | 46.15 | 46.77 | 18.07 | 23.39 |
| 10 | 62 | 47.61 | 45.16 | 18.31 | 25.80 |
| 11 | 50 | 52.26 | 51.61 | 23.40 | 38.71 |
| 12 | 47 | 56.83 | 51.61 | 24.05 | 41.94 |

## Regression Calibration Summary

| Metric | Value |
| --- | ---: |
| Slope median | 3.5907 |
| Slope mean | 3.6390 |
| Slope 80% interval | [1.9271, 5.2557] |
| Slope 95% interval | [1.1535, 6.2664] |
| P(slope > 0) | 0.9970 |
| R-squared median | 0.0365 |
| Recommended grade prior shift per grade | 1.7953 |

## Interpretation

The recommended grade prior shift is a weak prior input for the longitudinal model. It should not be treated as a direct score formula or as evidence from additional real observations.

Generated calibration distributions are accepted only if repeated same-size samples preserve grade-specific source summaries, quantiles, distribution distances, grade gaps, and regression behavior.
