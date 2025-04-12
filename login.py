from app import app
from werkzeug.security import generate_password_hash
import getpass
import os
from datetime import datetime
import getpass as gp
import platform
from models import db, User


# ==== Config ====
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "user_creation.log")
os.makedirs(LOG_DIR, exist_ok=True)

def log_action(message):
    system_user = gp.getuser()
    hostname = platform.node()
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.utcnow()}] [{system_user}@{hostname}] {message}\n")

def create_user():
    username = input("Enter username: ").strip()
    password = getpass.getpass("Enter password: ").strip()

    # Role assignment
    while True:
        role = input("🛡  Assign role (admin/user): ").strip().lower()
        if role in ['admin', 'user']:
            break
        print("Please enter a valid role: 'admin' or 'user'.")

    with app.app_context():
        db.create_all()
        existing = User.query.filter_by(username=username).first()
        if existing:
            msg = f" User '{username}' already exists."
            print(msg)
            log_action(msg)
            return

        hashed_pw = generate_password_hash(password)
        user = User(username=username, password=hashed_pw, role=role)
        db.session.add(user)
        db.session.commit()
        msg = f"User '{username}' with role '{role}' created successfully."
        print(msg)
        log_action(msg)

if __name__ == "__main__":
    create_user()
