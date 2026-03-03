# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'antigravityfacerecognition',
    'port': 3306
}

# Application Settings
APP_TITLE = "Face Recognition Attendance System"
APP_VERSION = "1.0.0"
WINDOW_SIZE = "1200x680"
MIN_WINDOW_SIZE = (1000, 600)

# Theme Colors
COLORS = {
    'primary': '#2563eb',
    'secondary': '#7c3aed',
    'success': '#10b981',
    'danger': '#ef4444',
    'warning': '#f59e0b',
    'info': '#06b6d4',
    'dark': '#1e293b',
    'light': '#f8fafc',
    'bg_dark': '#0f172a',
    'bg_light': '#ffffff'
}

# Paths
IMAGES_PATH = "images/"
ENCODINGS_PATH = "encodings/"
REPORTS_PATH = "attendance_reports/"

# Face Recognition Settings - IMPROVED for better recognition
FACE_DETECTION_CONFIDENCE = 0.4
FACE_MATCH_THRESHOLD = 0.32  # Lower threshold = more lenient matching
DEEPFACE_MODEL = 'Facenet'
DEEPFACE_DETECTOR = 'opencv'

# Database Table Names
TABLE_USERS = 'users'
TABLE_STUDENTS = 'students'
TABLE_ATTENDANCE = 'attendance'

# UI Settings
FONT_FAMILY = 'Roboto'
FONT_SIZE_NORMAL = 13
FONT_SIZE_HEADING = 20
FONT_SIZE_TITLE = 24
BUTTON_HEIGHT = 40
ENTRY_HEIGHT = 35
# Email Notification Settings
SMTP_CONFIG = {
    'server': 'smtp.gmail.com',  # Default to Gmail
    'port': 587,
    'username': 'x9watche@gmail.com',
    'password': 'zvyj xast kexl egyf',
    'from_name': 'Attendance System'
}
