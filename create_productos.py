from app import app
from extensions import db
from models import Producto

with app.app_context():
    # ✅ asegura que existan las tablas
    db.create_all()

    productos = [
    ]

    db.session.add_all(productos)
    db.session.commit()

    print("✅ Productos creados correctamente")
