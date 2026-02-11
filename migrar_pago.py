import sqlite3

DB_PATH = "instance/database.db"

def col_exists(cur, table, col):
    cur.execute(f"PRAGMA table_info({table});")
    cols = [row[1] for row in cur.fetchall()]  # row[1] = name
    return col in cols

def add_col(cur, table, col, coltype):
    print(f"➕ Agregando columna {col} a {table}...")
    cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {coltype};")

def main():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    table = "pedido"  # <- lo normal si tu modelo se llama Pedido

    # Si tu tabla se llama diferente, imprime las tablas:
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cur.fetchall()]
    print("📌 Tablas en la BD:", tables)
    if table not in tables:
        raise SystemExit(f"❌ No existe la tabla '{table}'. Revisa el nombre en la lista de arriba.")

    # Agregar columnas si no existen
    if not col_exists(cur, table, "metodo_pago"):
        add_col(cur, table, "metodo_pago", "VARCHAR(20)")
    if not col_exists(cur, table, "monto_recibido"):
        add_col(cur, table, "monto_recibido", "FLOAT")
    if not col_exists(cur, table, "cambio"):
        add_col(cur, table, "cambio", "FLOAT")
    if not col_exists(cur, table, "fecha_cierre"):
        add_col(cur, table, "fecha_cierre", "DATETIME")

    con.commit()
    con.close()
    print("✅ Migración lista. Ya puedes guardar método de pago y cambio.")

if __name__ == "__main__":
    main()
