
from datetime import datetime
from models.extensions import db

class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spots.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    parking_timestamp = db.Column(db.DateTime, nullable=False)
    leaving_timestamp = db.Column(db.DateTime)
    status = db.Column(db.String(1), default='A')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    parking_cost = db.Column(db.Integer, default=10)
    vehicle_number = db.Column(db.String(20), nullable=False)