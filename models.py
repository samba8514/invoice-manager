from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), default='user')

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), default="Unpaid")
    comment = db.Column(db.Text, default="")
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    subject = db.Column(db.String(300))
    sender = db.Column(db.String(300))
    filepath = db.Column(db.String(300))
    received_at = db.Column(db.DateTime)
    imap_uid = db.Column(db.String, nullable=True)
    amount = db.Column(db.Float, nullable=True)
    deadline = db.Column(db.Date, nullable=True)

class FetchLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
class ActionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=True)
