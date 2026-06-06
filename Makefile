.PHONY: all generate validate calibrate-grade-level

PYTHON ?= python3

all: generate validate

generate:
	$(PYTHON) scripts/generate_synthetic_math_department.py

validate:
	$(PYTHON) scripts/validate_synthetic_math_department.py

calibrate-grade-level:
	@test -n "$(SOURCE_GRADEBOOK)" || (echo "Set SOURCE_GRADEBOOK=/path/to/private/gradebook.csv"; exit 1)
	$(PYTHON) scripts/calibrate_grade_level_effect.py --source-gradebook "$(SOURCE_GRADEBOOK)"
