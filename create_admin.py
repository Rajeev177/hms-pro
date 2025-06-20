from app import app, db
from models import User
from werkzeug.security import generate_password_hash

# Run this script once to create the admin user
with app.app_context():
    existing_user = User.query.filter_by(username='admin').first()
    if existing_user:
        print("⚠️ Admin user already exists.")
    else:
        admin = User(
            username='admin',
            password=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created: username='admin', password='admin123'")

