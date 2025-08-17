from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from models.parking_lots import ParkingLot
from models.user import User
from models.extensions import db  

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')







@admin_bp.route('/add_lot', methods=['GET', 'POST'])
def add_lot():
    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        try:
            total_spots = int(request.form['total_spots'])
        except (ValueError, TypeError):
            flash('Total spots must be a valid integer.', 'danger')
            return redirect(url_for('admin.add_lot'))

        pincode = request.form['pincode']
        price = request.form['price']

        new_lot = ParkingLot(
            name=name,
            location=location,
            total_spots=total_spots,
            pincode=pincode,
            price=price
        )
        db.session.add(new_lot)
        db.session.commit()

        


        flash('Parking lot added successfully!', 'success')
        return redirect(url_for('admin.add_lot'))

    return render_template('admin/add_lot.html')
