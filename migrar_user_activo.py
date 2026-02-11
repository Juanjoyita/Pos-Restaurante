import sqlite3

DB_PATH = "instance/database.db"

def col_exists(cur, table, col):
    cur.execute(f"PRAGMA table_info({table});")
    cols = [row[1] for row in cur.fetchall()]
    return col in cols

def main():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # Ver tablas
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cur.fetchall()]
    print("📌 Tablas:", tables)

    table = "user"
    if table not in tables:
        raise SystemExit("❌ No existe la tabla 'user'. Revisa el nombre en la lista.")

    if not col_exists(cur, table, "activo"):
        print("➕ Agregando columna activo...")
        cur.execute("ALTER TABLE user ADD COLUMN activo BOOLEAN DEFAULT 1;")

    # Asegurar que usuarios existentes queden activos (por si quedan null)
    cur.execute("UPDATE user SET activo=1 WHERE activo IS NULL;")

    con.commit()
    con.close()
    print("✅ Migración lista. Campo activo agregado.")

if __name__ == "__main__":
    main()
