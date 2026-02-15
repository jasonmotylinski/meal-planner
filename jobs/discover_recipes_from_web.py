"""
Discover and import new recipes from the web
Uses curated popular recipe sites and specific recipe URLs
"""

import urllib.request
import json
import re
from app import create_app
from app.models import db, Meal
from app.recipe_importer import import_recipe_from_url, extract_domain_name

# Popular recipe collections to explore
RECIPE_SOURCES = {
    'inspiredtaste': [
        'https://www.inspiredtaste.net/7179/sweet-and-spicy-oven-baked-ribs/',
        'https://www.inspiredtaste.net/23934/honey-garlic-salmon/',
        'https://www.inspiredtaste.net/24014/caprese-salad/',
        'https://www.inspiredtaste.net/25564/grilled-lemon-chicken/',
    ],
    'budgetbytes': [
        'https://www.budgetbytes.com/chickpea-curry/',
        'https://www.budgetbytes.com/beef-fried-rice/',
        'https://www.budgetbytes.com/teriyaki-chicken/',
    ],
    'thepioneerwoman': [
        'https://www.thepioneerwoman.com/food-cooking/recipes/a11050/30-minute-dinners/',
        'https://www.thepioneerwoman.com/food-cooking/recipes/a11082/perfect-pot-roast/',
    ],
}

def recipe_exists_in_db(recipe_name, source_url):
    """Check if recipe already exists in database"""
    # Check by exact name
    if Meal.query.filter_by(name=recipe_name).first():
        return True

    # Check by source URL
    if Meal.query.filter_by(source_url=source_url).first():
        return True

    return False

def import_from_url(url, default_user):
    """Import a single recipe from URL"""
    try:
        # Import recipe
        recipe_data = import_recipe_from_url(url)

        if not recipe_data:
            return False, "No recipe data extracted"

        recipe_name = recipe_data.get('name', '').strip()
        if not recipe_name:
            return False, "No recipe name"

        # Check if already exists
        if recipe_exists_in_db(recipe_name, url):
            return False, "Already in database"

        # Create meal
        meal = Meal(
            name=recipe_name,
            description=recipe_data.get('description', ''),
            ingredients=recipe_data.get('ingredients', ''),
            instructions=recipe_data.get('instructions', ''),
            image_filename=recipe_data.get('image_url'),
            source_url=url,
            source_name=extract_domain_name(url),
            household_id=default_user.household_id,
            created_by=default_user.id
        )

        db.session.add(meal)
        db.session.commit()

        return True, recipe_name

    except Exception as e:
        return False, str(e)[:50]

def discover_and_import_recipes():
    """Main function to discover and import new recipes"""
    app = create_app()

    with app.app_context():
        # Get default user
        from app.models import User
        default_user = User.query.first()
        if not default_user:
            print("No users found. Create a user first.")
            return

        if not default_user.household_id:
            print(f"Default user '{default_user.username}' is not part of a household. Please join a household first.")
            return

        total_imported = 0
        total_checked = 0
        skipped_reasons = {}

        print("=" * 70)
        print("DISCOVERING RECIPES FROM POPULAR SITES")
        print("=" * 70)

        for source, urls in RECIPE_SOURCES.items():
            print(f"\nSource: {source.upper()}")
            print("-" * 70)

            for url in urls:
                total_checked += 1
                print(f"  {url[:55]:55} ", end='')

                success, message = import_from_url(url, default_user)

                if success:
                    print(f"✓ IMPORTED: {message[:30]}")
                    total_imported += 1
                else:
                    print(f"⊘ {message}")
                    skipped_reasons[message] = skipped_reasons.get(message, 0) + 1

        print("\n" + "=" * 70)
        print("DISCOVERY COMPLETE")
        print("=" * 70)
        print(f"Checked: {total_checked} URLs")
        print(f"Imported: {total_imported} new recipes")
        print(f"\nSkip reasons:")
        for reason, count in sorted(skipped_reasons.items(), key=lambda x: -x[1]):
            print(f"  - {reason}: {count}")
        print("=" * 70)

if __name__ == '__main__':
    discover_and_import_recipes()
