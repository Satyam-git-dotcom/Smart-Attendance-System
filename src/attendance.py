import sqlite3
import datetime
import os

DB_PATH = "attendance.db"

def init_db():
    """
    Initializes the SQLite database with support for Registration Numbers.
    Adds the column to existing databases if it's missing.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table for logged attendance
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            reg_no TEXT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')
    
    # Table for registered users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            name TEXT NOT NULL,
            reg_no TEXT PRIMARY KEY,
            added_at TEXT NOT NULL
        )
    ''')
    
    # Schema Migration: Add reg_no column to existing tables if missing
    try:
        cursor.execute("ALTER TABLE attendance ADD COLUMN reg_no TEXT")
    except sqlite3.OperationalError:
        pass # Column already exists
    
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN reg_no TEXT")
    except sqlite3.OperationalError:
        pass # Column already exists

    conn.commit()
    conn.close()

def mark_attendance(identity):
    """
    Marks attendance for a user. Identity is in the format "Name_RegNo".
    Ensures that attendance is marked only once per day.
    """
    if "_" in identity:
        name, reg_no = identity.split("_", 1)
    else:
        name, reg_no = identity, "Unknown"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")
    
    # Check if attendance is already marked for today
    cursor.execute("SELECT * FROM attendance WHERE reg_no=? AND date=?", (reg_no, current_date))
    existing = cursor.fetchone()
    
    if not existing:
        cursor.execute("INSERT INTO attendance (name, reg_no, date, time, status) VALUES (?, ?, ?, ?, ?)",
                       (name, reg_no, current_date, current_time, "Present"))
        conn.commit()
        conn.close()
        return True, "Attendance marked successfully."
    
    conn.close()
    return False, "Attendance already marked for today."

def get_attendance_history():
    """
    Retrieves all records from the attendance table.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, reg_no, date, time, status FROM attendance ORDER BY date DESC, time DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_registered_users():
    """
    Retrieves all records from the users table.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, reg_no, added_at FROM users ORDER BY name ASC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def register_user_db(name, reg_no):
    """
    Registers a new user in the database.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (name, reg_no, added_at) VALUES (?, ?, ?)", 
                       (name, reg_no, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def delete_user_db(reg_no):
    """
    Deletes a user from the users table.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE reg_no=?", (reg_no,))
    conn.commit()
    conn.close()
    return True

def update_user_db(old_reg_no, new_name, new_reg_no):
    """
    Updates a user's record in the database.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET name=?, reg_no=? WHERE reg_no=?", (new_name, new_reg_no, old_reg_no))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
