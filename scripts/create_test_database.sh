#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT="$REPO_ROOT/school_task_db"
PYTHON="${PYTHON:-$REPO_ROOT/venv/bin/python}"

STUDENTS_CSV="${1:-$PROJECT_ROOT/data/test_students_7_8_9.csv}"
TASK_BANK_JSON="${2:-$PROJECT_ROOT/data/test_task_bank.json}"
SCENARIO_JSON="${3:-$PROJECT_ROOT/data/test_scenario.json}"

if [[ ! -x "$PYTHON" ]]; then
    echo "Python virtualenv not found or not executable: $PYTHON" >&2
    exit 1
fi

cd "$PROJECT_ROOT"

"$PYTHON" manage.py migrate
"$PYTHON" manage.py load_codifier_oge
"$PYTHON" manage.py load_codifier_ege
"$PYTHON" manage.py load_physics_topics
"$PYTHON" manage.py import_students_csv "$STUDENTS_CSV"
"$PYTHON" manage.py import_tasks \
    "$TASK_BANK_JSON" \
    --mode update \
    --create-groups \
    --create-topics
"$PYTHON" manage.py build_test_scenario "$SCENARIO_JSON"

echo
echo "Test database is ready."
echo "Run: cd \"$PROJECT_ROOT\" && ../venv/bin/python manage.py runserver"
