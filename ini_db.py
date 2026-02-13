# init_db.py
from app import app
from extensions import db
from models import User, Mesa

def ensure_user(username, password, role):
    u = User.query.filter_by(username=username).first()
    if u:
        return u
    u = User(username=username, role=role, activo=True)
    u.set_password(password)
    db.session.add(u)
    return u

def ensure_mesas(cantidad=10):
    # Si ya hay mesas, no crea nada
    if Mesa.query.count() > 0:
        return

    for n in range(1, cantidad + 1):
        db.session.add(Mesa(numero=n, estado="libre"))

with app.app_context():
    db.create_all()

    # ✅ Seed usuarios
    ensure_user("admin", "admin123", "admin")
    ensure_user("mesero", "mesero123", "mesero")

    # ✅ Seed mesas (elige cuántas quieres)
    ensure_mesas(cantidad=10)  # ← cambia 10 por el número de mesas reales

    db.session.commit()
    print("✅ DB lista + usuarios + mesas creadas OK")
