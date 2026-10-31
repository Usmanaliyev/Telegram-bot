#!/usr/bin/env bash
set -e

git pull
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --noinput
.venv/bin/python -m pytest -q
.venv/bin/python manage.py botcheck
sudo systemctl restart mybot