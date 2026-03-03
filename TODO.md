# Role-Based Attendance System Implementation Plan

## Current System Analysis:
- Basic login with username/password and face recognition
- Admin role exists but no real access control
- Students can be added with department info
- Face recognition working for attendance marking
- No teacher-specific features

## Required Changes:

### 1. Database (db.py)
- [ ] Add `department` field to users table for teachers
- [ ] Add `assigned_department` field to users for teachers
- [ ] Create default teacher credential (teacher/teacher123)
- [ ] Create default student credential (student/student123)
- [ ] Add new methods for department-based queries

### 2. Backend (app.py)
- [ ] Update login to store department in session
- [ ] Create separate dashboard routes for each role
- [ ] Add teacher management endpoints (admin only)
- [ ] Add department-based student filtering
- [ ] Add manual attendance marking endpoint
- [ ] Add student attendance view endpoint
- [ ] Update existing endpoints to respect role-based access

### 3. Templates (New/Updated)
- [ ] admin_dashboard.html - Full system access
- [ ] teacher_dashboard.html - Department-specific access
- [ ] student_dashboard.html - View own attendance
- [ ] manage_teachers.html - Admin only
- [ ] manual_attendance.html - Teacher only
- [ ] my_attendance.html - Student only
- [ ] Update dashboard.html to be role-aware
- [ ] Update sidebar navigation based on role

### 4. API Endpoints to Add
- [ ] GET /api/teachers - List all teachers (admin)
- [ ] POST /api/teacher/add - Add teacher (admin)
- [ ] PUT /api/teacher/update/<id> - Update teacher (admin)
- [ ] DELETE /api/teacher/delete/<id> - Delete teacher (admin)
- [ ] GET /api/students/department/<dept> - Get students by department
- [ ] POST /api/attendance/manual - Manual attendance marking
- [ ] GET /api/attendance/my - Get student's own attendance

### 5. Departments List
- Computer Application
- Commerce
- Management Studies
- Geology
- Psychology
- Social Work

## Implementation Order:
1. Update db.py with new fields and methods
2. Update app.py with new routes and endpoints
3. Create new templates
4. Update existing templates
5. Test the system

## Default Credentials to Create:
- Admin: admin / admin123 (unchanged)
- Teacher: teacher / teacher123 (Computer Application dept)
- Student: student / student123 (Computer Application dept)
