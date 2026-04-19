# -*- coding: utf-8 -*-
"""
Tao bang users va 2 user ban dau (admin + sp1305).
Chay: python create_user.py
"""

import os
import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phieu_ck.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'viewer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def add_user(conn, username, password, role):
    pw_hash = generate_password_hash(password)
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, pw_hash, role),
        )
        conn.commit()
        print(f"[OK] User '{username}' (role={role}) da tao thanh cong.")
    except sqlite3.IntegrityError:
        print(f"[SKIP] User '{username}' da ton tai, bo qua.")


if __name__ == "__main__":
    conn = init_db()
    add_user(conn, "admin", "xinlayEOFFICE#002", "admin")
    add_user(conn, "sp1305", "Pnj@1305", "sp1305")
    conn.close()
    print(f"\nDatabase: {DB_PATH}")
