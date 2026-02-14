from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import User, Household, db

household_bp = Blueprint('household', __name__, url_prefix='/household')

@household_bp.route('/')
@login_required
def index():
    """View household and members"""
    if not current_user.household:
        return render_template('household/create.html')

    household = current_user.household
    members = household.members.all()

    return render_template('household/index.html', household=household, members=members)

@household_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new household"""
    if current_user.household:
        flash('You are already part of a household', 'info')
        return redirect(url_for('household.index'))

    if request.method == 'POST':
        household_name = request.form.get('household_name', '').strip()

        if not household_name:
            flash('Please enter a household name', 'danger')
            return redirect(url_for('household.create'))

        household = Household(name=household_name, created_by=current_user.id)
        db.session.add(household)
        db.session.flush()  # Get the household ID without committing
        current_user.household_id = household.id
        db.session.commit()

        flash(f'Household "{household_name}" created! Share your invite code with your partner.', 'success')
        return redirect(url_for('household.index'))

    return render_template('household/create.html')

@household_bp.route('/invite', methods=['GET', 'POST'])
@login_required
def invite():
    """Generate invite link/code"""
    if not current_user.household:
        flash('You must create a household first', 'danger')
        return redirect(url_for('household.create'))

    household = current_user.household

    return render_template('household/invite.html', household=household)

@household_bp.route('/join/<int:household_id>', methods=['POST'])
@login_required
def join(household_id):
    """Join a household via invite link"""
    if current_user.household:
        flash('You are already part of a household', 'warning')
        return redirect(url_for('household.index'))

    household = Household.query.get_or_404(household_id)

    # Add user to household
    current_user.household_id = household.id
    db.session.commit()

    flash(f'Successfully joined household "{household.name}"!', 'success')
    return redirect(url_for('household.index'))

@household_bp.route('/leave', methods=['POST'])
@login_required
def leave():
    """Leave a household"""
    if not current_user.household:
        flash('You are not part of any household', 'info')
        return redirect(url_for('main.index'))

    household = current_user.household
    household_name = household.name
    current_user.household_id = None
    db.session.commit()

    flash(f'You have left the household "{household_name}"', 'info')
    return redirect(url_for('main.index'))

@household_bp.route('/remove-member/<int:user_id>', methods=['POST'])
@login_required
def remove_member(user_id):
    """Remove a member from household (only household creator)"""
    if not current_user.household:
        flash('You are not part of any household', 'danger')
        return redirect(url_for('household.index'))

    household = current_user.household

    if household.created_by != current_user.id:
        flash('Only the household creator can remove members', 'danger')
        return redirect(url_for('household.index'))

    user = User.query.get_or_404(user_id)

    if user.household_id != household.id:
        flash('User is not part of this household', 'danger')
        return redirect(url_for('household.index'))

    if user.id == current_user.id:
        flash('You cannot remove yourself. Leave the household instead.', 'warning')
        return redirect(url_for('household.index'))

    user.household_id = None
    db.session.commit()

    flash(f'Removed {user.username} from the household', 'success')
    return redirect(url_for('household.index'))
