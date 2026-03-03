import pymysql
from pymysql import Error
import json
from datetime import datetime
from config import DB_CONFIG, TABLE_USERS, TABLE_STUDENTS, TABLE_ATTENDANCE
import hashlib


class Database:
    def __init__(self):
        self.connection = None
        self.create_database()
        self.connect()
        self.create_tables()

    def create_database(self):
        try:
            connection = pymysql.connect(
                host=DB_CONFIG['host'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                port=DB_CONFIG['port']
            )
            cursor = connection.cursor()
            db_name = DB_CONFIG['database']
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
            cursor.close()
            connection.close()
            print(f"Database '{DB_CONFIG['database']}' ready")
        except Error as e:
            print(f"Error creating database: {e}")

    def connect(self):
        try:
            self.connection = pymysql.connect(
                host=DB_CONFIG['host'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                database=DB_CONFIG['database'],
                port=DB_CONFIG['port'],
                autocommit=True
            )
            print("Database connected successfully")
        except Error as e:
            print(f"Error connecting to database: {e}")
            self.connection = None

    def create_tables(self):
        if not self.connection:
            return

        cursor = self.connection.cursor()

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_USERS} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                name VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'teacher',
                student_id VARCHAR(50) DEFAULT NULL,
                department VARCHAR(100) DEFAULT NULL,
                assigned_department VARCHAR(100) DEFAULT NULL,
                face_embedding TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Add new columns if they don't exist (for existing databases)
        try:
            cursor.execute(f"ALTER TABLE {TABLE_USERS} ADD COLUMN department VARCHAR(100) DEFAULT NULL")
        except:
            pass
        try:
            cursor.execute(f"ALTER TABLE {TABLE_USERS} ADD COLUMN assigned_department VARCHAR(100) DEFAULT NULL")
        except:
            pass

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_STUDENTS} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                roll_no VARCHAR(50) UNIQUE NOT NULL,
                department VARCHAR(100) NOT NULL,
                year VARCHAR(20) NOT NULL,
                email VARCHAR(255),
                phone VARCHAR(20),
                photo_path TEXT,
                face_embedding TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_ATTENDANCE} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id VARCHAR(50) NOT NULL,
                name VARCHAR(255) NOT NULL,
                department VARCHAR(100),
                date DATE NOT NULL,
                time TIME NOT NULL,
                period INT NOT NULL DEFAULT 1,
                status VARCHAR(20) DEFAULT 'Present',
                marked_by VARCHAR(100),
                marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_attendance (student_id, date, period)
            )
        """)

        # Claims table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS claims (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id VARCHAR(50) NOT NULL,
                date DATE NOT NULL,
                period INT NOT NULL,
                reason TEXT,
                status VARCHAR(20) DEFAULT 'Pending',
                teacher_id INT,
                teacher_response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Notifications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                message TEXT NOT NULL,
                type VARCHAR(50) DEFAULT 'info',
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.close()
        print("All tables created successfully")

        # Ensure default admin exists
        try:
            check_q = f"SELECT * FROM {TABLE_USERS} WHERE username = %s"
            existing = self.execute_query(check_q, ('admin',))
            if not existing:
                default_username = 'admin'
                default_password = hashlib.sha256('admin123'.encode()).hexdigest()
                default_name = 'Administrator'
                insert_q = f"INSERT INTO {TABLE_USERS} (username, password, name, role) VALUES (%s, %s, %s, %s)"
                self.execute_update(insert_q, (default_username, default_password, default_name, 'admin'))
                print("Default admin account created (username: admin, password: admin123)")
        except Exception:
            pass

        # Ensure default teacher exists
        try:
            check_q = f"SELECT * FROM {TABLE_USERS} WHERE username = %s"
            existing = self.execute_query(check_q, ('teacher',))
            if not existing:
                teacher_username = 'teacher'
                teacher_password = hashlib.sha256('teacher123'.encode()).hexdigest()
                teacher_name = 'John Teacher'
                teacher_dept = 'Computer Application'
                insert_q = f"INSERT INTO {TABLE_USERS} (username, password, name, role, assigned_department) VALUES (%s, %s, %s, %s, %s)"
                self.execute_update(insert_q, (teacher_username, teacher_password, teacher_name, 'teacher', teacher_dept))
                print("Default teacher account created (username: teacher, password: teacher123)")
        except Exception:
            pass

        # Ensure default student exists
        try:
            check_q = f"SELECT * FROM {TABLE_USERS} WHERE username = %s"
            existing = self.execute_query(check_q, ('student',))
            if not existing:
                student_username = 'student'
                student_password = hashlib.sha256('student123'.encode()).hexdigest()
                student_name = 'John Student'
                student_id = 'STU00001'
                student_dept = 'Computer Application'
                insert_q = f"INSERT INTO {TABLE_USERS} (username, password, name, role, student_id, department) VALUES (%s, %s, %s, %s, %s, %s)"
                self.execute_update(insert_q, (student_username, student_password, student_name, 'student', student_id, student_dept))
                print("Default student account created (username: student, password: student123)")
        except Exception:
            pass

    def execute_query(self, query, params=None):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if not self.connection:
                    self.connect()
                
                cursor = self.connection.cursor(pymysql.cursors.DictCursor)
                cursor.execute(query, params or ())
                results = cursor.fetchall()
                cursor.close()
                return results if results is not None else []
            except Error as e:
                print(f"Query error (attempt {attempt + 1}/{max_retries}): {e}")
                self.connect()
                if attempt == max_retries - 1:
                    return []
        return []

    def execute_update(self, query, params=None):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if not self.connection:
                    self.connect()
                
                cursor = self.connection.cursor()
                cursor.execute(query, params or ())
                self.connection.commit()
                cursor.close()
                return True
            except Error as e:
                print(f"Update error (attempt {attempt + 1}/{max_retries}): {e}")
                self.connect()
                if attempt == max_retries - 1:
                    return False
        return False

    def verify_user(self, username, password):
        query = f"SELECT * FROM {TABLE_USERS} WHERE username = %s AND password = %s"
        result = self.execute_query(query, (username, password))
        return result[0] if result else None

    def get_all_users(self):
        query = f"SELECT id, username, name, role, student_id, face_embedding FROM {TABLE_USERS}"
        return self.execute_query(query)

    def check_duplicate_face_user(self, face_embedding):
        """Check if face already exists for any user - STRICT threshold"""
        import numpy as np
        
        query = f"SELECT id, username, name, face_embedding FROM {TABLE_USERS}"
        all_users = self.execute_query(query)

        if not all_users:
            return None

        STRICT_THRESHOLD = 0.20
        
        for user in all_users:
            if user['face_embedding']:
                try:
                    stored_embedding = json.loads(user['face_embedding'])
                    
                    emb1 = np.array(face_embedding, dtype=np.float32)
                    emb2 = np.array(stored_embedding, dtype=np.float32)
                    
                    dot = np.dot(emb1, emb2)
                    norm1 = np.linalg.norm(emb1)
                    norm2 = np.linalg.norm(emb2)
                    similarity = dot / (norm1 * norm2 + 1e-6)
                    distance = 1 - similarity
                    
                    if distance < STRICT_THRESHOLD:
                        return {'id': user['id'], 'username': user['username'], 'name': user['name'], 'distance': distance}
                except:
                    pass
        return None

    def check_duplicate_face_student(self, face_embedding):
        """Check if face already exists for any student - STRICT threshold"""
        import numpy as np
        
        query = f"SELECT id, student_id, name, roll_no, face_embedding FROM {TABLE_STUDENTS}"
        all_students = self.execute_query(query)

        if not all_students:
            return None

        STRICT_THRESHOLD = 0.20
        
        for student in all_students:
            if student['face_embedding']:
                try:
                    stored_embedding = json.loads(student['face_embedding'])
                    
                    emb1 = np.array(face_embedding, dtype=np.float32)
                    emb2 = np.array(stored_embedding, dtype=np.float32)
                    
                    dot = np.dot(emb1, emb2)
                    norm1 = np.linalg.norm(emb1)
                    norm2 = np.linalg.norm(emb2)
                    similarity = dot / (norm1 * norm2 + 1e-6)
                    distance = 1 - similarity
                    
                    if distance < STRICT_THRESHOLD:
                        return {'id': student['id'], 'student_id': student['student_id'], 'name': student['name'], 'distance': distance}
                except:
                    pass
        return None

    def get_attendance_trend(self, days=7):
        from datetime import timedelta
        query = f"""
        SELECT DATE(date) as attendance_date, COUNT(DISTINCT student_id) as present_count
        FROM {TABLE_ATTENDANCE}
        WHERE date >= DATE_SUB(CURDATE(), INTERVAL {days} DAY)
        GROUP BY DATE(date)
        ORDER BY attendance_date ASC
        """
        result = self.execute_query(query)
        
        # Get total students safely
        stats = self.get_attendance_stats()
        total_students = stats.get('total_students', 0) if stats else 0
        
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

    def add_student(self, student_id, name, roll_no, department, year, email, phone, photo_path, face_embedding):
        query = f"""
            INSERT INTO {TABLE_STUDENTS} (student_id, name, roll_no, department, year, email, phone, photo_path, face_embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        emb = json.dumps(face_embedding) if face_embedding is not None else None
        return self.execute_update(query, (student_id, name, roll_no, department, year, email, phone, photo_path, emb))

    def update_student(self, id, name, roll_no, department, year, email, phone):
        query = f"UPDATE {TABLE_STUDENTS} SET name=%s, roll_no=%s, department=%s, year=%s, email=%s, phone=%s WHERE id=%s"
        return self.execute_update(query, (name, roll_no, department, year, email, phone, id))

    def update_student_face(self, student_id, face_embedding, photo_path=None):
        query = f"UPDATE {TABLE_STUDENTS} SET face_embedding=%s, photo_path=COALESCE(%s, photo_path) WHERE student_id=%s"
        emb = json.dumps(face_embedding) if face_embedding is not None else None
        return self.execute_update(query, (emb, photo_path, student_id))

    def delete_student(self, id):
        query = f"DELETE FROM {TABLE_STUDENTS} WHERE id = %s"
        return self.execute_update(query, (id,))

    def get_all_students(self):
        query = f"SELECT * FROM {TABLE_STUDENTS} ORDER BY name"
        return self.execute_query(query)

    def search_students(self, search_term, search_by='name'):
        query = f"SELECT * FROM {TABLE_STUDENTS} WHERE {search_by} LIKE %s ORDER BY name"
        return self.execute_query(query, (f'%{search_term}%',))

    def get_student_by_id(self, student_id):
        query = f"SELECT * FROM {TABLE_STUDENTS} WHERE student_id = %s"
        result = self.execute_query(query, (student_id,))
        return result[0] if result else None

    def mark_attendance(self, student_id, name, department, date, time, period=1, status='Present', marked_by=None):
        if hasattr(date, 'isoformat'):
            date_str = date.isoformat()
        else:
            date_str = str(date)
            
        check_query = f"SELECT * FROM {TABLE_ATTENDANCE} WHERE student_id = %s AND date = %s AND period = %s"
        existing = self.execute_query(check_query, (student_id, date_str, period))

        if existing:
            return False, f"Attendance already marked for Period {period} today"

        # Check if another teacher in the same department has already marked this slot
        # (This is a simplified version of slot locking)
        slot_lock_query = f"SELECT * FROM {TABLE_ATTENDANCE} WHERE department = %s AND date = %s AND period = %s AND marked_by != %s"
        other_teacher = self.execute_query(slot_lock_query, (department, date_str, period, marked_by))
        if other_teacher:
             return False, f"Period {period} for {department} has already been marked by another teacher"

        query = f"""
            INSERT INTO {TABLE_ATTENDANCE} (student_id, name, department, date, time, period, status, marked_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        success = self.execute_update(query, (student_id, name, department, date_str, str(time), period, status, marked_by))
        
        if success:
            print(f"Attendance marked: {name} ({student_id}) on {date_str} P{period}")
            
            # If absent, create a notification
            if status == 'Absent':
                self.add_notification_by_student_id(student_id, f"You were marked absent for Period {period} on {date_str}.", "warning")
        
        return success, "Attendance marked successfully" if success else "Failed to mark attendance"

    def get_attendance(self, date=None, department=None, name=None):
        query = f"SELECT * FROM {TABLE_ATTENDANCE} WHERE 1=1"
        params = []

        if date:
            if hasattr(date, 'isoformat'):
                date = date.isoformat()
            query += " AND date = %s"
            params.append(date)
        if department:
            query += " AND department LIKE %s"
            params.append(f'%{department}%')
        if name:
            query += " AND name LIKE %s"
            params.append(f'%{name}%')

        query += " ORDER BY date DESC, time DESC"
        return self.execute_query(query, tuple(params))

    def get_today_attendance(self):
        today = datetime.now().date()
        return self.get_attendance(date=today)

    def get_attendance_stats(self):
        today = datetime.now().date()
        if hasattr(today, 'isoformat'):
            today_str = today.isoformat()
        else:
            today_str = str(today)

        # Get total students
        total_query = f"SELECT COUNT(*) as cnt FROM {TABLE_STUDENTS}"
        total = self.execute_query(total_query)
        total_students = 0
        if total and len(total) > 0:
            total_students = total[0].get('cnt', 0) or 0

        # Get present count
        present_query = f"SELECT COUNT(*) as cnt FROM {TABLE_ATTENDANCE} WHERE date = %s"
        present = self.execute_query(present_query, (today_str,))
        present_today = 0
        if present and len(present) > 0:
            present_today = present[0].get('cnt', 0) or 0

        absent_today = total_students - present_today

        return {'total_students': total_students, 'present_today': present_today, 'absent_today': absent_today}

    def delete_attendance(self, id):
        query = f"DELETE FROM {TABLE_ATTENDANCE} WHERE id = %s"
        return self.execute_update(query, (id,))

    def clear_all_attendance(self):
        query = f"TRUNCATE TABLE {TABLE_ATTENDANCE}"
        return self.execute_update(query)

    def close(self):
        if self.connection:
            self.connection.close()
            print("Database connection closed")

    # ========== Teacher Management Methods ==========
    
    def get_all_teachers(self):
        """Get all teachers with their assigned departments"""
        query = f"SELECT id, username, name, role, assigned_department, created_at FROM {TABLE_USERS} WHERE role = 'teacher' ORDER BY name"
        return self.execute_query(query)

    def get_teacher_by_id(self, teacher_id):
        """Get teacher by ID"""
        query = f"SELECT id, username, name, role, assigned_department FROM {TABLE_USERS} WHERE id = %s AND role = 'teacher'"
        result = self.execute_query(query, (teacher_id,))
        return result[0] if result else None

    def add_teacher(self, username, password, name, assigned_department):
        """Add a new teacher"""
        hashed = hashlib.sha256(password.encode()).hexdigest()
        query = f"INSERT INTO {TABLE_USERS} (username, password, name, role, assigned_department) VALUES (%s, %s, %s, %s, %s)"
        return self.execute_update(query, (username, hashed, name, 'teacher', assigned_department))

    def update_teacher(self, teacher_id, name, assigned_department):
        """Update teacher details"""
        query = f"UPDATE {TABLE_USERS} SET name = %s, assigned_department = %s WHERE id = %s AND role = 'teacher'"
        return self.execute_update(query, (name, assigned_department, teacher_id))

    def delete_teacher(self, teacher_id):
        """Delete a teacher"""
        query = f"DELETE FROM {TABLE_USERS} WHERE id = %s AND role = 'teacher'"
        return self.execute_update(query, (teacher_id,))

    def get_teachers_by_department(self, department):
        """Get all teachers for a specific department"""
        query = f"SELECT id, username, name, role, assigned_department FROM {TABLE_USERS} WHERE role = 'teacher' AND assigned_department = %s ORDER BY name"
        return self.execute_query(query, (department,))

    # ========== Student Management by Department ==========
    
    def get_students_by_department(self, department):
        """Get all students for a specific department"""
        query = f"SELECT * FROM {TABLE_STUDENTS} WHERE department = %s ORDER BY name"
        return self.execute_query(query, (department,))

    def search_students_by_department(self, department, search_term):
        """Search students in a specific department"""
        query = f"SELECT * FROM {TABLE_STUDENTS} WHERE department = %s AND (name LIKE %s OR student_id LIKE %s OR roll_no LIKE %s) ORDER BY name"
        search = f'%{search_term}%'
        return self.execute_query(query, (department, search, search, search))

    # ========== Attendance Methods ==========
    
    def get_attendance_by_student(self, student_id):
        """Get all attendance records for a specific student"""
        query = f"SELECT * FROM {TABLE_ATTENDANCE} WHERE student_id = %s ORDER BY date DESC, time DESC"
        return self.execute_query(query, (student_id,))

    def get_student_attendance_stats(self, student_id):
        """Get attendance statistics for a specific student"""
        # Get total days student should have attended (from enrollment)
        total_query = f"SELECT COUNT(DISTINCT date) as total_days FROM {TABLE_ATTENDANCE}"
        total_result = self.execute_query(total_query)
        total_days = total_result[0]['total_days'] if total_result else 0
        
        # Get present days
        present_query = f"SELECT COUNT(*) as present_days FROM {TABLE_ATTENDANCE} WHERE student_id = %s AND status = 'Present'"
        present_result = self.execute_query(present_query, (student_id,))
        present_days = present_result[0]['present_days'] if present_result else 0
        
        # Get today's attendance
        today = datetime.now().date()
        today_str = today.isoformat() if hasattr(today, 'isoformat') else str(today)
        today_query = f"SELECT * FROM {TABLE_ATTENDANCE} WHERE student_id = %s AND date = %s"
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

    def mark_attendance_manual(self, student_id, name, department, date, time, status='Present', period=1, marked_by=None):
        """Manually mark attendance (allows marking for any date and period)"""
        if hasattr(date, 'isoformat'):
            date_str = date.isoformat()
        else:
            date_str = str(date)
            
        # Check if already marked for this date and period
        check_query = f"SELECT * FROM {TABLE_ATTENDANCE} WHERE student_id = %s AND date = %s AND period = %s"
        existing = self.execute_query(check_query, (student_id, date_str, period))

        if existing:
            return False, f"Attendance already marked for Period {period} on this date"

        # Check for slot locking (another teacher in same dept)
        slot_lock_query = f"SELECT * FROM {TABLE_ATTENDANCE} WHERE department = %s AND date = %s AND period = %s AND marked_by != %s"
        other_teacher = self.execute_query(slot_lock_query, (department, date_str, period, marked_by))
        if other_teacher:
             return False, f"Period {period} for {department} has already been marked by another teacher"

        query = f"""
            INSERT INTO {TABLE_ATTENDANCE} (student_id, name, department, date, time, period, status, marked_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        success = self.execute_update(query, (student_id, name, department, date_str, str(time), period, status, marked_by))
        
        if success:
            print(f"Manual attendance marked: {name} ({student_id}) on {date_str} P{period} - {status}")
            if status == 'Absent':
                self.add_notification_by_student_id(student_id, f"You were marked absent for Period {period} on {date_str}.", "warning")
        
        return success, "Attendance marked successfully" if success else "Failed to mark attendance"

    def get_attendance_by_department(self, department, date=None):
        """Get attendance for a specific department"""
        query = f"SELECT * FROM {TABLE_ATTENDANCE} WHERE department = %s"
        params = [department]
        
        if date:
            if hasattr(date, 'isoformat'):
                date = date.isoformat()
            query += " AND date = %s"
            params.append(date)
        
        query += " ORDER BY date DESC, time DESC"
        return self.execute_query(query, tuple(params))

    def get_department_attendance_stats(self, department):
        """Get attendance statistics for a specific department"""
        today = datetime.now().date()
        today_str = today.isoformat() if hasattr(today, 'isoformat') else str(today)
        
        # Get total students in department
        total_query = f"SELECT COUNT(*) as cnt FROM {TABLE_STUDENTS} WHERE department = %s"
        total = self.execute_query(total_query, (department,))
        total_students = total[0]['cnt'] if total else 0
        
        # Get present count for today in department
        present_query = f"SELECT COUNT(*) as cnt FROM {TABLE_ATTENDANCE} WHERE department = %s AND date = %s"
        present = self.execute_query(present_query, (department, today_str))
        present_today = present[0]['cnt'] if present else 0
        
        absent_today = total_students - present_today
        
        return {
            'total_students': total_students,
            'present_today': present_today,
            'absent_today': absent_today,
            'department': department
        }

    # ========== Department Methods ==========
    
    def get_departments(self):
        """Get list of all departments from students table"""
        query = f"SELECT DISTINCT department FROM {TABLE_STUDENTS} ORDER BY department"
        result = self.execute_query(query)
        return [r['department'] for r in result]

    def get_all_departments_list():
        """Get list of all predefined departments"""
        return [
            "Computer Application",
            "Commerce",
            "Management Studies",
            "Geology",
            "Psychology",
            "Social Work"
        ]

    # ========== Student Login Methods ==========
    
    def create_student_login(self, username, password, student_id, name, department):
        """Create login credentials for a student in the users table"""
        hashed = hashlib.sha256(password.encode()).hexdigest()
        query = f"""
            INSERT INTO {TABLE_USERS} (username, password, name, role, student_id, department)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        return self.execute_update(query, (username, hashed, name, 'student', student_id, department))

    def get_student_login(self, student_id):
        """Get login credentials for a student"""
        query = f"SELECT id, username, student_id FROM {TABLE_USERS} WHERE student_id = %s AND role = 'student'"
        result = self.execute_query(query, (student_id,))
        return result[0] if result else None

    def update_student_login(self, student_id, username, password):
        """Update login credentials for a student"""
        hashed = hashlib.sha256(password.encode()).hexdigest()
        query = f"UPDATE {TABLE_USERS} SET username = %s, password = %s WHERE student_id = %s AND role = 'student'"
        return self.execute_update(query, (username, hashed, student_id))

    # ========== Claim Methods ==========

    def add_claim(self, student_id, date, period, reason):
        """Add a new attendance claim"""
        query = "INSERT INTO claims (student_id, date, period, reason) VALUES (%s, %s, %s, %s)"
        return self.execute_update(query, (student_id, date, period, reason))

    def get_claims_by_student(self, student_id):
        """Get all claims for a student"""
        query = "SELECT * FROM claims WHERE student_id = %s ORDER BY created_at DESC"
        return self.execute_query(query, (student_id,))

    def get_pending_claims_by_department(self, department):
        """Get pending claims for a teacher's department"""
        query = """
            SELECT c.*, s.name, s.department 
            FROM claims c 
            JOIN students s ON c.student_id = s.student_id 
            WHERE s.department = %s AND c.status = 'Pending'
            ORDER BY c.created_at ASC
        """
        return self.execute_query(query, (department,))

    def update_claim_status(self, claim_id, teacher_id, status, response):
        """Approve or deny a claim"""
        query = "UPDATE claims SET status = %s, teacher_id = %s, teacher_response = %s WHERE id = %s"
        success = self.execute_update(query, (status, teacher_id, response, claim_id))
        
        if success and status == 'Approved':
            # Update attendance status to Present or Excused
            claim = self.execute_query("SELECT * FROM claims WHERE id = %s", (claim_id,))
            if claim:
                c = claim[0]
                self.execute_update(
                    f"UPDATE {TABLE_ATTENDANCE} SET status = 'Present' WHERE student_id = %s AND date = %s AND period = %s",
                    (c['student_id'], c['date'], c['period'])
                )
                self.add_notification_by_student_id(c['student_id'], f"Your claim for {c['date']} P{c['period']} was approved.", "success")
        elif success and status == 'Denied':
             claim = self.execute_query("SELECT * FROM claims WHERE id = %s", (claim_id,))
             if claim:
                 self.add_notification_by_student_id(claim[0]['student_id'], f"Your claim for {claim[0]['date']} P{claim[0]['period']} was denied.", "danger")
                 
        return success

    # ========== Notification Methods ==========

    def add_notification(self, user_id, message, type='info'):
        """Add a notification for a user"""
        query = "INSERT INTO notifications (user_id, message, type) VALUES (%s, %s, %s)"
        return self.execute_update(query, (user_id, message, type))

    def add_notification_by_student_id(self, student_id, message, type='info'):
        """Add notification for student using their student_id"""
        user_query = f"SELECT id FROM {TABLE_USERS} WHERE student_id = %s"
        user = self.execute_query(user_query, (student_id,))
        if user:
            return self.add_notification(user[0]['id'], message, type)
        return False

    def get_notifications(self, user_id):
        """Get all notifications for a user"""
        query = "SELECT * FROM notifications WHERE user_id = %s ORDER BY created_at DESC LIMIT 20"
        return self.execute_query(query, (user_id,))

    def mark_notifications_read(self, user_id):
        """Mark all notifications as read"""
        query = "UPDATE notifications SET is_read = TRUE WHERE user_id = %s"
        return self.execute_update(query, (user_id,))


db = Database()
