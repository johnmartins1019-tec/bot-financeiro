import sqlite3

def conectar():
    conn = sqlite3.connect("gastos.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            valor REAL,
            categoria TEXT,
            data TEXT
        )
    ''')
    conn.commit()
    return conn

def registrar_gasto(user_id, valor, categoria, data):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO gastos (user_id, valor, categoria, data) VALUES (?, ?, ?, ?)",
                   (user_id, valor, categoria, data))
    conn.commit()
    conn.close()

def obter_total(user_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(valor) FROM gastos WHERE user_id = ?", (user_id,))
    total = cursor.fetchone()[0]
    conn.close()
    return total or 0

def obter_extrato(user_id, limite=5):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT valor, categoria, data FROM gastos WHERE user_id = ? ORDER BY id DESC LIMIT ?",
                   (user_id, limite))
    resultado = cursor.fetchall()
    conn.close()
    return resultado

def gastos_por_categoria(user_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT categoria, SUM(valor)
        FROM gastos
        WHERE user_id = ?
        GROUP BY categoria
    """, (user_id,))
    dados = cursor.fetchall()
    conn.close()
    return dados

def gastos_por_dia(user_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DATE(data), SUM(valor)
        FROM gastos
        WHERE user_id = ?
        GROUP BY DATE(data)
        ORDER BY DATE(data)
    """, (user_id,))
    dados = cursor.fetchall()
    conn.close()
    return dados
