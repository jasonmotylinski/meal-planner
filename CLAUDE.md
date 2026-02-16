# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run dev server (http://localhost:8888)
python run.py

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 run:app

# Database migrations after model changes
export FLASK_APP=run.py
flask db migrate -m "description"
flask db upgrade
flask db downgrade  # rollback

# Background job (recipe processing via Claude API)
python jobs/process_pending_recipes.py
```

## Architecture

Flask app using the **application factory pattern** (`app/__init__.py` → `create_app()`). SQLite database with SQLAlchemy ORM and Flask-Migrate for schema versioning.

### Blueprints

| Blueprint | Prefix | Module | Purpose |
|-----------|--------|--------|---------|
| `auth_bp` | `/` | `auth.py` | Login, register, logout |
| `main_bp` | `/` | `main.py` | Landing page, dashboard |
| `meals_bp` | `/meals` | `meals.py` | Recipe CRUD, favorites, import |
| `planner_bp` | `/planner` | `planner.py` | Weekly meal planning |
| `shopping_bp` | `/shopping` | `shopping.py` | Shopping lists and items |
| `household_bp` | `/household` | `household.py` | Household creation, invites |
| `api_bp` | `/api/recipes` | `api.py` | JSON API for external tools |
| `api_keys_bp` | `/api-keys` | `api_keys.py` | API key management |
| `settings_bp` | `/settings` | `settings.py` | User settings |

### Key Models (`app/models.py`)

- **User** → belongs to Household, has Meals, ApiKeys
- **Household** → has many Users, Meals, MealPlans, ShoppingLists
- **Meal** → recipe with ingredients, instructions, image, source_url
- **MealPlan** → links a Meal (or custom entry/URL) to a date + meal_type for a Household
- **ShoppingList** / **ShoppingListItem** → per-household shopping with checkable items
- **HouseholdInvite** → secure token-based invites (256-bit, 7-day expiry)

### URL-First Workflow

Users paste recipe URLs directly into the planner (`planner.py` → `set_meal()`). The `recipe_importer.py` module extracts structured data via schema.org JSON-LD. If parsing fails, the URL is saved with a fallback label. Background jobs in `jobs/` use the Claude API for more complex extraction.

### Frontend

Vanilla JS with no framework. Custom CSS design system ("Farmers Market Warmth") in `app/static/css/`. Key colors: Sage Green `#87A878`, Terracotta `#E07A5F`, Honey Gold `#F4A261`, Cream `#F8F5F0`. Templates use Jinja2 with `base.html` as the layout root.

### Config & Environment

`config.py` loads from `.env` via python-dotenv. Required env vars:
- `SECRET_KEY` — Flask session secret
- `ANTHROPIC_API_KEY` — for Claude-based recipe parsing (optional, used by jobs)
- `FLASK_ENV` — `development` (default), `testing`, `production`
