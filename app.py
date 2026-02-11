# app.py
from flask import Flask, render_template, redirect, url_for, request, jsonify
from dotenv import load_dotenv
import os
from zoneinfo import ZoneInfo
from datetime import datetime, date, time
from sqlalchemy import func

from flask_login import (
    login_required,
    current_user,
    login_user,
    logout_user
)
from flask import abort
from extensions import db, login_manager, cors
from models import User, Mesa, Producto, Pedido, PedidoDetalle

load_dotenv()

app = Flask(__name__)

# ---------- CONFIGURACIÓN ----------
db_url = os.getenv("DATABASE_URL")  # Render la pone
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url or "sqlite:///database.db"


# ---------- INICIALIZAR EXTENSIONES ----------
db.init_app(app)
login_manager.init_app(app)
cors.init_app(app)

login_manager.login_view = "login"

@app.template_filter("hora_bogota")
def hora_bogota(dt):
    if not dt:
        return ""
    try:
        # Si viene sin tzinfo, asumimos que es hora local del servidor
        # y la convertimos a Bogotá
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("America/Bogota"))
        return dt.astimezone(ZoneInfo("America/Bogota")).strftime("%H:%M")
    except Exception:
        # fallback
        return dt.strftime("%H:%M")

# ---------- FILTRO COP (para imprimir dinero estilo Colombia) ----------
@app.template_filter("cop")
def cop(value):
    try:
        n = int(round(float(value)))
    except (TypeError, ValueError):
        n = 0
    return "$" + f"{n:,}".replace(",", ".")


# ---------- LOGIN MANAGER ----------
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ---------- LOGIN ----------
@app.route("/", methods=["GET", "POST"])
def login():
    error = None  # para mostrar mensajes en el HTML (opcional)

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            # ✅ bloquear si está desactivado
            if hasattr(user, "activo") and not user.activo:
                error = "Usuario desactivado. Contacta al administrador."
            else:
                login_user(user)

                next_page = request.args.get("next")
                if next_page:
                    return redirect(next_page)

                if (user.role or "").lower() == "admin":
                    return redirect(url_for("admin_panel"))
                elif (user.role or "").lower() == "mesero":
                    return redirect(url_for("ver_mesas"))

                error = "Rol desconocido."
        else:
            error = "Usuario o contraseña incorrectos."

    return render_template("login.html", error=error)



@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ---------- MESERO: MESAS ----------
@app.route("/mesas")
@login_required
def ver_mesas():
    if current_user.role.lower() != "mesero":
        return redirect(url_for("login"))

    mesas = Mesa.query.order_by(Mesa.numero.asc()).all()
    return render_template("mesas.html", mesas=mesas)


# ✅ Mesas en tiempo real (JSON)
@app.route("/mesas.json")
@login_required
def mesas_json():
    if current_user.role.lower() != "mesero":
        return jsonify({"error": "forbidden"}), 403

    mesas = Mesa.query.order_by(Mesa.numero.asc()).all()
    return jsonify({
        "mesas": [{"id": m.id, "numero": m.numero, "estado": m.estado} for m in mesas]
    })


# ---------- MESERO: MENU / ENVIAR PEDIDO (1 pedido abierto por mesa) ----------
@app.route("/mesa/<int:mesa_id>", methods=["GET", "POST"])
@login_required
def menu_mesa(mesa_id):
    if current_user.role.lower() != "mesero":
        return redirect(url_for("login"))

    mesa = Mesa.query.get_or_404(mesa_id)
    productos = Producto.query.filter_by(activo=True).order_by(Producto.nombre.asc()).all()

    if request.method == "POST":
        items = []  # [(producto_id, cantidad)]
        for producto in productos:
            cantidad_str = request.form.get(f"producto_{producto.id}", "0")
            try:
                cantidad = int(cantidad_str)
            except ValueError:
                cantidad = 0

            if cantidad > 0:
                items.append((producto.id, cantidad))

        if not items:
            return render_template(
                "menu.html",
                mesa=mesa,
                productos=productos,
                error="No seleccionaste ningún producto. El pedido no se envió."
            )

        pedido = (
            Pedido.query
            .filter_by(mesa_id=mesa.id, estado="abierto")
            .order_by(Pedido.fecha.desc())
            .first()
        )

        if not pedido:
            pedido = Pedido(mesa_id=mesa.id, mesero_id=current_user.id, estado="abierto")
            db.session.add(pedido)
            db.session.flush()

        for producto_id, cantidad in items:
            detalle_existente = (
                PedidoDetalle.query
                .filter_by(pedido_id=pedido.id, producto_id=producto_id)
                .first()
            )
            if detalle_existente:
                detalle_existente.cantidad += cantidad
            else:
                db.session.add(PedidoDetalle(
                    pedido_id=pedido.id,
                    producto_id=producto_id,
                    cantidad=cantidad
                ))

        mesa.estado = "ocupada"
        db.session.commit()
        return redirect(url_for("ver_mesas"))

    return render_template("menu.html", mesa=mesa, productos=productos, error=None)


# ---------- ADMIN: PANEL ----------

@app.route("/admin/pedidos")
@login_required
def admin_pedidos():
    if current_user.role.lower() != "admin":
        return redirect(url_for("login"))
    return render_template("admin_pedidos.html")

@app.route("/admin")
@login_required
def admin_panel():
    if current_user.role.lower() != "admin":
        return redirect(url_for("login"))

    pedidos_cerrados = (
        Pedido.query
        .filter_by(estado="cerrado")
        .order_by(Pedido.fecha.desc())
        .limit(20)
        .all()
    )

    return render_template(
        "admin.html",
        pedidos_cerrados=pedidos_cerrados
    )

from datetime import datetime, date, time


def solo_admin():
    return current_user.is_authenticated and (current_user.role or "").lower() == "admin"


@app.route("/admin/usuarios")
@login_required
def admin_usuarios():
    if not solo_admin():
        return redirect(url_for("login"))

    usuarios = User.query.order_by(User.role.asc(), User.username.asc()).all()
    return render_template("admin_usuarios.html", usuarios=usuarios)


@app.route("/admin/usuarios/nuevo", methods=["GET", "POST"])
@login_required
def admin_usuario_nuevo():
    if not solo_admin():
        return redirect(url_for("login"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = "mesero"  # ✅ solo mesero por seguridad

        if not username or not password:
            return render_template("admin_usuario_form.html", error="Faltan datos.", usuario=None)

        if User.query.filter_by(username=username).first():
            return render_template("admin_usuario_form.html", error="Ese usuario ya existe.", usuario=None)

        u = User(username=username, role=role, activo=True)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        return redirect(url_for("admin_usuarios"))

    return render_template("admin_usuario_form.html", error=None, usuario=None)


@app.route("/admin/usuarios/<int:user_id>/toggle", methods=["POST"])
@login_required
def admin_usuario_toggle(user_id):
    if not solo_admin():
        return redirect(url_for("login"))

    u = db.session.get(User, user_id)
    if not u:
        return redirect(url_for("admin_usuarios"))

    # No tocar admins por seguridad
    if (u.role or "").lower() != "mesero":
        return redirect(url_for("admin_usuarios"))

    # No desactivar al usuario logueado si fuera mesero (normalmente admin no es mesero)
    if u.id == current_user.id:
        return redirect(url_for("admin_usuarios"))

    u.activo = not bool(u.activo)
    db.session.commit()
    return redirect(url_for("admin_usuarios"))


@app.route("/admin/usuarios/<int:user_id>/eliminar", methods=["POST"])
@login_required
def admin_usuario_eliminar(user_id):
    if not solo_admin():
        return redirect(url_for("login"))

    u = db.session.get(User, user_id)
    if not u:
        return redirect(url_for("admin_usuarios"))

    # Solo borrar meseros
    if (u.role or "").lower() != "mesero":
        return redirect(url_for("admin_usuarios"))

    # Regla para NO romper historial: si tiene pedidos, no se borra
    tiene_pedidos = Pedido.query.filter_by(mesero_id=u.id).first()
    if tiene_pedidos:
        # En vez de borrar, mejor desactivar
        u.activo = False
        db.session.commit()
        return redirect(url_for("admin_usuarios"))

    db.session.delete(u)
    db.session.commit()
    return redirect(url_for("admin_usuarios"))


@app.route("/admin/caja")
@login_required
def caja_dia():
    if current_user.role.lower() != "admin":
        return redirect(url_for("login"))

    # 1) Traer todas las fechas únicas (YYYY-MM-DD) donde hubo pedidos cerrados
    fechas_rows = (
        db.session.query(db.func.date(Pedido.fecha_cierre))
        .filter(
            Pedido.estado == "cerrado",
            Pedido.fecha_cierre.isnot(None)
        )
        .group_by(db.func.date(Pedido.fecha_cierre))
        .order_by(db.func.date(Pedido.fecha_cierre).desc())
        .all()
    )

    # lista tipo ["2026-02-09", "2026-02-08", ...]
    fechas_disponibles = [str(r[0]) for r in fechas_rows if r[0] is not None]

    # 2) Determinar qué día mostrar
    fecha_str = request.args.get("fecha", "").strip()

    if fecha_str and fecha_str in fechas_disponibles:
        dia = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    else:
        # por defecto, el más reciente
        dia = datetime.strptime(fechas_disponibles[0], "%Y-%m-%d").date() if fechas_disponibles else date.today()

    inicio = datetime.combine(dia, time.min)
    fin = datetime.combine(dia, time.max)

    pedidos = (
        Pedido.query
        .filter(
            Pedido.estado == "cerrado",
            Pedido.fecha_cierre.isnot(None),
            Pedido.fecha_cierre >= inicio,
            Pedido.fecha_cierre <= fin
        )
        .order_by(Pedido.fecha_cierre.desc())
        .all()
    )

    total_dia = 0.0
    conteo = len(pedidos)
    por_metodo = {"efectivo": 0.0, "transferencia": 0.0, "tarjeta": 0.0, "otro": 0.0}
    pedidos_info = []

    top = {}  # nombre -> {"cantidad": x, "ventas": y}

    for p in pedidos:
        total_pedido = 0.0
        for d in p.detalles:
            subtotal = float(d.producto.precio) * int(d.cantidad)
            total_pedido += subtotal

            nombre = d.producto.nombre
            if nombre not in top:
                top[nombre] = {"cantidad": 0, "ventas": 0.0}
            top[nombre]["cantidad"] += int(d.cantidad)
            top[nombre]["ventas"] += subtotal

        total_dia += total_pedido

        metodo = (p.metodo_pago or "otro").lower()
        if metodo not in por_metodo:
            metodo = "otro"
        por_metodo[metodo] += total_pedido

        pedidos_info.append({
            "id": p.id,
            "mesa": p.mesa.numero,
            "hora": p.fecha_cierre.strftime("%H:%M") if p.fecha_cierre else "",
            "metodo": (p.metodo_pago or "otro"),
            "total": total_pedido,
        })

    ticket_promedio = (total_dia / conteo) if conteo > 0 else 0.0

    top_lista = sorted(
        [{"nombre": k, "cantidad": v["cantidad"], "ventas": v["ventas"]} for k, v in top.items()],
        key=lambda x: x["ventas"],
        reverse=True
    )[:10]

    return render_template(
        "caja.html",
        dia=dia,
        fechas_disponibles=fechas_disponibles,
        total_dia=total_dia,
        conteo=conteo,
        ticket_promedio=ticket_promedio,
        por_metodo=por_metodo,
        pedidos_info=pedidos_info,
        top_lista=top_lista
    )


# ---------- ADMIN: FACTURA (HTML imprimible) ----------
@app.route("/admin/factura/<int:pedido_id>")
@login_required
def ver_factura(pedido_id):
    if current_user.role.lower() != "admin":
        return redirect(url_for("login"))

    pedido = Pedido.query.get_or_404(pedido_id)

    items = []
    total = 0.0
    for d in pedido.detalles:
        precio = float(d.producto.precio)
        cantidad = int(d.cantidad)
        subtotal = precio * cantidad
        total += subtotal
        items.append({
            "nombre": d.producto.nombre,
            "cantidad": cantidad,
            "precio": precio,
            "subtotal": subtotal
        })

    # ✅ si viene ?print=1 => auto imprimir en factura.html
    auto_print = request.args.get("print") == "1"
    error = request.args.get("error")

    return render_template(
        "factura.html",
        pedido=pedido,
        items=items,
        total=total,
        auto_print=auto_print
    )


# ✅ Pedidos en tiempo real (JSON) + total + subtotales
@app.route("/admin/pedidos.json")
@login_required
def admin_pedidos_json():
    if current_user.role.lower() != "admin":
        return jsonify({"error": "forbidden"}), 403

    pedidos = (
        Pedido.query
        .filter_by(estado="abierto")
        .order_by(Pedido.fecha.desc())
        .all()
    )

    data = []
    for p in pedidos:
        detalles = []
        total = 0.0

        for d in p.detalles:
            precio = float(d.producto.precio)
            cantidad = int(d.cantidad)
            subtotal = precio * cantidad
            total += subtotal

            detalles.append({
                "nombre": d.producto.nombre,
                "cantidad": cantidad,
                "precio": precio,
                "subtotal": subtotal
            })

        data.append({
            "id": p.id,
            "mesa": p.mesa.numero,
            "mesero": p.mesero.username,
            "fecha": p.fecha.isoformat() if p.fecha else "",
            "detalles": detalles,
            "total": total
        })

    return jsonify({"pedidos": data})


# ---------- ADMIN: CERRAR PEDIDO (LIBERA MESA) ----------
@app.route("/admin/pedido/<int:pedido_id>/cerrar", methods=["POST"])
@login_required
def cerrar_pedido(pedido_id):
    if current_user.role.lower() != "admin":
        return redirect(url_for("login"))

    pedido = Pedido.query.get_or_404(pedido_id)

    if pedido.estado != "cerrado":
        pedido.estado = "cerrado"

        mesa = db.session.get(Mesa, pedido.mesa_id)
        if mesa:
            mesa.estado = "libre"

        db.session.commit()

    return redirect(url_for("admin_panel"))


from datetime import datetime

@app.route("/admin/pedido/<int:pedido_id>/cobrar", methods=["POST"])
@login_required
def cobrar_pedido(pedido_id):
    if current_user.role.lower() != "admin":
        return redirect(url_for("login"))

    pedido = Pedido.query.get_or_404(pedido_id)

    # leer datos del form
    metodo_pago = (request.form.get("metodo_pago") or "").strip().lower()
    monto_recibido_raw = (request.form.get("monto_recibido") or "").strip()

    # calcular total del pedido
    total = 0.0
    for d in pedido.detalles:
        total += float(d.producto.precio) * int(d.cantidad)

    # calcular cambio
    cambio = 0.0
    monto_recibido = None

    if metodo_pago == "efectivo":
        try:
            monto_recibido = float(monto_recibido_raw)
        except ValueError:
            monto_recibido = 0.0

        cambio = monto_recibido - total
        if cambio < 0:
            # no alcanza el dinero
            return redirect(url_for("ver_factura", pedido_id=pedido.id, error="pago_insuficiente"))

    elif metodo_pago in ["transferencia", "tarjeta"]:
        # normalmente no hay cambio
        monto_recibido = total
        cambio = 0.0
    else:
        return redirect(url_for("ver_factura", pedido_id=pedido.id, error="metodo_invalido"))

    # cerrar pedido + guardar pago
    pedido.estado = "cerrado"
    pedido.metodo_pago = metodo_pago
    pedido.monto_recibido = monto_recibido
    pedido.cambio = cambio
    pedido.fecha_cierre = datetime.now()

    # liberar mesa
    mesa = db.session.get(Mesa, pedido.mesa_id)
    if mesa:
        mesa.estado = "libre"

    db.session.commit()

    # auto imprimir
    return redirect(url_for("ver_factura", pedido_id=pedido.id, print=1))


def solo_admin():
    return current_user.is_authenticated and (current_user.role or "").lower() == "admin"


@app.route("/admin/productos")
@login_required
def admin_productos():
    if not solo_admin():
        return redirect(url_for("login"))

    productos = Producto.query.order_by(Producto.activo.desc(), Producto.nombre.asc()).all()
    return render_template("admin_productos.html", productos=productos)


@app.route("/admin/productos/nuevo", methods=["GET", "POST"])
@login_required
def admin_producto_nuevo():
    if not solo_admin():
        return redirect(url_for("login"))

    error = None

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        precio_str = request.form.get("precio", "").strip()

        if not nombre:
            error = "El nombre es obligatorio."
        else:
            try:
                precio = float(precio_str)
                if precio < 0:
                    raise ValueError()
            except ValueError:
                error = "Precio inválido. Ej: 12000"

        if error:
            return render_template("admin_producto_form.html", modo="nuevo", producto=None, error=error)

        p = Producto(nombre=nombre, precio=precio, activo=True)
        db.session.add(p)
        db.session.commit()
        return redirect(url_for("admin_productos"))

    return render_template("admin_producto_form.html", modo="nuevo", producto=None, error=error)


@app.route("/admin/productos/<int:producto_id>/editar", methods=["GET", "POST"])
@login_required
def admin_producto_editar(producto_id):
    if not solo_admin():
        return redirect(url_for("login"))

    producto = Producto.query.get_or_404(producto_id)
    error = None

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        precio_str = request.form.get("precio", "").strip()
        activo = request.form.get("activo") == "on"

        if not nombre:
            error = "El nombre es obligatorio."
        else:
            try:
                precio = float(precio_str)
                if precio < 0:
                    raise ValueError()
            except ValueError:
                error = "Precio inválido. Ej: 12000"

        if error:
            # mantener lo que escribió el usuario
            producto.nombre = nombre
            try:
                producto.precio = float(precio_str)
            except Exception:
                pass
            producto.activo = activo
            return render_template("admin_producto_form.html", modo="editar", producto=producto, error=error)

        producto.nombre = nombre
        producto.precio = precio
        producto.activo = activo

        db.session.commit()
        return redirect(url_for("admin_productos"))

    return render_template("admin_producto_form.html", modo="editar", producto=producto, error=error)


@app.route("/admin/productos/<int:producto_id>/toggle", methods=["POST"])
@login_required
def admin_producto_toggle(producto_id):
    if not solo_admin():
        return redirect(url_for("login"))

    producto = Producto.query.get_or_404(producto_id)
    producto.activo = not bool(producto.activo)
    db.session.commit()
    return redirect(url_for("admin_productos"))


@app.route("/admin/productos/<int:producto_id>/eliminar", methods=["POST"])
@login_required
def admin_producto_eliminar(producto_id):
    if not solo_admin():
        return redirect(url_for("login"))

    producto = Producto.query.get_or_404(producto_id)

    # ✅ regla segura: si el producto ya se usó en pedidos, NO lo borres (desactívalo)
    usado = PedidoDetalle.query.filter_by(producto_id=producto.id).first()
    if usado:
        producto.activo = False
        db.session.commit()
        return redirect(url_for("admin_productos"))

    db.session.delete(producto)
    db.session.commit()
    return redirect(url_for("admin_productos"))



# ---------- MAIN ----------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=8000, debug=False)
