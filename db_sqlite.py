"""
SQLite Database for Face Recognition Attendance System
Alternative to MySQL - works without external database server
"""

import sqlite3
import json
from datetime import datetime
from config import TABLE_USERS, TABLE_STUDENTS, TABLE_ATTENDANCE
import hashlib
import os

class Database:
    def __init__(self):
        self.db_file = 'attendance.db'
        self.create_tables()

    def connect(self):
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn

    def create_tables(self):
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_USERS} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                name TEXT NOT NULL,
                role TEXT DEFAULT 'teacher',
                student_id TEXT,
                department TEXT,
                assigned_department TEXT,
                face_embedding TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_STUDENTS} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                roll_no TEXT UNIQUE NOT NULL,
                department TEXT NOT NULL,
                year TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                photo_path TEXT,
                face_embedding TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_ATTENDANCE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                name TEXT NOT NULL,
                department TEXT,
                date DATE NOT NULL,
                time TIME NOT NULL,
                status TEXT DEFAULT 'Present',
                marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        
        # Create default admin
        cursor.execute(f"SELECT * FROM {TABLE_USERS} WHERE username = ?", ('admin',))
        if not cursor.fetchone():
            default_password = hashlib.sha256('admin123'.encode()).hexdigest()
            cursor.execute(f"INSERT INTO {TABLE_USERS} (username, password, name, role) VALUES (?, ?, ?, ?)",
                          ('admin', default_password, 'Administrator', 'admin'))
            print("Default admin account created (username: admin, password: admin123)")

        # Create default teacher
        cursor.execute(f"SELECT * FROM {TABLE_USERS} WHERE username = ?", ('teacher',))
        if not cursor.fetchone():
            teacher_password = hashlib.sha256('teacher123'.encode()).hexdigest()
            cursor.execute(f"INSERT INTO {TABLE_USERS} (username, password, name, role, assigned_department) VALUES (?, ?, ?, ?, ?)",
                          ('teacher', teacher_password, 'John Teacher', 'teacher', 'Computer Application'))
            print("Default teacher account created (username: teacher, password: teacher123)")

        # Create default student
        cursor.execute(f"SELECT * FROM {TABLE_USERS} WHERE username = ?", ('student',))
        if not cursor.fetchone():
            student_password = hashlib.sha256('student123'.encode()).hexdigest()
            cursor.execute(f"INSERT INTO {TABLE_USERS} (username, password, name, role, student_id, department) VALUES (?, ?, ?, ?, ?, ?)",
                          ('student', student_password, 'John Student', 'student', 'STU00001', 'Computer Application'))
            print("Default student account created (username: student, password: student123)")

        conn.commit()
        conn.close()
        print("SQLite database ready!")

    def execute_query(self, query, params=None):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        results = cursor.fetchall()
        conn.close()
        # Convert to list of dicts
        if results:
            return [dict(row) for row in results]
        return []

    def execute_update(self, query, params=None):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()
        conn.close()
        return True

    def verify_user(self, username, password):
        query = f"SELECT * FROM {TABLE_USERS} WHERE username = ? AND password = ?"
        result = self.execute_query(query, (username, password))
        return result[0] if result else None

    def get_all_users(self):
        query = f"SELECT id, username, name, role, student_id, face_embedding FROM {TABLE_USERS}"
        return self.execute_query(query)

    def get_all_students(self):
        query = f"SELECT * FROM {TABLE_STUDENTS} ORDER BY name"
        return self.execute_query(query)

    def get_student_by_id(self, student_id):
        query = f"SELECT * FROM {TABLE_STUDENTS} WHERE student_id = ?"
        result = self.execute_query(query, (student_id,))
        return result[0] if result else None

    def add_student(self, student_id, name, roll_no, department, year, email, phone, photo_path, face_embedding):
        emb = json.dumps(face_embedding) if face_embedding is not None else None
        query = f"INSERT INTO {TABLE_STUDENTS} (student_id, name, roll_no, department, year, email, phone, photo_path, face_embedding) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
        return self.execute_update(query, (student_id, name, roll_no, department, year, email, phone, photo_path, emb))

    def delete_student(self, id):
        query = f"DELETE FROM {TABLE_STUDENTS} WHERE id = ?"
        return self.execute_update(query, (id,))

    def update_student_face(self, student_id, face_embedding, photo_path=None):
        emb = json.dumps(face_embedding) if face_embedding is not None else None
        query = f"UPDATE {TABLE_STUDENTS} SET face_embedding = ? WHERE student_id = ?"
        return self.execute_update(query, (emb, student_id))

    def mark_attendance(self, student_id, name, department, date, time, status='Present'):
        if hasattr(date, 'isoformat'):
            date_str = date.isoformat()
        else:
            date_str = str(date)
            
        check_query = f"SELECT * FROM {TABLE_ATTENDANCE} WHERE student_id = ? AND date = ?"
        existing = self.execute_query(check_query, (student_id, date_str))

        if existing:
            return False, "Attendance already marked today"

        query = f"INSERT INTO {TABLE_ATTENDANCE} (student_id, name, department, date, time, status) VALUES (?, ?, ?, ?, ?, ?)"
        success = self.execute_update(query, (student_id, name, department, date_str, str(time), status))
        
        if success:
            print(f"Attendance marked: {name} ({student_id}) on {date_str}")
        
        return success, "Attendance marked successfully" if success else "Failed to mark attendance"

    def get_attendance(self, date=None, department=None, name=None):
        query = f"SELECT * FROM {TABLE_ATTENDANCE} WHERE 1=1"
        params = []

        if date:
            if hasattr(date, 'isoformat'):
                date = date.isoformat()
            query += " AND date = ?"
            params.append(date)
        if department:
            query += " AND department LIKE ?"
            params.append(f'%{department}%')
        if name:
            query += " AND name LIKE ?"
            params.append(f'%{name}%')

        query += " ORDER BY date DESC, time DESC"
        return self.execute_query(query, tuple(params))

    def get_attendance_stats(self):
        today = datetime.now().date()
        if hasattr(today, 'isoformat'):
            today_str = today.isoformat()
        else:
            today_str = str(today)

        total_query = f"SELECT COUNT(*) as cnt FROM {TABLE_STUDENTS}"
        total = self.execute_query(total_query)
        total_students = total[0]['cnt'] if total else 0

        present_query = f"SELECT COUNT(*) as cnt FROM {TABLE_ATTENDANCE} WHERE date = ?"
        present = self.execute_query(present_query, (today_str,))
        present_today = present[0]['cnt'] if present else 0

        absent_today = total_students - present_today

        return {'total_students': total_students, 'present_today': present_today, 'absent_today': absent_today}

    def get_attendance_trend(self, days=7):
        from datetime import timedelta
        query = f"""
        SELECT DATE(date) as attendance_date, COUNT(DISTINCT student_id) as present_count
        FROM {TABLE_ATTENDANCE}
        WHERE date >= DATE('now', '-{days} days')
        GROUP BY DATE(date)
        ORDER BY attendance_date ASC
        """
        result = self.execute_query(query)
        
        stats = self.get_attendance_stats()
        total_students = stats.get('total_students', 0)
        
        trend_data = []
        current_date = datetime.now().date() - timedelta(days=days - 1)
        attendance_dict = {}
        
        if result:
            for row in result:
                attendance_dict[row['attendance_date']] = row.get('present_count', 0)

        for i in range(days):
            date = current_date + timedelta(days=i)
            count = attendance_dict.get(date, 0)
            percentage = (count / total_students * 100) if total_students > 0 else 0
            trend_data.append({'date': date, 'count': count, 'percentage': round(percentage, 1)})

        return trend_data

    # Teacher Management Methods
    def get_all_teachers(self):
        query = f"SELECT id, username, name, role, assigned_department, created_at FROM {TABLE_USERS} WHERE role = 'teacher' ORDER BY name"
        return self.execute_query(query)

    def add_teacher(self, username, password, name, assigned_department):
        hashed = hashlib.sha256(password.encode()).hexdigest()
        query = f"INSERT INTO {TABLE_USERS} (username, password, name, role, assigned_department) VALUES (?, ?, ?, ?, ?)"
        return self.execute_update(query, (username, hashed, name, 'teacher', assigned_department))

    def update_teacher(self, teacher_id, name, assigned_department):
        query = f"UPDATE {TABLE_USERS} SET name = ?, assigned_department = ? WHERE id = ? AND role = 'teacher'"
        return self.execute_update(query, (name, assigned_department, teacher_id))

    def delete_teacher(self, teacher_id):
        query = f"DELETE FROM {TABLE_USERS} WHERE id = ? AND role = 'teacher'"
        return self.execute_update(query, (teacher_id,))

    def get_students_by_department(self, department):
        query = f"SELECT * FROM {TABLE_STUDENTS} WHERE department = ? ORDER BY name"
        return self.execute_query(query, (department,))

    def get_attendance_by_student(self, student_id):
        query = f"SELECT * FROM {TABLE_ATTENDANCE} WHERE student_id = ? ORDER BY date DESC, time DESC"
        return self.execute_query(query, (student_id,))

    def get_student_attendance_stats(self, student_id):
        total_query = f"SELECT COUNT(DISTINCT date) as total_days FROM {TABLE_ATTENDANCE}"
        total_result = self.execute_query(total_query)
        total_days = total_result[0]['total_days'] if total_result else 0
        
        present_query = f"SELECT COUNT(*) as present_days FROM {TABLE_ATTENDANCE} WHERE student_id = ? AND status = 'Present'"
        present_result = self.execute_query(present_query, (student_id,))
        present_days = present_result[0]['present_days'] if present_result else 0
        
        today = datetime.now().date()
        today_str = today.isoformat() if hasattr(today, 'isoformat') else str(today)
        today_query = f"SELECT * FROM {TABLE_ATTENDANCE} WHERE student_id = ? AND date = ?"
        today_result = self.execute_query(today_query, (student_id, today_str))
        marked_today = len(today_result) > 0
        
        percentage = (present_days / total_days * 100) if total_days > 0 else 0
        
        return {
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': total_days - present_days,
            'percentage': round(percentage, 1),
            'marked_today': marked_today
        }

    def mark_attendance_manual(self, student_id, name, department, date, time, status='Present'):
        if hasattr(date, 'isoformat'):
            date_str = date.isoformat()
        else:
            date_str = str(date)
            
        check_query = f"SELECT * FROM {TABLE_ATTENDANCE} WHERE student_id = ? AND date = ?"
        existing = self.execute_query(check_query, (student_id, date_str))

        if existing:
            return False, "Attendance already marked for this date"

        query = f"INSERT INTO {TABLE_ATTENDANCE} (student_id, name, department, date, time, status) VALUES (?, ?, ?, ?, ?, ?)"
        success = self.execute_update(query, (student_id, name, department, date_str, str(time), status))
        
        if success:
            print(f"Manual attendance marked: {name} ({student_id}) on {date_str} - {status}")
        
        return success, "Attendance marked successfully" if success else "Failed to mark attendance"

    def get_attendance_by_department(self, department, date=None):
        query = f"SELECT * FROM {TABLE_ATTENDANCE} WHERE department = ?"
        params = [department]
        
        if date:
            if hasattr(date, 'isoformat'):
                date = date.isoformat()
            query += " AND date = ?"
            params.append(date)
        
        query += " ORDER BY date DESC, time DESC"
        return self.execute_query(query, tuple(params))

    def get_department_attendance_stats(self, department):
        today = datetime.now().date()
        today_str = today.isoformat() if hasattr(today, 'isoformat') else str(today)
        
        total_query = f"SELECT COUNT(*) as cnt FROM {TABLE_STUDENTS} WHERE department = ?"
        total = self.execute_query(total_query, (department,))
        total_students = total[0]['cnt'] if total else 0
        
        present_query = f"SELECT COUNT(*) as cnt FROM {TABLE_ATTENDANCE} WHERE department = ? AND date = ?"
        present = self.execute_query(present_query, (department, today_str))
        present_today = present[0]['cnt'] if present else 0
        
        absent_today = total_students - present_today
        
        return {
            'total_students': total_students,
            'present_today': present_today,
            'absent_today': absent_today,
            'department': department
        }

    def check_duplicate_face_student(self, face_embedding):
        """Check if face already exists - simplified for SQLite"""
        return None  # Skip for now

    def search_students(self, search_term, search_by='name'):
        query = f"SELECT * FROM {TABLE_STUDENTS} WHERE {search_by} LIKE ? ORDER BY name"
        return self.execute_query(query, (f'%{search_term}%',))

    def search_students_by_department(self, department, search_term):
        query = f"SELECT * FROM {TABLE_STUDENTS} WHERE department = ? AND (name LIKE ? OR student_id LIKE ? OR roll_no LIKE ?) ORDER BY name"
        search = f'%{search_term}%'
        return self.execute_query(query, (department, search, search, search))

db = Database()
