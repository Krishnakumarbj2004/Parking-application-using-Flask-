from flask import Flask, render_template, request, redirect, url_for, flash,session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from werkzeug.security import generate_password_hash,check_password_hash
from models.extensions import db
from models.user import User
from models.user import User
from models.Reservation import Reservation
from models.parking_spot import ParkingSpot
from models.parking_lots import ParkingLot
import datetime
import matplotlib.pyplot as plt
import os,math,io,base64
import matplotlib
matplotlib.use('Agg')






app = Flask(__name__)
app.secret_key = 'root'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)  # 2. initialize db with app
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user:
            print("Hashed password in DB:", user.password)
            print("Password entered:", password)
            print("Password match:", check_password_hash(user.password, password))
            
            print("User role:", user.role)

        if user.role == "admin":
            print("Admin login attempt")
            if user and password=="admin" and user.role =='admin':
                print("inside if")
                login_user(user)
                
                return redirect('/admin/dashboard')
                
            else:
                flash("Invalid credentials", "danger")
        elif user.role == 'user':
            if user and check_password_hash(user.password, password) and user.role == role:
                login_user(user)
                return redirect('/user/dashboard')
            else:
                flash("Invalid credentials", "danger")
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists.')
            return redirect(url_for('signup'))
        data = request.form
        
        new_user = User(
        name=data.get('name'),
        age=data.get('age'),
        dob=data.get('dob'),
        username=data.get('username'),
        password=generate_password_hash(data.get('password')),
        phone=data.get('phone'),
        role='user'
    )
        db.session.add(new_user)
        db.session.commit()
        flash('Signup successful. Please log in.')
        return redirect(url_for('login'))
    return render_template('signup.html')



@app.route('/admin/dashboard')
def admin_dashboard():
    users = User.query.all()
    lots = ParkingLot.query.all()
    spots = ParkingSpot.query.all()
    reservations = Reservation.query.filter_by(status='O').all()

    total_users = len(users)
    total_lots = len(lots)
    total_spots = len(spots)
    occupied_spots = len(reservations)
    available_spots = total_spots - occupied_spots

    occupancy_data = []
    for lot in lots:
        lot_spots = [spot for spot in spots if spot.lot_id == lot.id]
        occupied = 0
        for spot in lot_spots:
            if Reservation.query.filter_by(spot_id=spot.id, status='O').first():
                occupied += 1
        occupancy_data.append((lot.prime_location_name, len(lot_spots), occupied))
    return render_template('admin.html',total_users=total_users,
                           total_lots=total_lots,
                           total_spots=total_spots,
                           occupied_spots=occupied_spots,
                           available_spots=available_spots)


@app.route('/admin/add_lot', methods=['GET', 'POST'])
def add_lot():
    if request.method == 'POST':
        prime_location_name = request.form['prime_location_name']
        address = request.form['address']
        pin_code = request.form['pin_code']
        max_spots = int(request.form['maximum_number_of_spots'])
        description = request.form.get('description', '')

        lot = ParkingLot(
            prime_location_name=prime_location_name,
            address=address,
            pin_code=pin_code,
            maximum_number_of_spots=max_spots,
            description=description
        )
        db.session.add(lot)
        db.session.commit()

        # Add spots
        for _ in range(max_spots):
            spot = ParkingSpot(lot_id=lot.id) 
            db.session.add(spot)
        db.session.commit()

        flash("Parking lot created with spots.")
        return redirect(url_for('view_lots'))

    return render_template('add_lot.html')


@app.route('/admin/search_user', methods=['GET', 'POST'])
@login_required
def search_user():
    if current_user.role != 'admin':
        return redirect('/login')

    result = None

    if request.method == 'POST':
        keyword = request.form.get('search_input')
        print("Search keyword:", keyword)
        # Search by username (get vehicle numbers)
        user = User.query.filter_by(username=keyword).first()
        if user:

            reservations = Reservation.query.filter_by(user_id=user.id).all()
            print(reservations)
            result = {
                'type': 'user',
                'user': user,
                'reservations': reservations
            }
        else:
            # If not username, try as vehicle number
            reservation = Reservation.query.filter_by(vehicle_number=keyword).first()
            print("reserve:",reservation)
            if reservation:
                user = User.query.get(reservation.user_id)
                result = {
                    'type': 'vehicle',
                    'user': user,
                    'reservation': reservation
                }
            else:
                print("no match found")
                flash("No match found.", "warning")

    return render_template('search_user.html', result=result)


@app.route('/admin/view_lots')
def view_lots():
    lots = ParkingLot.query.all()
    data = []

    for lot in lots:
        
        #available_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='A')).all() 
        available_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').count()  
        

        data.append({
            'id': lot.id,
            'prime_location_name': lot.prime_location_name,
            'address': lot.address,
            'pin_code': lot.pin_code,
            'maximum_number_of_spots': lot.maximum_number_of_spots,
            'description': lot.description,
            'available_spots': available_spots,
            'created_at': lot.created_at
        })

    return render_template('view_lots.html', lots=data)

@app.route('/admin/delete_lot/<int:lot_id>')
def delete_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    spots = ParkingSpot.query.filter_by(lot_id=lot_id).all()

    for spot in spots:
        if Reservation.query.filter_by(spot_id=spot.id, status='O').first():
            flash("Cannot delete lot. Some spots have active reservations.")
            return redirect(url_for('view_lots'))

    # Delete
    db.session.delete(lot)
    db.session.commit()

    flash("Parking lot and all associated data deleted successfully.")
    return redirect(url_for('view_lots'))







   

@app.route('/admin/edit_lot/<int:lot_id>', methods=['GET', 'POST'])
@login_required
def edit_lot(lot_id):
    if current_user.role != 'admin':
        return redirect(url_for('login'))

    lot = ParkingLot.query.get_or_404(lot_id)

    if request.method == 'POST':
        try:
            new_max = int(request.form['maximum_number_of_spots'])
        except ValueError:
            flash("Invalid number of spots.", "danger")
            return redirect(url_for('edit_lot', lot_id=lot_id))

        current_max = lot.maximum_number_of_spots
        current_spots = ParkingSpot.query.filter_by(lot_id=lot.id).order_by(ParkingSpot.id).all()

        if new_max < current_max:
            spots_to_remove = current_max - new_max
            available_spots = [spot for spot in reversed(current_spots) if spot.status == 'A']

            if len(available_spots) < spots_to_remove:
                flash("Cannot reduce spots. Not enough available (free) spots to delete.", "danger")
                return redirect(url_for('edit_lot', lot_id=lot_id))

            for spot in available_spots[:spots_to_remove]:
                db.session.delete(spot)

        elif new_max > current_max:
            for i in range(current_max + 1, new_max + 1):
                new_spot = ParkingSpot(lot_id=lot.id, status='A')
                db.session.add(new_spot)

        # Update lot details
        lot.prime_location_name = request.form['prime_location_name']
        lot.address = request.form['address']
        lot.pin_code = request.form['pin_code']
        lot.description = request.form.get('description', '')
        lot.maximum_number_of_spots = new_max
        
        db.session.commit()

        available_spots = lot.maximum_number_of_spots - len(ParkingSpot.query.filter_by(lot_id=lot.id, status='O').all())
        print("Available spots after edit:", available_spots)
        flash("Parking lot updated successfully.", "success")
        return redirect(url_for('view_lots',available_spots=available_spots))

    return render_template('edit_lot.html', lot=lot)






@app.route('/admin/view_users')
def view_users():
    users = User.query.all()
    active_reservations = []

    all_reservations = Reservation.query.filter(
        Reservation.parking_timestamp <= datetime.datetime.now(),
        Reservation.leaving_timestamp >= datetime.datetime.now()
    ).all()
    res1=Reservation.query.filter_by(status='O').all()
    print("Active Reservations:", res1)

   

    for res in res1:
        user = User.query.get(res.user_id)
        spot = ParkingSpot.query.get(res.spot_id)
        lot = ParkingLot.query.get(spot.lot_id)
        
        active_reservations.append({
            
            'user_name': user.username if user else 'Unknown',
            'spot_number': res.spot_id if spot else 'Unknown',
            'status': res.status ,
            'prime_location_name': lot.prime_location_name if lot else 'Unknown',
            'parking_timestamp': res.parking_timestamp,
            'leaving_timestamp': res.leaving_timestamp


            
        })

    return render_template('view_users.html', users=users, active_reservations=active_reservations)

@app.route('/admin/summary')
def summary():
    users = User.query.all()
    lots = ParkingLot.query.all()
    spots = ParkingSpot.query.all()
    reservations = Reservation.query.filter_by(status='O').all()

    total_users = len(users)
    total_lots = len(lots)
    total_spots = len(spots)
    occupied_spots = len(reservations)
    available_spots = total_spots - occupied_spots

    occupancy_data = []
    for lot in lots:
        lot_spots = [spot for spot in spots if spot.lot_id == lot.id]
        occupied = 0
        for spot in lot_spots:
            if Reservation.query.filter_by(spot_id=spot.id, status='O').first():
                occupied += 1
        occupancy_data.append((lot.prime_location_name, len(lot_spots), occupied))

    # Pie Chart
    pie_labels = ['Occupied', 'Available']
    pie_sizes = [occupied_spots, available_spots]

    pie_chart_path = None
    if sum(pie_sizes) > 0:
        plt.figure(figsize=(5, 5))
        plt.pie(pie_sizes, labels=pie_labels, autopct='%1.1f%%', startangle=90)
        plt.title('Parking Slot Summary')
        plt.axis('equal')
        pie_chart_path = os.path.join('static', 'summary_pie.png')
        plt.savefig(pie_chart_path)
        plt.close()

    # Bar Chart
    lot_names = [row[0] for row in occupancy_data]
    total_per_lot = [row[1] for row in occupancy_data]
    occupied_per_lot = [row[2] for row in occupancy_data]

    x = range(len(lot_names))
    plt.figure(figsize=(8, 5))
    plt.bar(x, total_per_lot, label='Total Spots', width=0.4, align='center')
    plt.bar(x, occupied_per_lot, label='Occupied', width=0.4, align='edge')
    plt.xticks(x, lot_names, rotation=30)
    plt.title('Occupancy per Parking Lot')
    plt.legend()
    plt.tight_layout()
    bar_chart_path = os.path.join('static', 'summary_bar.png')
    plt.savefig(bar_chart_path)
    plt.close()

    return render_template('summary.html',
                           total_users=total_users,
                           total_lots=total_lots,
                           total_spots=total_spots,
                           occupied_spots=occupied_spots,
                           available_spots=available_spots,
                           pie_chart=pie_chart_path,
                           bar_chart=bar_chart_path)



@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if current_user.role != 'user':
        return redirect(url_for('login'))

    # Get the latest reservation for the current user
    reservation = (
        Reservation.query.filter_by(user_id=current_user.id).order_by(Reservation.parking_timestamp.desc()).first()
    )

    current_booking = None
    if reservation and reservation.spot and reservation.spot.lot:
        current_booking = {
            'start_time': reservation.parking_timestamp,
            'spot_number': reservation.spot.lot_id,  # assuming this field exists
            'lot_name': reservation.spot.lot.prime_location_name,
            'vehicle_number': reservation.vehicle_number,
        }

    return render_template('user_dashboard.html', current_booking=current_booking)


@app.route('/book', methods=['GET', 'POST'])
@login_required
def book_spot():
    if current_user.role != 'user':
        return redirect(url_for('login'))

    if request.method == 'POST':
        lot_id = request.form['lot_id']
        vehicle_number = request.form['vehicle_number'].strip().upper()

        # Validate format in server side as a backup
    
        import re
        pattern = r"^[A-Z]{2}\s\d{2}\s[A-Z]{2}\s\d{1,4}$"
        if not re.match(pattern, vehicle_number):
            flash("Invalid vehicle number format. Please use 'TN 01 XX 0001'.", 'danger')
            return redirect(url_for('book_spot'))
        # First, get all active reservations for this vehicle


        active_reservations = Reservation.query.filter_by(
            vehicle_number=vehicle_number,
            leaving_timestamp=None
        ).all()

        # Then, check if any of those are in the selected parking lot
        for res in active_reservations:
            spot = ParkingSpot.query.get(res.spot_id)
            if spot and str(spot.lot_id) == lot_id:
                flash("This vehicle is already parked in the selected parking lot.", 'danger')
                return redirect(url_for('book_spot'))

        # Find the first free spot in the selected lot
        spot = ParkingSpot.query.filter_by(lot_id=lot_id, status='A').first()

        if spot:
            reservation = Reservation(
                user_id=current_user.id,
                spot_id=spot.id,
                parking_timestamp=datetime.datetime.now(),
                vehicle_number=vehicle_number,
                status='O',  # 'O' for Occupied
            )
            db.session.add(reservation)
            spot.status = 'O'
            db.session.commit()

            flash(f"Spot #{spot.id} booked successfully in Lot #{lot_id}", 'success')
        else:
            flash("No available spots in this lot.", 'danger')

        return redirect(url_for('user_dashboard'))

    lots = ParkingLot.query.all()
    return render_template('book.html', lots=lots)



@app.route('/release', methods=['GET', 'POST'])
@login_required
def release_spot():
    if current_user.role != 'user':
        return redirect(url_for('login'))

    user_id = current_user.id

    if request.method == 'POST':
        reservation_id = request.form.get('reservation_id')
        print("Reservation ID:", reservation_id)
        reservation_id = str(reservation_id)
        print("String Reservation ID:", reservation_id)
        if not reservation_id:
            flash("No reservation selected.", "danger")
            return redirect(url_for('release_spot'))

        # Convert to int
        reservation_id = int(reservation_id)
        print("Converted Reservation ID:", reservation_id)

        # Fetch reservation
        reservation = Reservation.query.filter_by(id=reservation_id, user_id=user_id).first()

        if reservation and reservation.status == 'O':
            # Update timestamps
            reservation.leaving_timestamp = datetime.datetime.now()
            reservation.status = 'A'

            # Free the parking spot
            spot = ParkingSpot.query.get(reservation.spot_id)
            spot.status = 'A'

            # Calculate parking fee
            fee = calculate_parking_fee(reservation.parking_timestamp, reservation.leaving_timestamp)
            # Ensure this column exists

            db.session.commit()

            flash(f"Spot released successfully. Total charge: ₹{fee}", "success")
        else:
            flash("Invalid or inactive reservation.", "danger")

        return redirect(url_for('user_dashboard',cost=fee))

    # GET: show user reservations with status 'O' (Occupied)

    reservations = Reservation.query.filter_by(user_id=user_id, status='O').all()
    return render_template('release.html', reservations=reservations)


@app.route('/user/active_bookings')
@login_required
def calculate_parking_fee(start, end):
    if not end:
        end = datetime.now()
    duration = end - start
    total_days = math.ceil(duration.total_seconds() / (24 * 60 * 60))
    return 100 if total_days <= 1 else 100 + (total_days - 1) * 50




@app.route('/user/summary')
@login_required
def user_summary():
    if current_user.role != 'user':
        return redirect(url_for('login'))

    user_id = current_user.id
    reservations = Reservation.query.filter_by(user_id=user_id).order_by(Reservation.parking_timestamp.desc()).all()

    total_reservations = len(reservations)
    total_hours = 0
    total_paid = 0

    summary = []
    labels = []
    hours_list = []

    for res in reservations:
        spot = ParkingSpot.query.get(res.spot_id)
        lot = ParkingLot.query.get(spot.lot_id) if spot else None

        hours = 0
        if res.leaving_timestamp:
            delta = res.leaving_timestamp - res.parking_timestamp
            hours = round(delta.total_seconds() / 3600, 2)
            total_hours += hours
            total_paid += int(res.parking_cost)*10 if res.parking_cost else 0

        summary.append({
            'reservation_id': res.id,
            'spot_id': spot.id if spot else None,
            'lot_name': lot.prime_location_name if lot else "Unknown",
            'timestamp': res.parking_timestamp,
            'leaving': res.leaving_timestamp,
            'hours': hours,
            'amount': int(res.parking_cost)*10 if res.parking_cost else 0
        })

        labels.append(res.parking_timestamp.strftime('%d-%b %H:%M'))
        hours_list.append(hours)

    # Generate Matplotlib chart
    plt.figure(figsize=(8, 4))
    plt.bar(labels, hours_list, color='skyblue')
    plt.xticks(rotation=45, ha='right')
    plt.title("Hours Used per Reservation")
    plt.xlabel("Reservation Time")
    plt.ylabel("Hours")
    plt.tight_layout()

    # Save the plot to a string buffer
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    chart_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()

    return render_template('user_summary.html',
                           summary=summary,
                           total_reservations=total_reservations,
                           total_hours=total_hours,
                           total_paid=total_paid,
                           chart_data=chart_url)



@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))


from controllers.admin_controller import admin_bp
from controllers.user_controller import user_bp

app.register_blueprint(admin_bp)
app.register_blueprint(user_bp)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin_user = User(username='admin', password= generate_password_hash('admin'), role='admin',phone=1234567890)
            db.session.add(admin_user)
            db.session.commit()
    app.run(debug=True)
