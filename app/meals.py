from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.models import Meal, db, meal_favorites
from app.forms import MealForm, RecipeImportForm
from app.utils import save_picture, delete_picture, save_picture_from_url
from app.recipe_importer import import_recipe_from_url, extract_domain_name
from datetime import datetime, timedelta, date

meals_bp = Blueprint('meals', __name__, url_prefix='/meals')

@meals_bp.route('/')
@login_required
def library():
    """View meal library with search and filter"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    category = request.args.get('category', '', type=str)

    query = Meal.query

    if search:
        query = query.filter(Meal.name.ilike(f'%{search}%') | Meal.description.ilike(f'%{search}%'))

    if category:
        query = query.filter(Meal.category == category)

    meals = query.order_by(Meal.created_at.desc()).paginate(page=page, per_page=12)

    # Get all available categories for filter UI
    available_categories = db.session.query(Meal.category).distinct().filter(Meal.category.isnot(None)).all()
    available_categories = sorted([c[0] for c in available_categories if c[0]])

    return render_template('meals/library.html', meals=meals, search=search, category=category, available_categories=available_categories)

@meals_bp.route('/favorites')
@login_required
def favorites():
    """View favorite meals"""
    page = request.args.get('page', 1, type=int)
    meals = current_user.favorites.paginate(page=page, per_page=12)
    return render_template('meals/favorites.html', meals=meals)

@meals_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new meal"""
    form = MealForm()
    if form.validate_on_submit():
        image_filename = None
        if form.image.data:
            image_filename = save_picture(form.image.data)

        meal = Meal(
            name=form.name.data,
            description=form.description.data,
            category=form.category.data or None,
            ingredients=form.ingredients.data,
            instructions=form.instructions.data,
            image_filename=image_filename,
            created_by=current_user.id
        )
        db.session.add(meal)
        db.session.commit()
        flash('Meal created successfully!', 'success')
        return redirect(url_for('meals.view', id=meal.id))

    return render_template('meals/create.html', form=form)

@meals_bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_recipe():
    """Import a recipe from a URL"""
    form = RecipeImportForm()

    if form.validate_on_submit():
        url = form.url.data

        try:
            # Extract recipe from URL
            flash('🔄 Fetching recipe from URL...', 'info')
            recipe_data = import_recipe_from_url(url)

            if not recipe_data:
                flash('Could not extract recipe from that URL. Try manually adding it instead.', 'warning')
                return render_template('meals/import.html', form=form)

            # Download image if available
            image_filename = None
            if recipe_data.get('image_url'):
                image_filename = save_picture_from_url(recipe_data['image_url'])

            # Create meal with imported data
            meal = Meal(
                name=recipe_data.get('name', 'Imported Recipe'),
                description=recipe_data.get('description', ''),
                category=recipe_data.get('category'),  # Some recipes may have category
                ingredients=recipe_data.get('ingredients', ''),
                instructions=recipe_data.get('instructions', ''),
                image_filename=image_filename,
                source_url=url,
                source_name=extract_domain_name(url),
                created_by=current_user.id
            )

            db.session.add(meal)
            db.session.commit()

            flash('✨ Recipe imported successfully!', 'success')
            return redirect(url_for('meals.view', id=meal.id))

        except Exception as e:
            flash(f'Error importing recipe: {str(e)}', 'error')
            return render_template('meals/import.html', form=form)

    return render_template('meals/import.html', form=form)

@meals_bp.route('/<int:id>')
@login_required
def view(id):
    """View a single meal"""
    meal = Meal.query.get_or_404(id)
    is_favorite = current_user.favorites.filter(meal_favorites.c.meal_id == id).first() is not None
    is_owner = meal.created_by == current_user.id

    # Get today's date and next 7 days for meal planning
    today = date.today()
    week_dates = [today + timedelta(days=i) for i in range(7)]

    return render_template('meals/view.html', meal=meal, is_favorite=is_favorite, is_owner=is_owner,
                         today=today, week_dates=week_dates)

@meals_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit a meal"""
    meal = Meal.query.get_or_404(id)

    if meal.created_by != current_user.id:
        abort(403)

    form = MealForm()
    if form.validate_on_submit():
        meal.name = form.name.data
        meal.description = form.description.data
        meal.category = form.category.data or None
        meal.ingredients = form.ingredients.data
        meal.instructions = form.instructions.data

        if form.image.data:
            delete_picture(meal.image_filename)
            meal.image_filename = save_picture(form.image.data)

        db.session.commit()
        flash('Meal updated successfully!', 'success')
        return redirect(url_for('meals.view', id=meal.id))

    elif request.method == 'GET':
        form.name.data = meal.name
        form.description.data = meal.description
        form.category.data = meal.category or ''
        form.ingredients.data = meal.ingredients
        form.instructions.data = meal.instructions

    return render_template('meals/edit.html', form=form, meal=meal)

@meals_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete a meal"""
    meal = Meal.query.get_or_404(id)

    if meal.created_by != current_user.id:
        abort(403)

    delete_picture(meal.image_filename)
    db.session.delete(meal)
    db.session.commit()
    flash('Meal deleted successfully!', 'success')
    return redirect(url_for('meals.library'))

@meals_bp.route('/<int:id>/favorite', methods=['POST'])
@login_required
def toggle_favorite(id):
    """Add or remove meal from favorites"""
    meal = Meal.query.get_or_404(id)
    is_favorite = current_user.favorites.filter(meal_favorites.c.meal_id == id).first() is not None

    if is_favorite:
        current_user.favorites.remove(meal)
        flash('Removed from favorites', 'info')
    else:
        current_user.favorites.append(meal)
        flash('Added to favorites', 'success')

    db.session.commit()
    return redirect(request.referrer or url_for('meals.library'))
