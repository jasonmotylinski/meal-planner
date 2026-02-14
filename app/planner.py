from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date
from app.models import MealPlan, Meal, db
from app.forms import MealPlanForm

planner_bp = Blueprint('planner', __name__, url_prefix='/planner')

def get_week_start(date_obj=None):
    """Get the Monday of the week for a given date"""
    if date_obj is None:
        date_obj = date.today()
    return date_obj - timedelta(days=date_obj.weekday())

def get_week_dates(week_start):
    """Get all dates for a week starting from Monday"""
    return [week_start + timedelta(days=i) for i in range(7)]

@planner_bp.route('/')
@login_required
def index():
    """View weekly meal plan"""
    if not current_user.household:
        return redirect(url_for('household.create'))

    week_param = request.args.get('week', type=str)

    if week_param:
        try:
            week_start = datetime.strptime(week_param, '%Y-%m-%d').date()
        except ValueError:
            week_start = get_week_start()
    else:
        week_start = get_week_start()

    week_dates = get_week_dates(week_start)
    meal_types = ['dinner']  # UI only shows dinner, but backend supports all types

    # Get meal plans for the week (from household)
    meal_plans = {}
    for day in week_dates:
        meal_plans[day] = {}
        for meal_type in meal_types:
            plan = MealPlan.query.filter_by(
                household_id=current_user.household_id,
                date=day,
                meal_type=meal_type
            ).first()
            meal_plans[day][meal_type] = plan

    # Get next and previous week
    prev_week = week_start - timedelta(days=7)
    next_week = week_start + timedelta(days=7)

    return render_template('planner/index.html',
                         week_start=week_start,
                         week_dates=week_dates,
                         meal_types=meal_types,
                         meal_plans=meal_plans,
                         prev_week=prev_week,
                         next_week=next_week,
                         today=date.today())

@planner_bp.route('/<date_str>/<meal_type>', methods=['GET', 'POST'])
@login_required
def set_meal(date_str, meal_type):
    """Set meal for a specific day and meal type"""
    if not current_user.household:
        return redirect(url_for('household.create'))

    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        flash('Invalid date', 'danger')
        return redirect(url_for('planner.index'))

    # Check if meal_id is passed as query parameter (quick add from recipe view)
    quick_meal_id = request.args.get('meal_id', type=int)

    if meal_type not in ['breakfast', 'lunch', 'dinner']:
        flash('Invalid meal type', 'danger')
        return redirect(url_for('planner.index'))

    # Handle quick add from recipe view
    if quick_meal_id:
        meal_plan = MealPlan.query.filter_by(
            household_id=current_user.household_id,
            date=target_date,
            meal_type=meal_type
        ).first()

        if not meal_plan:
            meal_plan = MealPlan(
                household_id=current_user.household_id,
                date=target_date,
                meal_type=meal_type
            )

        meal_plan.meal_id = quick_meal_id
        meal_plan.custom_entry = None
        db.session.add(meal_plan)
        db.session.commit()
        flash('Meal added to your plan!', 'success')
        week_start = get_week_start(target_date)
        return redirect(url_for('planner.index', week=week_start.isoformat()))

    form = MealPlanForm()

    # Populate meal choices
    meals = Meal.query.order_by(Meal.name).all()
    form.meal_id.choices = [(0, '-- None --')] + [(m.id, m.name) for m in meals]

    if form.validate_on_submit():
        # Get or create meal plan entry (from household)
        meal_plan = MealPlan.query.filter_by(
            household_id=current_user.household_id,
            date=target_date,
            meal_type=meal_type
        ).first()

        if not meal_plan:
            meal_plan = MealPlan(
                household_id=current_user.household_id,
                date=target_date,
                meal_type=meal_type
            )

        # Set either meal or custom entry
        if form.meal_id.data and form.meal_id.data != 0:
            meal_plan.meal_id = form.meal_id.data
            meal_plan.custom_entry = None
        elif form.custom_entry.data:
            meal_plan.meal_id = None
            meal_plan.custom_entry = form.custom_entry.data
        else:
            # Delete if neither meal nor custom entry
            if meal_plan.id:
                db.session.delete(meal_plan)
            db.session.commit()
            flash('Meal removed', 'info')
            return redirect(request.referrer or url_for('planner.index'))

        db.session.add(meal_plan)
        db.session.commit()
        flash('Meal updated successfully!', 'success')
        # Get the week start for the target date
        week_start = get_week_start(target_date)
        return redirect(url_for('planner.index', week=week_start.isoformat()))

    # Pre-fill form
    existing = MealPlan.query.filter_by(
        household_id=current_user.household_id,
        date=target_date,
        meal_type=meal_type
    ).first()

    if existing:
        if existing.meal_id:
            form.meal_id.data = existing.meal_id
        else:
            form.custom_entry.data = existing.custom_entry

    return render_template('planner/set_meal.html',
                         form=form,
                         date=target_date,
                         meal_type=meal_type)

@planner_bp.route('/<date_str>/<meal_type>/delete', methods=['POST'])
@login_required
def delete_meal(date_str, meal_type):
    """Delete meal from plan"""
    if not current_user.household:
        return redirect(url_for('household.create'))

    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid date'}), 400

    meal_plan = MealPlan.query.filter_by(
        household_id=current_user.household_id,
        date=target_date,
        meal_type=meal_type
    ).first()

    if meal_plan:
        db.session.delete(meal_plan)
        db.session.commit()
        flash('Meal removed', 'info')

    return redirect(request.referrer or url_for('planner.index'))
