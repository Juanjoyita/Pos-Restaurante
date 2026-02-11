from app import app, db
from models import User

with app.app_context():
    admin = User(
        username="admin",
        role="admin"
    )
    admin.set_password("admin123")

    mesero = User(
        username="mesero",
        role="mesero"
    )
    mesero.set_password("mesero123")

    db.session.add(admin)
    db.session.add(mesero)
    db.session.commit()

    print("✅ Usuarios creados correctamente")
