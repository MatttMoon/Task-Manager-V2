import sqlite3

def get_connection():
    return sqlite3.connect("task_manager.db")

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            xp INTEGER DEFAULT 0
        )
    """)

    # Tasks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            complete BOOLEAN DEFAULT 0,
            due_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()

def validate_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

def add_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_tasks(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE user_id = ?", (user_id,))
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def add_task(user_id, title, description, due_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (user_id, title, description, complete, due_date) VALUES (?, ?, ?, 0, ?)",
        (user_id, title, description, due_date)
    )
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def complete_task(task_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT complete FROM tasks WHERE id = ?", (task_id,))
    result = cursor.fetchone()

    if result and result[0] == 0:
        cursor.execute("UPDATE tasks SET complete = 1 WHERE id = ?", (task_id,))
        cursor.execute("UPDATE users SET xp = xp + 10 WHERE id = ?", (user_id,))
        conn.commit()
        print(f"[DB] Marking task {task_id} complete for user {user_id}")

    conn.close()

def get_user_xp(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT xp FROM users WHERE id = ?", (user_id,))
    xp = cursor.fetchone()[0]
    conn.close()
    return xp
