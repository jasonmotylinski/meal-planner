#!/usr/bin/env python
"""
Script to automatically categorize existing recipes based on name and description.
Run this from the project root: python categorize_recipes.py
"""

from app import create_app
from app.models import db, Meal

def categorize_meal(meal_name, meal_description):
    """
    Determine category based on meal name and description.
    Returns the category string or None if no match.
    """
    text = f"{meal_name} {meal_description}".lower()

    # Category keywords mapping
    categories = {
        'Chicken': ['chicken', 'poultry'],
        'Beef': ['beef', 'steak', 'ground beef', 'burger', 'brisket', 'roast'],
        'Pork': ['pork', 'ham', 'bacon', 'sausage', 'ribs'],
        'Seafood': ['fish', 'salmon', 'tuna', 'shrimp', 'seafood', 'crab', 'lobster', 'clams'],
        'Pasta': ['pasta', 'noodle', 'spaghetti', 'fettuccine', 'penne', 'lasagna', 'ravioli'],
        'Soup': ['soup', 'broth', 'chowder', 'bisque'],
        'Salad': ['salad', 'greens', 'lettuce'],
        'Side': ['side', 'side dish', 'vegetable', 'potato', 'rice', 'beans', 'corn', 'broccoli'],
        'Dessert': ['dessert', 'cake', 'pie', 'brownie', 'cookie', 'candy', 'chocolate', 'ice cream', 'pudding', 'cheesecake'],
        'Breakfast': ['breakfast', 'pancake', 'waffle', 'egg', 'omelet', 'hash brown', 'cereal', 'oatmeal', 'toast'],
        'Vegetarian': ['vegetarian', 'veggie', 'vegetable', 'tofu', 'tempeh', 'bean', 'lentil'],
        'Vegan': ['vegan'],
    }

    # Check keywords in order of priority
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in text:
                return category

    return None


def categorize_meals():
    """Categorize all meals without categories"""
    app = create_app()

    with app.app_context():
        # Get all meals without categories
        meals_to_categorize = Meal.query.filter(
            (Meal.category == None) | (Meal.category == '')
        ).all()

        print(f"Found {len(meals_to_categorize)} recipes without categories.")
        print("Analyzing recipes...\n")

        categorized = 0
        by_category = {}

        for meal in meals_to_categorize:
            category = categorize_meal(meal.name, meal.description or "")

            if category:
                meal.category = category
                categorized += 1
                by_category[category] = by_category.get(category, 0) + 1
                print(f"✓ {meal.name:<50} → {category}")
            else:
                print(f"⊘ {meal.name:<50} → (no category)")

        # Save to database
        if categorized > 0:
            db.session.commit()
            print(f"\n{'='*70}")
            print(f"✓ Successfully categorized {categorized} recipes!\n")
            print("Summary by category:")
            for category in sorted(by_category.keys()):
                print(f"  • {category}: {by_category[category]} recipes")
            print(f"{'='*70}")
        else:
            print("\nNo recipes needed categorization.")


if __name__ == '__main__':
    categorize_meals()
