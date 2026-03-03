
import customtkinter as ctk
import sys
from config import APP_TITLE, WINDOW_SIZE, MIN_WINDOW_SIZE, COLORS
from utils import ensure_directories, center_window
from db import db
from login import LoginPage
from dashboard import Dashboard


class AttendanceApp(ctk.CTk):
    """Main application window"""

    def __init__(self):
        super().__init__()

        # Configure window
        self.title(APP_TITLE)
        self.geometry(WINDOW_SIZE)
        self.minsize(MIN_WINDOW_SIZE[0], MIN_WINDOW_SIZE[1])

        # Set theme
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # Ensure directories exist
        ensure_directories()

        # Center window
        self.update_idletasks()
        width = int(WINDOW_SIZE.split('x')[0])
        height = int(WINDOW_SIZE.split('x')[1])
        center_window(self, width, height)

        # Current frame
        self.current_frame = None

        # Always show login (default admin account is created automatically)
        print("Showing login page...")
        self.show_login()

    def clear_frame(self):
        """Clear current frame"""
        if self.current_frame:
            self.current_frame.destroy()
            self.current_frame = None

    def show_register(self):
        """Show registration page"""
        self.clear_frame()
        # Registration disabled in this build
        self.show_login()

    def show_login(self):
        """Show login page"""
        self.clear_frame()
        self.current_frame = LoginPage(self, self.show_dashboard, self.show_register)
        self.current_frame.pack(fill="both", expand=True)

    def show_dashboard(self, user_data):
        """Show main dashboard"""
        self.clear_frame()
        self.current_frame = Dashboard(self, user_data, self.show_login)
        self.current_frame.pack(fill="both", expand=True)

    def on_closing(self):
        """Handle window close event"""
        # Close database connection
        db.close()

        # Destroy window
        self.destroy()
        sys.exit(0)


def main():
    """Main function"""
    print("=" * 60)
    print("Face Recognition-Based Student Attendance System")
    print("Powered by Python, CustomTkinter, OpenCV, and DeepFace")
    print("=" * 60)
    print()

    try:
        # Create and run app
        app = AttendanceApp()
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        app.mainloop()

    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user")
        db.close()
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Application error: {e}")
        db.close()
        sys.exit(1)


if __name__ == "__main__":
    main()
