#!/usr/bin/env bash
cd /var/projects/meal-planner
source venv/bin/activate

python jobs/process_pending_recipes.py