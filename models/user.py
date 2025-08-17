
from flask_login import UserMixin
from models.extensions import db



class User(db.Model,UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    dob = db.Column(db.String(100))
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    phone=db.Column(db.Integer, nullable=False)
    role = db.Column(db.String(20), default='user')
    reservations = db.relationship('Reservation', backref='user', lazy=True)