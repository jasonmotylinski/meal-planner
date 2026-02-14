#!/usr/bin/env bash
cd /var/projects/meal-planner
source venv/bin/activate
exec gunicorn --bind unix:/run/meal-planner.sock run:app