"""
Populate meals from TheMealDB API
https://www.themealdb.com/api.php
"""

import urllib.request
import json
from app import create_app
from app.models import db, Meal, User

API_BASE = "https://www.themealdb.com/api/json/v1/1"

def fetch_meals_by_category(category):
    """Fetch all meals for a given category"""
    url = f"{API_BASE}/filter.php?c={category}"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data.get('meals', [])
    except Exception as e:
        print(f"Error fetching category {category}: {e}")
        return []

def fetch_meal_details(meal_id):
    """Fetch detailed information for a meal"""
    url = f"{API_BASE}/lookup.php?i={meal_id}"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            meals = data.get('meals', [])
            return meals[0] if meals else None
    except Exception as e:
        print(f"Error fetching meal {meal_id}: {e}")
        return None

def extract_ingredients(meal_details):
    """Extract ingredients from meal details"""
    ingredients = []
    for i in range(1, 21):  # TheMealDB has up to 20 ingredients
        ingredient = meal_details.get(f'strIngredient{i}')
        measure = meal_details.get(f'strMeasure{i}')
        if ingredient and ingredient.strip():
            if measure and measure.strip():
                ingredients.append(f"{measure} {ingredient}".strip())
            else:
                ingredients.append(ingredient.strip())
    return '\n'.join(ingredients)

def populate_meals_from_mealsdb():
    """Main function to populate meals"""
    app = create_app()

    with app.app_context():
        # Get or create default user for ownership
        default_user = User.query.first()
        if not default_user:
            print("No users found. Create a user first.")
            return

        # List of categories to fetch
        categories = [
            'Seafood', 'Breakfast', 'Pasta', 'Dessert', 'Chicken',
            'Beef', 'Vegetarian', 'Vegan', 'Side'
        ]

        total_added = 0

        for category in categories:
            print(f"\nFetching meals from category: {category}")
            meals_list = fetch_meals_by_category(category)
            print(f"  Found {len(meals_list)} meals")

            for meal_item in meals_list:
                meal_id = meal_item['idMeal']
                meal_name = meal_item['strMeal']
                meal_image = meal_item.get('strMealThumb')

                # Check if already exists
                existing = Meal.query.filter_by(name=meal_name).first()
                if existing:
                    print(f"  ⊘ {meal_name} (already exists)")
                    continue

                # Fetch detailed information
                print(f"  ⟳ Fetching: {meal_name}...", end='')
                details = fetch_meal_details(meal_id)

                if not details:
                    print(" failed")
                    continue

                # Extract data
                ingredients = extract_ingredients(details)
                instructions = details.get('strInstructions', '').strip()

                # Create meal
                meal = Meal(
                    name=meal_name,
                    description=f"Recipe from TheMealDB",
                    category=category,
                    ingredients=ingredients,
                    instructions=instructions,
                    image_filename=meal_image,  # Store URL directly
                    created_by=default_user.id
                )

                db.session.add(meal)
                total_added += 1
                print(f" ✓")

                # Commit every 10 meals to avoid timeout
                if total_added % 10 == 0:
                    db.session.commit()

        # Final commit
        db.session.commit()

        print(f"\n{'='*60}")
        print(f"Successfully added {total_added} meals from TheMealDB!")
        print(f"{'='*60}")

if __name__ == '__main__':
    populate_meals_from_mealsdb()
