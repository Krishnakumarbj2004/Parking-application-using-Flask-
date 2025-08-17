
from datetime import datetime
from models.extensions import db


class ParkingLot(db.Model):
    __tablename__ = 'parking_lots'
    id = db.Column(db.Integer, primary_key=True)
    prime_location_name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pin_code = db.Column(db.String(20), nullable=False)
    maximum_number_of_spots = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    parking_spots = db.relationship('ParkingSpot', backref='lot', cascade="all, delete")