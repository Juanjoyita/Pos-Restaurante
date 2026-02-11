from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    # ✅ para activar/desactivar meseros
    activo = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Mesa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.Integer, unique=True, nullable=False)
    estado = db.Column(db.String(20), default="libre")

    def __repr__(self):
        return f"<Mesa {self.numero} - {self.estado}>"


class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    activo = db.Column(db.Boolean, default=True)


    def __repr__(self):
        return f"<Producto {self.nombre}>"


class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mesa_id = db.Column(db.Integer, db.ForeignKey("mesa.id"), nullable=False)
    mesero_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    estado = db.Column(db.String(20), default="abierto")
    fecha = db.Column(db.DateTime, default=datetime.now)

    # ✅ pago/cierre
    metodo_pago = db.Column(db.String(20), nullable=True)      # efectivo / transferencia / tarjeta
    monto_recibido = db.Column(db.Float, nullable=True)
    cambio = db.Column(db.Float, nullable=True)
    fecha_cierre = db.Column(db.DateTime, nullable=True)

    mesa = db.relationship("Mesa")
    mesero = db.relationship("User")


class PedidoDetalle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedido.id"), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("producto.id"), nullable=False)
    cantidad = db.Column(db.Integer, default=1)

    pedido = db.relationship("Pedido", backref="detalles")
    producto = db.relationship("Producto")
