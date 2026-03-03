"""
Flask Web Application for Face Recognition Attendance System
Keeps the same backend (db.py, face_recognition_module.py) unchanged
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from functools import wraps
import hashlib
import json
import os
from datetime import datetime, timedelta

from db import db
from face_recognition_module import face_recognizer
from config import APP_TITLE, COLORS

app = Flask(__name__)
app.secret_key = 'face_recognition_attendance_secret_key_2024'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Warm up face recognizer on startup
print("🔄 Initializing face recognition...")
face_recognizer.warm_up()
print("✅ Face recognition ready")


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            if request.is_json:
                data = request.get_json()
                username = data.get('username', '').strip()
                password = data.get('password', '')
            else:
                username = request.form.get('username', '').strip()
                password = request.form.get('password', '')

            if not username or not password:
                if request.is_json:
                    return jsonify({'success': False, 'message': 'Please enter username and password'})
                return render_template('login.html', app_title=APP_TITLE, error='Please enter username and password')

            hashed = hashlib.sha256(password.encode()).hexdigest()
            print(f"Login attempt: username={username}, hashed={hashed[:20]}...")
            
            user = db.verify_user(username, hashed)
            print(f"User found: {user}")

            if user:
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['name'] = user['name']
                session['role'] = user['role']
                session['student_id'] = user.get('student_id')
                session['department'] = user.get('department') or user.get('assigned_department')
                session['assigned_department'] = user.get('assigned_department')
                session.modified = True
                
                print(f"Login successful for {username}, role: {user['role']}")
                
                return jsonify({
                    'success': True, 
                    'message': f'Welcome, {user["name"]}!',
                    'role': user['role']
                })
            else:
                if request.is_json:
                    return jsonify({'success': False, 'message': 'Invalid username or password'})
                return render_template('login.html', app_title=APP_TITLE, error='Invalid username or password')
        except Exception as e:
            print(f"Login error: {e}")
            import traceback
            traceback.print_exc()
            if request.is_json:
                return jsonify({'success': False, 'message': f'Server error: {str(e)}'})
            return render_template('login.html', app_title=APP_TITLE, error=f'Server error: {str(e)}')

    return render_template('login.html', app_title=APP_TITLE)


@app.route('/face-login', methods=['POST'])
def face_login():
    try:
        data = request.get_json()
        image_data = data.get('image')

        if not image_data:
            return jsonify({'success': False, 'message': 'No image provided'})

        import base64
        import numpy as np
        import cv2

        if 'data:image' in image_data:
            image_data = image_data.split(',')[1]

        img_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        embedding = face_recognizer.generate_embedding(image)

        if not embedding:
            return jsonify({'success': False, 'message': 'No face detected'})

        users = db.get_all_users()

        for user in users:
            if user.get('face_embedding'):
                try:
                    stored_embedding = json.loads(user['face_embedding'])
                    is_match, distance = face_recognizer.compare_embeddings(embedding, stored_embedding)

                    if is_match:
                        session['user_id'] = user['id']
                        session['username'] = user['username']
                        session['name'] = user['name']
                        session['role'] = user['role']
                        session['student_id'] = user.get('student_id')
                        return jsonify({
                            'success': True, 
                            'message': f'Welcome, {user["name"]}!',
                            'role': user['role']
                        })
                except:
                    pass

        return jsonify({'success': False, 'message': 'Face not recognized'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    role = session.get('role')
    user_data = {
        'name': session.get('name'), 
        'role': role,
        'department': session.get('department') or session.get('assigned_department')
    }
    
    if role == 'admin':
        stats = db.get_attendance_stats()
        trend_data = db.get_attendance_trend(days=7)
    elif role == 'teacher':
        dept = session.get('assigned_department')
        if dept:
            stats = db.get_department_attendance_stats(dept)
            trend_data = db.get_attendance_trend(days=7)
        else:
            stats = {'total_students': 0, 'present_today': 0, 'absent_today': 0}
            trend_data = []
    else:  # student
        student_id = session.get('student_id')
        if student_id:
            stats = db.get_student_attendance_stats(student_id)
            # Get recent attendance for chart
            trend_data = db.get_attendance_trend(days=7)
        else:
            stats = {'total_days': 0, 'present_days': 0, 'percentage': 0}
            trend_data = []
    
    notifications = []
    if 'user_id' in session:
        notifications = db.get_notifications(session['user_id'])
    
    return render_template('dashboard.html', user_data=user_data, stats=stats, trend_data=trend_data, notifications=notifications, app_title=APP_TITLE)


@app.route('/students')
@login_required
def students():
    if session.get('role') != 'admin':
        return redirect(url_for('dashboard'))
    all_students = db.get_all_students()
    return render_template('students.html', students=all_students, app_title=APP_TITLE)


@app.route('/attendance')
@login_required
def attendance():
    records = db.get_attendance()
    stats = db.get_attendance_stats()
    return render_template('attendance.html', records=records, stats=stats, app_title=APP_TITLE)


@app.route('/mark-attendance')
@login_required
def mark_attendance():
    if session.get('role') == 'student':
        return redirect(url_for('dashboard'))
    return render_template('mark_attendance.html', app_title=APP_TITLE)


# API ENDPOINTS

@app.route('/api/stats')
@login_required
def api_stats():
    stats = db.get_attendance_stats()
    return jsonify(stats)


@app.route('/api/trend')
@login_required
def api_trend():
    days = request.args.get('days', 7, type=int)
    trend = db.get_attendance_trend(days=days)
    return jsonify(trend)


@app.route('/api/students', methods=['GET'])
@login_required
def api_students():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    search = request.args.get('search', '')
    if search:
        students = db.search_students(search)
    else:
        students = db.get_all_students()
    return jsonify(students)


@app.route('/api/student/add', methods=['POST'])
@login_required
def api_add_student():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    try:
        data = request.get_json()
        student_id = data.get('student_id')
        name = data.get('name')
        roll_no = data.get('roll_no')
        department = data.get('department')
        year = data.get('year')
        email = data.get('email', '')
        phone = data.get('phone', '')
        embedding = data.get('embedding')
        username = data.get('username', '')
        password = data.get('password', '')

        if not all([student_id, name, roll_no, department, year]):
            return jsonify({'success': False, 'message': 'Missing required fields'})

        # Check for duplicate face only if embedding is provided
        if embedding:
            duplicate = db.check_duplicate_face_student(embedding)
            if duplicate:
                return jsonify({'success': False, 'message': f'Face already registered to {duplicate["name"]}'})

        success = db.add_student(student_id, name, roll_no, department, year, email, phone, f"{student_id}.jpg", embedding)

        if success:
            # Create login credentials if username and password are provided
            if username and password:
                db.create_student_login(username, password, student_id, name, department)
            return jsonify({'success': True, 'message': 'Student added successfully'})
        return jsonify({'success': False, 'message': 'Student ID or Roll No already exists'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/student/delete/<int:student_id>', methods=['DELETE'])
@login_required
def api_delete_student(student_id):
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    success = db.delete_student(student_id)
    return jsonify({'success': success})


@app.route('/api/student/update', methods=['PUT'])
@login_required
def api_update_student():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    data = request.get_json()
    success = db.update_student(data.get('id'), data.get('name'), data.get('roll_no'), data.get('department'), data.get('year'), data.get('email'), data.get('phone'))
    return jsonify({'success': success})


@app.route('/api/student/update-face', methods=['POST'])
@login_required
def api_update_student_face():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    try:
        data = request.get_json()
        student_id = data.get('student_id')
        image_data = data.get('image')

        if not student_id or not image_data:
            return jsonify({'success': False, 'message': 'Missing required fields'})

        import base64
        import numpy as np
        import cv2

        if 'data:image' in image_data:
            image_data = image_data.split(',')[1]

        img_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        embedding = face_recognizer.generate_embedding(image)

        if not embedding:
            return jsonify({'success': False, 'message': 'No face detected'})

        # Check for duplicates (but allow updating own face)
        duplicate = db.check_duplicate_face_student(embedding)
        if duplicate and duplicate['student_id'] != student_id:
            return jsonify({'success': False, 'message': f'Face already registered to {duplicate["name"]}'})

        success = db.update_student_face(student_id, embedding)

        if success:
            return jsonify({'success': True, 'message': 'Face registered successfully!'})
        return jsonify({'success': False, 'message': 'Failed to update face'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/face-capture', methods=['POST'])
@login_required
def api_capture_face():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    try:
        data = request.get_json()
        image_data = data.get('image')

        if not image_data:
            return jsonify({'success': False, 'message': 'No image provided'})

        import base64
        import numpy as np
        import cv2

        if 'data:image' in image_data:
            image_data = image_data.split(',')[1]

        img_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        embedding = face_recognizer.generate_embedding(image)

        if not embedding:
            return jsonify({'success': False, 'message': 'No face detected'})

        return jsonify({'success': True, 'embedding': embedding})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/recognize-face', methods=['POST'])
@login_required
def api_recognize_face():
    """Recognize face and mark attendance - IMPROVED with retry logic"""
    if session.get('role') == 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            data = request.get_json()
            image_data = data.get('image')

            if not image_data:
                return jsonify({'success': False, 'message': 'No image provided'})

            import base64
            import numpy as np
            import cv2

            if 'data:image' in image_data:
                image_data = image_data.split(',')[1]

            img_bytes = base64.b64decode(image_data)
            nparr = np.frombuffer(img_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Generate embedding
            embedding = face_recognizer.generate_embedding(image)

            if not embedding:
                if attempt < max_retries - 1:
                    print(f"⚠️ No face detected, attempt {attempt + 1}/{max_retries}, retrying...")
                    continue
                return jsonify({'success': False, 'message': 'No face detected'})

            # Get all students with face embeddings
            students = db.get_all_students()
            database = {}
            for s in students:
                if s.get('face_embedding'):
                    try:
                        database[s['student_id']] = json.loads(s['face_embedding'])
                    except:
                        pass

            if not database:
                return jsonify({'success': False, 'message': 'No registered students in database'})

            # Find matching face
            match_id, distance = face_recognizer.find_matching_face(embedding, database)

            if match_id:
                student = db.get_student_by_id(match_id)
                if student:
                    # Get today's date properly
                    today = datetime.now().date()
                    
                    period = data.get('period', 1)
                    
                    # Teacher can only mark students of their department
                    teacher_dept = session.get('department')
                    if teacher_dept and student['department'] != teacher_dept:
                        return jsonify({
                            'success': False, 
                            'message': f"Student {student['name']} belongs to {student['department']}. You can only mark attendance for {teacher_dept}."
                        }), 400
                    
                    # Mark attendance
                    success, message = db.mark_attendance(
                        student['student_id'],
                        student['name'],
                        student['department'],
                        today,
                        datetime.now().time(),
                        period=period,
                        marked_by=session.get('name')
                    )

                    if success:
                        return jsonify({
                            'success': True,
                            'message': f'Attendance marked for {student["name"]}',
                            'student': {
                                'name': student['name'],
                                'student_id': student['student_id'],
                                'department': student['department']
                            }
                        })
                    else:
                        # Already marked - still return success but indicate it
                        return jsonify({
                            'success': True,
                            'message': message,
                            'student': {
                                'name': student['name'],
                                'student_id': student['student_id'],
                                'department': student['department']
                            },
                            'already_marked': True
                        })
            
            # No match found
            if attempt < max_retries - 1:
                print(f"⚠️ Face not recognized, attempt {attempt + 1}/{max_retries}, retrying...")
                continue
                
            return jsonify({'success': False, 'message': 'Face not recognized'})

        except Exception as e:
            import traceback
            print(f"Recognition error (attempt {attempt + 1}/{max_retries}): {e}")
            print(traceback.format_exc())
            if attempt < max_retries - 1:
                continue
            return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    
    return jsonify({'success': False, 'message': 'Failed after multiple attempts'})


@app.route('/api/attendance', methods=['GET'])
@login_required
def api_attendance():
    date = request.args.get('date')
    department = request.args.get('department')
    status = request.args.get('status')
    period = request.args.get('period')
    
    # Default to today's date if not provided (for dashboard)
    if not date:
        date = datetime.now().date().isoformat()

    records = db.get_attendance(date=date, department=department) or []

    # Convert datetime/date/time objects to strings for JSON serialization
    serialized_records = []
    for record in records:
        serialized_record = dict(record)
        if serialized_record.get('date'):
            serialized_record['date'] = str(serialized_record['date'])
        if serialized_record.get('time'):
            serialized_record['time'] = str(serialized_record['time'])
        serialized_records.append(serialized_record)

    if status and status != 'All':
        serialized_records = [r for r in serialized_records if r.get('status', '').lower() == status.lower()]
    
    if period and period != 'All':
        serialized_records = [r for r in serialized_records if str(r.get('period')) == str(period)]

    return jsonify(serialized_records)


@app.route('/api/attendance/export')
@login_required
def api_export_attendance():
    date = request.args.get('date')
    status = request.args.get('status', 'all')

    records = db.get_attendance(date=date)

    if status != 'all':
        records = [r for r in records if r.get('status', '').lower() == status.lower()]

    if not records:
        return jsonify({'success': False, 'message': 'No records to export'})

    from utils import export_to_excel

    export_data = []
    for record in records:
        export_data.append([
            record['student_id'],
            record['name'],
            record['department'] or 'N/A',
            str(record['date']),
            str(record['time']),
            record['status']
        ])

    headers = ['Student ID', 'Name', 'Department', 'Date', 'Time', 'Status']
    filename = f"attendance_{status}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = export_to_excel(export_data, filename, headers)

    if filepath:
        return send_file(filepath, as_attachment=True)

    return jsonify({'success': False, 'message': 'Export failed'})


# ==================== ROLE-BASED ROUTES ====================

# Predefined departments list
DEPARTMENTS = [
    "Computer Application",
    "Commerce",
    "Management Studies",
    "Geology",
    "Psychology",
    "Social Work"
]


@app.route('/teachers')
@login_required
def teachers():
    """Manage teachers - Admin only"""
    if session.get('role') != 'admin':
        return redirect(url_for('dashboard'))
    all_teachers = db.get_all_teachers()
    return render_template('teachers.html', teachers=all_teachers, departments=DEPARTMENTS, app_title=APP_TITLE)


@app.route('/my-attendance')
@login_required
def my_attendance():
    """Student's own attendance view"""
    if session.get('role') != 'student':
        return redirect(url_for('dashboard'))
    return render_template('my_attendance.html', app_title=APP_TITLE)


@app.route('/department-students')
@login_required
def department_students():
    """Teacher's department students - Teacher only"""
    if session.get('role') != 'teacher':
        return redirect(url_for('dashboard'))
    dept = session.get('assigned_department')
    if dept:
        students = db.get_students_by_department(dept)
    else:
        students = []
    return render_template('department_students.html', students=students, department=dept, app_title=APP_TITLE)


@app.route('/manual-attendance')
@login_required
def manual_attendance():
    """Manual attendance marking - Teacher only"""
    if session.get('role') != 'teacher':
        return redirect(url_for('dashboard'))
    dept = session.get('assigned_department')
    if dept:
        students = db.get_students_by_department(dept)
    else:
        students = []
    return render_template('manual_attendance.html', students=students, department=dept, app_title=APP_TITLE)


# ==================== ROLE-BASED API ENDPOINTS ====================

@app.route('/api/teachers', methods=['GET'])
@login_required
def api_teachers():
    """Get all teachers - Admin only"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    teachers = db.get_all_teachers()
    return jsonify(teachers)


@app.route('/api/teacher/add', methods=['POST'])
@login_required
def api_add_teacher():
    """Add new teacher - Admin only"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        name = data.get('name')
        department = data.get('department')
        
        if not all([username, password, name, department]):
            return jsonify({'success': False, 'message': 'Missing required fields'})
        
        success = db.add_teacher(username, password, name, department)
        
        if success:
            return jsonify({'success': True, 'message': 'Teacher added successfully'})
        return jsonify({'success': False, 'message': 'Username already exists'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/teacher/update', methods=['PUT'])
@login_required
def api_update_teacher():
    """Update teacher - Admin only"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.get_json()
    teacher_id = data.get('id')
    name = data.get('name')
    department = data.get('department')
    
    if not all([teacher_id, name, department]):
        return jsonify({'success': False, 'message': 'Missing required fields'})
    
    success = db.update_teacher(teacher_id, name, department)
    return jsonify({'success': success})


@app.route('/api/teacher/delete/<int:teacher_id>', methods=['DELETE'])
@login_required
def api_delete_teacher(teacher_id):
    """Delete teacher - Admin only"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    success = db.delete_teacher(teacher_id)
    return jsonify({'success': success})


@app.route('/api/students/department', methods=['GET'])
@login_required
def api_students_by_department():
    """Get students by department - Admin/Teacher"""
    if session.get('role') not in ['admin', 'teacher']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    # Teachers can only see their assigned department
    if session.get('role') == 'teacher':
        department = session.get('assigned_department')
    else:
        department = request.args.get('department')
    
    search = request.args.get('search', '')
    
    if department:
        if search:
            students = db.search_students_by_department(department, search)
        else:
            students = db.get_students_by_department(department)
    else:
        students = db.get_all_students()
    
    return jsonify(students)


@app.route('/api/attendance/manual', methods=['POST'])
@login_required
def api_manual_attendance():
    """Mark manual attendance - Teacher/Admin only"""
    if session.get('role') not in ['admin', 'teacher']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    # Teachers can only mark for their department
    if session.get('role') == 'teacher':
        allowed_dept = session.get('assigned_department')
    
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        date = data.get('date')
        status = data.get('status', 'Present')
        period = data.get('period', 1)
        
        if not student_id or not date:
            return jsonify({'success': False, 'message': 'Missing required fields'})
        
        # Get student details
        student = db.get_student_by_id(student_id)
        if not student:
            return jsonify({'success': False, 'message': 'Student not found'})
        
        # Check department permission for teachers
        if session.get('role') == 'teacher':
            if student['department'] != allowed_dept:
                return jsonify({'success': False, 'message': 'Cannot mark attendance for other departments'}), 403
        
        # Mark attendance
        success, message = db.mark_attendance_manual(
            student['student_id'],
            student['name'],
            student['department'],
            date,
            datetime.now().time(),
            status=status,
            period=period,
            marked_by=session.get('name')
        )

        # Trigger email notification if student is absent
        if success and status.lower() == 'absent':
            from utils import send_attendance_email
            # Try to get student email (assuming student['email'] exists)
            student_email = student.get('email')
            if student_email:
                import threading
                # Send email in background thread to avoid slowing down the response
                email_thread = threading.Thread(
                    target=send_attendance_email,
                    args=(student['name'], student_email, date, period, status, session.get('name'))
                )
                email_thread.start()
            else:
                print(f"⚠️ Cannot send email: No email field for student {student['name']}")
        
        return jsonify({'success': success, 'message': message})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/attendance/student', methods=['GET'])
@login_required
def api_student_attendance():
    """Get attendance for a specific student"""
    if session.get('role') not in ['admin', 'teacher', 'student']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    student_id = request.args.get('student_id')
    
    # Students can only view their own attendance
    if session.get('role') == 'student':
        student_id = session.get('student_id')
    
    if not student_id:
        return jsonify({'success': False, 'message': 'Student ID required'})
    
    attendance = db.get_attendance_by_student(student_id)
    
    # Serialize dates
    serialized = []
    for record in attendance:
        r = dict(record)
        if r.get('date'):
            r['date'] = str(r['date'])
        if r.get('time'):
            r['time'] = str(r['time'])
        serialized.append(r)
    
    return jsonify(serialized)


@app.route('/api/attendance/stats/student')
@login_required
def api_student_attendance_stats():
    """Get attendance stats for a specific student"""
    if session.get('role') not in ['admin', 'teacher', 'student']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    student_id = request.args.get('student_id')
    
    # Students can only view their own stats
    if session.get('role') == 'student':
        student_id = session.get('student_id')
    
    if not student_id:
        return jsonify({'success': False, 'message': 'Student ID required'})
    
    stats = db.get_student_attendance_stats(student_id)
    return jsonify(stats)


@app.route('/api/attendance/taken-periods')
@login_required
def api_taken_periods():
    """Get list of periods already marked for a department today"""
    dept = session.get('assigned_department')
    if not dept:
        return jsonify([])
    
    date = request.args.get('date', datetime.now().date().isoformat())
    
    query = f"SELECT DISTINCT period FROM attendance WHERE department = %s AND date = %s"
    results = db.execute_query(query, (dept, date))
    
    periods = [int(r['period']) for r in results]
    return jsonify(periods)


@app.route('/api/attendance/department', methods=['GET'])
@login_required
def api_attendance_department():
    """Get attendance for teacher's department"""
    if session.get('role') not in ['admin', 'teacher']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    # Teachers can only see their department
    if session.get('role') == 'teacher':
        department = session.get('assigned_department')
    else:
        department = request.args.get('department')
    
    date = request.args.get('date')
    
    if not department:
        return jsonify({'success': False, 'message': 'Department required'})
    
    records = db.get_attendance_by_department(department, date)
    
    # Serialize
    serialized = []
    for record in records:
        r = dict(record)
        if r.get('date'):
            r['date'] = str(r['date'])
        if r.get('time'):
            r['time'] = str(r['time'])
        serialized.append(r)
    
    return jsonify(serialized)


@app.route('/api/stats/department')
@login_required
def api_department_stats():
    """Get stats for a specific department"""
    if session.get('role') not in ['admin', 'teacher']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    if session.get('role') == 'teacher':
        department = session.get('assigned_department')
    else:
        department = request.args.get('department')
    
    if not department:
        return jsonify({'success': False, 'message': 'Department required'})
    
    stats = db.get_department_attendance_stats(department)
    return jsonify(stats)


# ==================== DEPARTMENT LIST ====================

@app.route('/api/departments')
@login_required
def api_departments():
    """Get list of all departments"""
    return jsonify(DEPARTMENTS)


# ==================== CLAIM ROUTES ====================

@app.route('/claims')
@login_required
def claims():
    """Claims management page"""
    role = session.get('role')
    if role == 'student':
        student_id = session.get('student_id')
        user_claims = db.get_claims_by_student(student_id)
        return render_template('claims.html', claims=user_claims, role=role, app_title=APP_TITLE)
    elif role == 'teacher':
        dept = session.get('assigned_department')
        pending_claims = db.get_pending_claims_by_department(dept)
        return render_template('claims.html', claims=pending_claims, role=role, app_title=APP_TITLE)
    else:
        return redirect(url_for('dashboard'))

@app.route('/api/claims/add', methods=['POST'])
@login_required
def api_add_claim():
    """Add a new claim - Student only"""
    if session.get('role') != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.get_json()
    student_id = session.get('student_id')
    date = data.get('date')
    period = data.get('period')
    reason = data.get('reason')
    
    if not all([date, period, reason]):
        return jsonify({'success': False, 'message': 'Missing fields'})
        
    success = db.add_claim(student_id, date, period, reason)
    return jsonify({'success': success})

@app.route('/api/claims/update', methods=['POST'])
@login_required
def api_update_claim():
    """Approve/Deny a claim - Teacher only"""
    if session.get('role') != 'teacher':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    data = request.get_json()
    claim_id = data.get('claim_id')
    status = data.get('status')
    response = data.get('response', '')
    teacher_id = session.get('user_id')
    
    if not all([claim_id, status]):
        return jsonify({'success': False, 'message': 'Missing fields'})
        
    success = db.update_claim_status(claim_id, teacher_id, status, response)
    return jsonify({'success': success})

# ==================== NOTIFICATION ROUTES ====================

@app.route('/api/notifications/read', methods=['POST'])
@login_required
def api_notifications_read():
    """Mark notifications as read"""
    user_id = session.get('user_id')
    success = db.mark_notifications_read(user_id)
    return jsonify({'success': success})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
    print("=" * 60)
    print("Face Recognition Attendance System - Web Version")
    print("=" * 60)
    print(f"Starting server at http://localhost:5000")
    print("Default admin: username='admin', password='admin123'")
    print("Default teacher: username='teacher', password='teacher123'")
    print("Default student: username='student', password='student123'")
    print("=" * 60)

    from utils import ensure_directories
    ensure_directories()

    app.run(debug=True, host='0.0.0.0', port=5000)
