import sqlite3
import datetime
import os

DB_PATH = "attendance.db"

def init_db():
    """
    Initializes the SQLite database with support for Registration Numbers and Courses.
    Adds missing columns to existing databases if they are missing.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table for logged attendance
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            reg_no TEXT,
            course TEXT,
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
            course TEXT,
            added_at TEXT NOT NULL
        )
    ''')
    
    # Schema Migration: Add missing columns if they don't exist
    columns_to_add = [
        ("attendance", "reg_no", "TEXT"),
        ("attendance", "course", "TEXT"),
        ("users", "reg_no", "TEXT"),
        ("users", "course", "TEXT")
    ]
    
    for table, col, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError:
            pass # Column already exists
            
    conn.commit()
    conn.close()

def mark_attendance(identity):
    """
    Marks attendance for a user. Identity is in the format "Name_RegNo".
    Fetches the assigned course from the users table.
    """
    if "_" in identity:
        name, reg_no = identity.split("_", 1)
    else:
        name, reg_no = identity, "Unknown"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Fetch the user's assigned course
    cursor.execute("SELECT course FROM users WHERE reg_no=?", (reg_no,))
    user_data = cursor.fetchone()
    course = user_data[0] if user_data else "General"
    
    now = datetime.datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")
    
    # Check for cooldown (5 minutes)
    cursor.execute("SELECT date, time FROM attendance WHERE reg_no=? AND date=? ORDER BY time DESC LIMIT 1", (reg_no, current_date))
    last_log = cursor.fetchone()
    
    should_log = False
    if last_log:
        last_recorded_time = datetime.datetime.strptime(f"{last_log[0]} {last_log[1]}", "%Y-%m-%d %H:%M:%S")
        time_diff = (now - last_recorded_time).total_seconds() / 60 
        
        if time_diff >= 5:
            should_log = True
        else:
            conn.close()
            return False, f"Already recorded {int(time_diff)} mins ago. Wait {int(5-time_diff)} more mins."
    else:
        should_log = True
    
    if should_log:
        cursor.execute("INSERT INTO attendance (name, reg_no, course, date, time, status) VALUES (?, ?, ?, ?, ?, ?)",
                       (name, reg_no, course, current_date, current_time, "Present"))
        conn.commit()
        conn.close()
        return True, "Attendance marked successfully."
    
    conn.close()
    return False, "Error marking attendance."

def get_attendance_history():
    """
    Retrieves all records from the attendance table including course and rowid.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, reg_no, course, date, time, status, rowid FROM attendance ORDER BY date DESC, time DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_attendance_log(rowid):
    """
    Deletes a specific attendance record by rowid.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM attendance WHERE rowid=?", (rowid,))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()

def get_registered_users():
    """
    Retrieves all records from the users table, including internal rowid and course.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, reg_no, added_at, rowid, course FROM users ORDER BY name ASC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def register_user_db(name, reg_no, course):
    """
    Registers a new user in the database with an assigned course.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (name, reg_no, course, added_at) VALUES (?, ?, ?, ?)", 
                       (name, reg_no, course, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def delete_user_db(rowid, reg_no):
    """
    Deletes a user by rowid and clears their attendance history by reg_no.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE rowid=?", (rowid,))
        if reg_no:
            cursor.execute("DELETE FROM attendance WHERE reg_no=?", (reg_no,))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()

def update_user_db(rowid, old_reg_no, new_name, new_reg_no, new_course):
    """
    Updates a user's record including their course.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET name=?, reg_no=?, course=? WHERE rowid=?", (new_name, new_reg_no, new_course, rowid))
        if old_reg_no and old_reg_no != new_reg_no:
            cursor.execute("UPDATE attendance SET name=?, reg_no=?, course=? WHERE reg_no=?", (new_name, new_reg_no, new_course, old_reg_no))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
