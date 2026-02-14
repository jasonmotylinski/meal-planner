"""
Example: Claude Recipe Importer using Tool Use
Shows how Claude can discover and use the recipe API via tool_use

This demonstrates:
1. Claude calling GET /api/recipes/schema to discover fields
2. Claude extracting recipe data
3. Claude calling POST /api/recipes to submit the recipe
"""

import json
import urllib.request
from typing import Any

# Example usage - would be called by Claude via tool_use
API_BASE = "http://localhost:5000"
API_ENDPOINT = f"{API_BASE}/api/recipes"

TOOLS = [
    {
        "name": "get_recipe_schema",
        "description": "Get the JSON schema for creating recipes. Shows required and optional fields.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "extract_recipe_from_html",
        "description": "Extract recipe data from HTML page using structured data (JSON-LD)",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL of recipe blog post"
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "submit_recipe",
        "description": "Submit extracted recipe to the meal planner API",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Recipe name"},
                "description": {"type": "string", "description": "Brief description"},
                "ingredients": {"type": "string", "description": "Ingredients, one per line"},
                "instructions": {"type": "string", "description": "Instructions, one step per line"},
                "category": {"type": "string", "description": "Recipe category"},
                "source_url": {"type": "string", "description": "Source URL"}
            },
            "required": ["name", "ingredients", "instructions"]
        }
    }
]


def get_recipe_schema() -> dict:
    """Get the recipe schema from API"""
    try:
        req = urllib.request.Request(
            f"{API_ENDPOINT}/schema",
            headers={"User-Agent": "Claude-RecipeImporter/1.0"}
        )
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}


def extract_recipe_from_html(url: str) -> dict:
    """Extract recipe from URL using recipe_importer"""
    try:
        from app.recipe_importer import import_recipe_from_url
        result = import_recipe_from_url(url)
        return result or {"error": "Could not extract recipe from URL"}
    except Exception as e:
        return {"error": str(e)}


def submit_recipe(name: str, ingredients: str, instructions: str,
                 description: str = "", category: str = None,
                 source_url: str = None) -> dict:
    """Submit recipe to API"""
    try:
        payload = json.dumps({
            "name": name,
            "description": description,
            "ingredients": ingredients,
            "instructions": instructions,
            "category": category,
            "source_url": source_url
        })

        # In a real scenario, you'd have authentication
        # For demo, we'd need to be logged in via session
        req = urllib.request.Request(
            API_ENDPOINT,
            data=payload.encode('utf-8'),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Claude-RecipeImporter/1.0"
            },
            method='POST'
        )

        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))

    except urllib.error.HTTPError as e:
        if e.code == 401:
            return {"error": "Authentication required. User must be logged in."}
        error_data = e.read().decode('utf-8')
        return {"error": f"API Error: {error_data}"}
    except Exception as e:
        return {"error": str(e)}


def process_tool_call(tool_name: str, tool_input: dict) -> Any:
    """Process tool calls from Claude"""
    if tool_name == "get_recipe_schema":
        return get_recipe_schema()
    elif tool_name == "extract_recipe_from_html":
        return extract_recipe_from_html(tool_input.get("url"))
    elif tool_name == "submit_recipe":
        return submit_recipe(
            name=tool_input.get("name"),
            description=tool_input.get("description", ""),
            ingredients=tool_input.get("ingredients"),
            instructions=tool_input.get("instructions"),
            category=tool_input.get("category"),
            source_url=tool_input.get("source_url")
        )
    else:
        return {"error": f"Unknown tool: {tool_name}"}


def claude_extract_and_save_recipe(recipe_url: str):
    """
    Example: What Claude would do to extract and save a recipe

    In production, Claude would:
    1. Call get_recipe_schema to learn what fields are needed
    2. Call extract_recipe_from_html to get recipe data
    3. Call submit_recipe to save to the meal planner
    """

    print("=" * 70)
    print("CLAUDE RECIPE IMPORT WORKFLOW")
    print("=" * 70)

    # Step 1: Learn the schema
    print("\n[1] Learning recipe schema...")
    schema = get_recipe_schema()
    print(f"✓ Schema retrieved")
    print(f"  Required fields: {schema.get('required', [])}")

    # Step 2: Extract recipe
    print(f"\n[2] Extracting recipe from: {recipe_url}")
    recipe = extract_recipe_from_html(recipe_url)
    if recipe.get("error"):
        print(f"✗ Extraction failed: {recipe.get('error')}")
        return
    print(f"✓ Recipe extracted: {recipe.get('name')}")

    # Step 3: Submit to API
    print(f"\n[3] Submitting to API...")
    result = submit_recipe(
        name=recipe.get("name"),
        description=recipe.get("description"),
        ingredients=recipe.get("ingredients"),
        instructions=recipe.get("instructions"),
        source_url=recipe_url
    )

    if result.get("success"):
        print(f"✓ Recipe saved: {result.get('message')}")
        if result.get("recipe"):
            print(f"  Recipe ID: {result['recipe'].get('id')}")
    else:
        print(f"✗ Failed: {result.get('error')}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    print("CLAUDE RECIPE IMPORTER - TOOL USE EXAMPLE")
    print("=" * 70)
    print("\nThis script demonstrates how Claude can use the Meal Planner API:")
    print("1. GET /api/recipes/schema - Discover recipe fields")
    print("2. POST /api/recipes - Submit recipe data")
    print("\nTools available to Claude:")
    for tool in TOOLS:
        print(f"  - {tool['name']}: {tool['description']}")

    print("\n" + "=" * 70)
    print("EXAMPLE WORKFLOW:")
    print("=" * 70)

    # Test with a real recipe URL
    # Note: This requires the app to be running
    test_url = "https://www.inspiredtaste.net/7179/sweet-and-spicy-oven-baked-ribs/"

    print(f"\nWould execute for URL: {test_url}")
    print("(Requires app running on localhost:5000 and user logged in)")
