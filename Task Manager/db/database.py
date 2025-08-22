# db.py
import sqlite3
from datetime import datetime

DB_FILE = "tasks.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            xp INTEGER DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            completed INTEGER DEFAULT 0,
            due_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    conn.commit()
    conn.close()

# --- Users ---------------------------------------------------------------

def add_user(username: str, password: str) -> bool:
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE users ADD COLUMN password TEXT DEFAULT ''")
        conn.commit()
    except Exception:
        pass  # column already exists

    cur.execute(
        "INSERT OR IGNORE INTO users (username, password, xp) VALUES (?, ?, 0)",
        (username.strip(), password.strip()),
    )
    created = (cur.rowcount == 1)
    conn.commit(); conn.close()
    return created

def validate_user(username: str, password: str):
    conn = get_connection(); cur = conn.cursor()
    cur.execute(
        "SELECT id, username, xp FROM users WHERE username=? AND password=?",
        (username.strip(), password.strip()),
    )
    row = cur.fetchone(); conn.close()
    return (row["id"], row["username"], row["xp"]) if row else None

def add_task(user_id, title, description, due_date):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (user_id, title, description, due_date) VALUES (?, ?, ?, ?)",
        (user_id, title, description, due_date)
    )
    conn.commit()
    conn.close()

def get_tasks(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, user_id, title, description, completed, due_date FROM tasks WHERE user_id = ? ORDER BY due_date, id",
        (user_id,)
    )
    tasks = cur.fetchall()
    conn.close()
    return tasks

def complete_task(task_id, user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET completed = 1 WHERE id = ? AND user_id = ?", (task_id, user_id))
    cur.execute("UPDATE users SET xp = xp + 10 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def get_user_xp(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT xp FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    xp = row['xp'] if row else 0
    conn.close()
    return xp