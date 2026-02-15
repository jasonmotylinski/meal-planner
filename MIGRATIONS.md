# Database Migrations Guide

This project uses **Flask-Migrate** (built on Alembic) to manage database schema changes safely in production.

## Setup (One-time)

1. **Install Flask-Migrate:**
```bash
pip install -r requirements.txt
```

2. **Initialize migrations folder:**
```bash
export FLASK_APP=run.py
flask db init
```

This creates a `migrations/` folder with Alembic configuration.

## Workflow for Schema Changes

### 1. Modify Your Models
Edit `app/models.py` with your new fields/tables.

### 2. Generate Migration
```bash
flask db migrate -m "Describe your change"
```

Example:
```bash
flask db migrate -m "Add source_url to MealPlan"
```

This auto-detects changes and creates a migration file in `migrations/versions/`.

### 3. Review the Migration
Check `migrations/versions/XXXX_describe_change.py` to ensure it looks correct. You can edit it if needed.

### 4. Apply Migration (Development)
```bash
flask db upgrade
```

Applies the migration to your local database.

### 5. Deploy to Production

**First time:**
```bash
# On production server
pip install -r requirements.txt
flask db upgrade
```

**For subsequent changes:**
- Commit your models.py + migration file to git
- Deploy code
- SSH to production and run:
```bash
flask db upgrade
```

No need to delete/recreate the database! ✅

## Common Commands

```bash
# See current migration status
flask db current

# See all migrations
flask db history

# See pending migrations
flask db heads

# Rollback last migration (careful in production!)
flask db downgrade

# View SQL that will be executed (preview)
flask db upgrade --sql
```

## Best Practices

✅ **DO:**
- Always review migration files before applying
- Test migrations on a copy of production data first
- Keep migration files in git
- Run `flask db migrate` after every model change
- Use descriptive migration names

❌ **DON'T:**
- Manually edit database schema outside migrations
- Delete migration files
- Edit migration files unless you know Alembic well
- Use `db.create_all()` in production (use migrations instead)

## If Something Goes Wrong

**Rollback to previous state:**
```bash
flask db downgrade
```

**Manually fix a broken migration:**
1. Edit the migration file in `migrations/versions/`
2. Run `flask db upgrade` again
3. Test thoroughly

**Reset everything (dev only):**
```bash
rm -rf migrations/
rm your_database.db
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## Links

- [Flask-Migrate Docs](https://flask-migrate.readthedocs.io/)
- [Alembic Docs](https://alembic.sqlalchemy.org/) (advanced)
