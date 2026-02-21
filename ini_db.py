from app import app
from extensions import db
from models import User, Mesa, Producto
from sqlalchemy import text

with app.app_context():

    # ─── MIGRACIONES MANUALES ─────────────────────────────────────
    # db.create_all() NO agrega columnas a tablas existentes.
    # Por eso agregamos las columnas que faltan con SQL directo.
    # Usamos IF NOT EXISTS para que no falle si ya existen.
    migraciones = [
        # Tabla producto
        "ALTER TABLE producto ADD COLUMN IF NOT EXISTS categoria VARCHAR(30) NOT NULL DEFAULT 'almuerzos'",
        # Tabla pedido
        "ALTER TABLE pedido ADD COLUMN IF NOT EXISTS metodo_pago  VARCHAR(20)",
        "ALTER TABLE pedido ADD COLUMN IF NOT EXISTS monto_recibido FLOAT",
        "ALTER TABLE pedido ADD COLUMN IF NOT EXISTS cambio FLOAT",
        "ALTER TABLE pedido ADD COLUMN IF NOT EXISTS fecha_cierre TIMESTAMP",
        # Tabla user
        "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS activo BOOLEAN DEFAULT TRUE",
    ]

    for sql in migraciones:
        try:
            db.session.execute(text(sql))
            print(f"✅ Migración OK: {sql[:60]}...")
        except Exception as e:
            print(f"⚠️  Migración omitida: {e}")

    db.session.commit()
    print("✅ Migraciones completas")

    # ─── CREAR TABLAS NUEVAS (si las hubiera) ────────────────────
    db.create_all()
    print("✅ Tablas verificadas")

    # ─── USUARIOS ────────────────────────────────────────────────
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", role="admin", activo=True)
        admin.set_password("admin123")
        db.session.add(admin)
        print("✅ Admin creado")
    else:
        print("ℹ️  Admin ya existe")

    if not User.query.filter_by(username="mesero").first():
        mesero = User(username="mesero", role="mesero", activo=True)
        mesero.set_password("mesero123")
        db.session.add(mesero)
        print("✅ Mesero creado")
    else:
        print("ℹ️  Mesero ya existe")

    db.session.commit()

    # ─── MESAS (completa hasta 20) ───────────────────────────────
    numeros_existentes = {m.numero for m in Mesa.query.all()}
    mesas_nuevas = 0
    for i in range(1, 21):
        if i not in numeros_existentes:
            db.session.add(Mesa(numero=i, estado="libre"))
            mesas_nuevas += 1
    db.session.commit()
    print(f"✅ Mesas: {mesas_nuevas} nuevas | Total: {Mesa.query.count()}")

    # ─── PRODUCTOS BASE ──────────────────────────────────────────
    productos_base = [
        # (nombre, precio, categoria)
        # ESPECIALIDAD
        ("Arepa de choclo", 6_500, "especialidad"),
        # DESAYUNOS
        ("Sencillo",        7_000,  "desayunos"),
        ("Completo",        17_000,  "desayunos"),
        ("Rancho 27 ",      28_000,  "desayunos"),
        # ALMUERZOS
        ("Almuerzo al horno",   30_000,  "almuerzos"),
        ("Almuerzo ejecutivo", 27_000,  "almuerzos"),
        ("Sopa del día",     7_000,  "almuerzos"),

        # PORCIONES
        ("Carne al horno",           27_000,  "porciones"),
        ("Chuleta",                  27_000,  "porciones"),
        ("Costilla ahumada",         27_000,  "porciones"),
        ("Filete de Pollo",          25_000,  "porciones"),
        ("Chorizo + arepa blanca",    6_500,  "porciones"),
        ("papa francesa",             5_000,  "porciones"),
        ("Papa al vapor",             3_000,  "porciones"),
        ("Arroz",                     4_000,  "porciones"),
        ("ensalada",                  3_000,  "porciones"),
        ("Queso",                     3_000,  "porciones"),

        # BEBIDAS CALIENTES
        ("Chocolate grande",          5_000,  "bebidas calientes"),
        ("Chocolate pequeño",         3_500,  "bebidas calientes"),
        ("Agua de panela grande",     4_000,  "bebidas calientes"),
        ("Agua de panela pequeña",    3_000,  "bebidas calientes"),
        ("cafe negro",                2_000,  "bebidas calientes"),
        ("cafe en leche",             2_500,  "bebidas calientes"),
        ("Aromatica",                 3_000,  "bebidas calientes"),
        # BEBIDAS FRÍAS
        ("Jugo hit",                  5_000,  "bebidas frías"),
        ("Gaseosa",                   5_000,  "bebidas frías"),
        ("Cerveza poker o club",      5_000,  "bebidas frías"),
        ("Cerveza corona",            7_000,  "bebidas frías"),
        ("Agua botella",              3_000,  "bebidas frías"),
        ("H20",                       4_000,  "bebidas frías"),
        ("Gatorade",                  5_000,  "bebidas frías"),
        ("Pony malta",                5_000,  "bebidas frías"),
        ("Limoinada",                 3_000,  "bebidas frías"),
    ]

    nombres_existentes = {p.nombre for p in Producto.query.all()}
    productos_nuevos = 0
    for nombre, precio, categoria in productos_base:
        if nombre not in nombres_existentes:
            db.session.add(Producto(
                nombre=nombre,
                precio=precio,
                categoria=categoria,
                activo=True
            ))
            productos_nuevos += 1
    db.session.commit()
    print(f"✅ Productos: {productos_nuevos} nuevos creados | Total: {Producto.query.count()}")

    # ─── RESUMEN FINAL ───────────────────────────────────────────
    print("─" * 40)
    print(f"👤 Usuarios : {User.query.count()}")
    print(f"🪑 Mesas    : {Mesa.query.count()}")
    print(f"🍽️  Productos: {Producto.query.count()}")
    print("✅ DB lista + usuarios + mesas creadas OK")