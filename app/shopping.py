from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import date, timedelta
from app.models import ShoppingList, ShoppingListItem, MealPlan, Meal, db
from app.forms import ShoppingListForm, ShoppingListItemForm

shopping_bp = Blueprint('shopping', __name__, url_prefix='/shopping')

def get_week_start(date_obj=None):
    """Get the Monday of the week for a given date"""
    if date_obj is None:
        date_obj = date.today()
    return date_obj - timedelta(days=date_obj.weekday())

def parse_ingredients(ingredients_text):
    """Parse ingredients from meal text (one per line)"""
    lines = ingredients_text.strip().split('\n')
    ingredients = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('-'):
            line = line.lstrip('- ')
        if line:
            ingredients.append(line)
    return ingredients

@shopping_bp.route('/')
@login_required
def index():
    """View shopping lists"""
    if not current_user.household:
        return redirect(url_for('household.create'))

    week_param = request.args.get('week', type=str)

    if week_param:
        try:
            week_start = date.fromisoformat(week_param)
        except (ValueError, AttributeError):
            week_start = get_week_start()
    else:
        week_start = get_week_start()

    shopping_lists = ShoppingList.query.filter_by(
        household_id=current_user.household_id,
        week_start_date=week_start
    ).all()

    # Get next and previous week
    prev_week = week_start - timedelta(days=7)
    next_week = week_start + timedelta(days=7)

    return render_template('shopping/index.html',
                         shopping_lists=shopping_lists,
                         week_start=week_start,
                         prev_week=prev_week,
                         next_week=next_week)

@shopping_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create shopping list"""
    if not current_user.household:
        return redirect(url_for('household.create'))

    week_param = request.args.get('week', type=str)

    if week_param:
        try:
            week_start = date.fromisoformat(week_param)
        except (ValueError, AttributeError):
            week_start = get_week_start()
    else:
        week_start = get_week_start()

    form = ShoppingListForm()
    if form.validate_on_submit():
        shopping_list = ShoppingList(
            household_id=current_user.household_id,
            store_name=form.store_name.data,
            week_start_date=week_start
        )
        db.session.add(shopping_list)
        db.session.commit()
        flash(f'Shopping list "{form.store_name.data}" created!', 'success')
        return redirect(url_for('shopping.view', id=shopping_list.id))

    return render_template('shopping/create.html', form=form, week_start=week_start)

@shopping_bp.route('/<int:id>')
@login_required
def view(id):
    """View shopping list"""
    shopping_list = ShoppingList.query.get_or_404(id)

    if not current_user.household or shopping_list.household_id != current_user.household_id:
        flash('You do not have permission to view this list', 'danger')
        return redirect(url_for('shopping.index'))

    items = shopping_list.items.all()
    completed = sum(1 for item in items if item.is_checked)

    return render_template('shopping/view.html',
                         shopping_list=shopping_list,
                         items=items,
                         completed=completed,
                         total=len(items))

@shopping_bp.route('/<int:id>/add-item', methods=['GET', 'POST'])
@login_required
def add_item(id):
    """Add item to shopping list"""
    shopping_list = ShoppingList.query.get_or_404(id)

    if not current_user.household or shopping_list.household_id != current_user.household_id:
        flash('You do not have permission to edit this list', 'danger')
        return redirect(url_for('shopping.index'))

    form = ShoppingListItemForm()
    if form.validate_on_submit():
        item = ShoppingListItem(
            shopping_list_id=id,
            item_name=form.item_name.data,
            quantity=form.quantity.data or None,
            unit=form.unit.data or None
        )
        db.session.add(item)
        db.session.commit()
        flash('Item added!', 'success')
        return redirect(url_for('shopping.view', id=id))

    return render_template('shopping/add_item.html', form=form, shopping_list=shopping_list)

@shopping_bp.route('/<int:id>/generate', methods=['POST'])
@login_required
def generate_from_meals(id):
    """Generate shopping list items from meal plan"""
    shopping_list = ShoppingList.query.get_or_404(id)

    if not current_user.household or shopping_list.household_id != current_user.household_id:
        return jsonify({'error': 'Permission denied'}), 403

    week_start = shopping_list.week_start_date
    week_end = week_start + timedelta(days=6)

    # Get all meals for the week
    meal_plans = MealPlan.query.filter(
        MealPlan.household_id == current_user.household_id,
        MealPlan.date >= week_start,
        MealPlan.date <= week_end
    ).all()

    # Collect ingredients from meals
    ingredients_set = set()
    for meal_plan in meal_plans:
        if meal_plan.meal:
            ingredients = parse_ingredients(meal_plan.meal.ingredients)
            for ingredient in ingredients:
                ingredients_set.add(ingredient)

    # Add items to shopping list (avoid duplicates)
    existing_items = {item.item_name.lower() for item in shopping_list.items}

    for ingredient in ingredients_set:
        if ingredient.lower() not in existing_items:
            item = ShoppingListItem(
                shopping_list_id=id,
                item_name=ingredient
            )
            db.session.add(item)

    db.session.commit()
    flash(f'Added {len(ingredients_set)} items to shopping list!', 'success')
    return redirect(url_for('shopping.view', id=id))

@shopping_bp.route('/item/<int:item_id>/toggle', methods=['POST'])
@login_required
def toggle_item(item_id):
    """Toggle item completion status"""
    item = ShoppingListItem.query.get_or_404(item_id)
    shopping_list = item.shopping_list

    if shopping_list.user_id != current_user.id:
        return jsonify({'error': 'Permission denied'}), 403

    item.is_checked = not item.is_checked
    db.session.commit()

    return jsonify({'checked': item.is_checked})

@shopping_bp.route('/item/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(item_id):
    """Delete item from shopping list"""
    item = ShoppingListItem.query.get_or_404(item_id)
    shopping_list = item.shopping_list

    if shopping_list.user_id != current_user.id:
        return jsonify({'error': 'Permission denied'}), 403

    list_id = shopping_list.id
    db.session.delete(item)
    db.session.commit()

    return redirect(url_for('shopping.view', id=list_id))

@shopping_bp.route('/item/<int:item_id>/move', methods=['POST'])
@login_required
def move_item(item_id):
    """Move item to another shopping list"""
    item = ShoppingListItem.query.get_or_404(item_id)
    old_list = item.shopping_list

    if old_list.user_id != current_user.id:
        return jsonify({'error': 'Permission denied'}), 403

    target_list_id = request.form.get('target_list_id', type=int)
    target_list = ShoppingList.query.get_or_404(target_list_id)

    if target_list.user_id != current_user.id:
        return jsonify({'error': 'Permission denied'}), 403

    item.shopping_list_id = target_list_id
    db.session.commit()
    flash(f'Item moved to {target_list.store_name}', 'success')

    return redirect(url_for('shopping.view', id=old_list.id))

@shopping_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_list(id):
    """Delete shopping list"""
    shopping_list = ShoppingList.query.get_or_404(id)

    if not current_user.household or shopping_list.household_id != current_user.household_id:
        flash('You do not have permission to delete this list', 'danger')
        return redirect(url_for('shopping.index'))

    db.session.delete(shopping_list)
    db.session.commit()
    flash('Shopping list deleted', 'info')
    return redirect(url_for('shopping.index', week=shopping_list.week_start_date.isoformat()))
