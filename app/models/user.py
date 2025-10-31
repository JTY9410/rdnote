from app import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    org_name = db.Column(db.String(200))
    department = db.Column(db.String(200))
    researcher_code = db.Column(db.String(50), index=True)
    signature_path = db.Column(db.String(500))
    status = db.Column(db.String(20), default='pending', nullable=False, index=True)  # pending, active, suspended
    is_admin = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<User {self.email}>'

