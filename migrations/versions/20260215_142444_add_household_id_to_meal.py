"""Add household_id to Meal

Revision ID: add_household_id_to_meal
Revises:
Create Date: 2026-02-15 14:25:00.000000

"""

# revision identifiers, used by Alembic.
revision = 'add_household_id_to_meal'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # This migration marks the schema state where meal.household_id was added
    # The column already exists in the database from earlier manual changes
    # This is a no-op migration that just tracks the schema version
    pass


def downgrade():
    # No-op for downgrade as well (schema already has the column)
    pass
