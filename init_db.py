from models import db, User
from app import app
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password=generate_password_hash('admin'), access_level='admin')
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created.")

