from flask import Blueprint, render_template, session, redirect, url_for, flash

from models.Reservation import  Reservation
from models.user import User
user_bp = Blueprint('user', __name__)

@user_bp.route('/user/dashboard')
def user_dashboard():
    if 'user_id' not in session:
        flash('Please login to access dashboard.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = User.query.get(user_id)

    active_reservations = Reservation.query.filter_by(user_id=user_id, status='O').all()
    past_reservations = Reservation.query.filter_by(user_id=user_id, status='L').all()

    return render_template('user_dashboard.html', user=user,
                           active_reservations=active_reservations,
                           past_reservations=past_reservations)
