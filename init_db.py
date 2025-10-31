#!/usr/bin/env python3
"""
Initialize database and create admin users
"""
from app import create_app, db
from app.models.user import User
from app.models.system_settings import SystemSettings
from app.utils.auth import hash_password
from datetime import datetime

app = create_app()

with app.app_context():
    # Ensure tables exist (safe if already created)
    db.create_all()
    # Initialize system settings
    SystemSettings.initialize_defaults()
    
    # Create admin users
    admin_users = [
        {
            'email': 'jty9410@wecar-m.co.kr',
            'name': 'Admin User 1',
            'password': '#jeong07209',
            'is_admin': True,
            'status': 'active'
        },
        {
            'email': 'wecar@wecar-m.co.kr',
            'name': 'Admin User 2',
            'password': '#wecarm1004',
            'is_admin': True,
            'status': 'active'
        }
    ]
    
    for admin_data in admin_users:
        existing = User.query.filter_by(email=admin_data['email']).first()
        if not existing:
            admin = User(
                email=admin_data['email'],
                name=admin_data['name'],
                password_hash=hash_password(admin_data['password']),
                is_admin=True,
                status='active',
                created_at=datetime.utcnow()
            )
            db.session.add(admin)
            print(f"Created admin user: {admin_data['email']}")
        else:
            print(f"Admin user already exists: {admin_data['email']}")
    
    db.session.commit()
    print("Database initialization complete!")

