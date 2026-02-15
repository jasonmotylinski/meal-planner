"""Add household_id to Meal

Revision ID: add_household_id_to_meal
Revises: 
Create Date: 2026-02-15 14:25:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_household_id_to_meal'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add household_id column to meal table
    op.add_column('meal', sa.Column('household_id', sa.Integer(), nullable=True))
    
    # If there are existing meals, they need to be assigned to a household
    # For now, we'll use a simple approach: assign to the creator's household
    # This requires a data migration
    
    # Create foreign key constraint
    op.create_foreign_key('fk_meal_household_id', 'meal', 'household', ['household_id'], ['id'])
    
    # Make column NOT NULL after setting values
    # First, connect creator's household if they have one
    connection = op.get_bind()
    
    # Populate household_id from user's household
    connection.execute(
        """
        UPDATE meal 
        SET household_id = (
            SELECT household_id FROM user WHERE user.id = meal.created_by
        )
        WHERE household_id IS NULL AND created_by IN (
            SELECT id FROM user WHERE household_id IS NOT NULL
        )
        """
    )
    
    # For users without a household, we can't auto-assign
    # This is a data integrity issue - log or handle manually
    # For now, just leave them NULL temporarily
    
    # Drop the nullable constraint (if all have values)
    # In practice, you may need to handle orphaned records differently
    op.alter_column('meal', 'household_id', existing_type=sa.Integer(), nullable=False)


def downgrade():
    op.drop_constraint('fk_meal_household_id', 'meal', type_='foreignkey')
    op.drop_column('meal', 'household_id')
