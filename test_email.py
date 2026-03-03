
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.getcwd())

from utils import send_attendance_email

def run_test():
    print("Starting Email Test...")
    print("Recipient: x9watche@gmail.com")
    
    # Test data
    student_name = "Test Student"
    student_email = "alansajivalolickal@gmail.com"
    date = datetime.now().strftime("%Y-%m-%d")
    period = 1
    status = "Absent"
    marked_by = "Diagnostic Test"

    print("Executing send_attendance_email...")
    success = send_attendance_email(
        student_name,
        student_email,
        date,
        period,
        status,
        marked_by
    )

    if success:
        print("SUCCESS: Test email sent successfully!")
    else:
        print("ERROR: Failed to send test email. Check the console output for details.")

if __name__ == "__main__":
    run_test()
