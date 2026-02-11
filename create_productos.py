from app import app
from extensions import db
from models import Producto

with app.app_context():
    # ✅ asegura que existan las tablas
    db.create_all()

    productos = [
        Producto(nombre="Hamburguesa", precio=15000, activo=True),
        Producto(nombre="Papas fritas", precio=6000, activo=True),
        Producto(nombre="Gaseosa", precio=3000, activo=True),
        Producto(nombre="Jugo natural", precio=5000, activo=True),
    ]

    db.session.add_all(productos)
    db.session.commit()

    print("✅ Productos creados correctamente")
