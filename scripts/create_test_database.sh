#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT="$REPO_ROOT/school_task_db"
PYTHON="${PYTHON:-$REPO_ROOT/venv/bin/python}"

STUDENTS_CSV="${1:-$PROJECT_ROOT/data/test_students_7_8_9.csv}"
TASK_BANK_JSON="${2:-$PROJECT_ROOT/data/test_task_bank.json}"
SCENARIO_JSON="${3:-$PROJECT_ROOT/data/test_scenario.json}"
TEST_ADMIN_USERNAME="${TEST_ADMIN_USERNAME:-admin}"
TEST_ADMIN_PASSWORD="${TEST_ADMIN_PASSWORD:-admin}"

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
TEST_ADMIN_USERNAME="$TEST_ADMIN_USERNAME" \
TEST_ADMIN_PASSWORD="$TEST_ADMIN_PASSWORD" \
"$PYTHON" manage.py shell -c '
import os
from django.contrib.auth import get_user_model

user_model = get_user_model()
username = os.environ["TEST_ADMIN_USERNAME"]
password = os.environ["TEST_ADMIN_PASSWORD"]
user, _ = user_model.objects.get_or_create(username=username)
user.is_staff = True
user.is_superuser = True
user.set_password(password)
user.save()
print(f"Test admin is ready: {username}")
'

echo
echo "Test database is ready."
echo "Admin: $TEST_ADMIN_USERNAME / $TEST_ADMIN_PASSWORD"
echo "Run: cd \"$PROJECT_ROOT\" && ../venv/bin/python manage.py runserver"
