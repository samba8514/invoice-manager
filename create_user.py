# create_default_user.py

from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    username = "admin"
    password = "jelly22fi$h"

    # Check if user already exists
    existing = User.query.filter_by(username=username).first()
    if existing:
        print(f"⚠️ User '{username}' already exists.")
    else:
        hashed_password = generate_password_hash(password)
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        print(f"✅ Default user created: {username} / {password}")
