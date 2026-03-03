

import customtkinter as ctk
from PIL import Image
import threading
from config import COLORS, APP_TITLE
from utils import show_toast, center_window
from face_recognition_module import face_recognizer
from db import db
import hashlib


class RegisterPage(ctk.CTkFrame):
    """Registration page with face capture"""

    def __init__(self, parent, on_success):
        super().__init__(parent, fg_color=COLORS['bg_light'])
        self.parent = parent
        self.on_success = on_success
        self.face_embedding = None
        self.captured = False

        self.create_ui()

    def create_ui(self):
        """Create registration UI"""
        # Scrollable frame container
        scrollable = ctk.CTkScrollableFrame(self, fg_color="transparent", width=600, height=680)
        scrollable.pack(expand=True, fill="both", padx=20, pady=20)

        main_container = ctk.CTkFrame(scrollable, fg_color="transparent")
        main_container.pack(expand=True, fill="both")

        # Title
        title_label = ctk.CTkLabel(
            main_container,
            text="🎓 User Registration",
            font=("Roboto", 32, "bold"),
            text_color=COLORS['primary']
        )
        title_label.pack(pady=(0, 10))

        # Subtitle
        subtitle_label = ctk.CTkLabel(
            main_container,
            text="Create your account to access the system",
            font=("Roboto", 14),
            text_color="gray"
        )
        subtitle_label.pack(pady=(0, 10))

        # Form frame
        form_frame = ctk.CTkFrame(
            main_container,
            fg_color="white",
            corner_radius=15,
            border_width=2,
            border_color=COLORS['primary']
        )
        form_frame.pack(padx=40, pady=20)

        form_inner = ctk.CTkFrame(form_frame, fg_color="transparent")
        form_inner.pack(padx=40, pady=40)

        # Name field
        ctk.CTkLabel(
            form_inner,
            text="Full Name",
            font=("Roboto", 13, "bold"),
            anchor="w"
        ).pack(anchor="w", pady=(0, 5))

        self.name_entry = ctk.CTkEntry(
            form_inner,
            width=350,
            height=40,
            placeholder_text="Enter your full name",
            font=("Roboto", 13),
            corner_radius=8
        )
        self.name_entry.pack(pady=(0, 15))

        # Username field
        ctk.CTkLabel(
            form_inner,
            text="Username",
            font=("Roboto", 13, "bold"),
            anchor="w"
        ).pack(anchor="w", pady=(0, 5))

        self.username_entry = ctk.CTkEntry(
            form_inner,
            width=350,
            height=40,
            placeholder_text="Choose a username",
            font=("Roboto", 13),
            corner_radius=8
        )
        self.username_entry.pack(pady=(0, 15))

        # Password field
        ctk.CTkLabel(
            form_inner,
            text="Password",
            font=("Roboto", 13, "bold"),
            anchor="w"
        ).pack(anchor="w", pady=(0, 5))

        self.password_entry = ctk.CTkEntry(
            form_inner,
            width=350,
            height=40,
            placeholder_text="Create a password",
            font=("Roboto", 13),
            show="●",
            corner_radius=8
        )
        self.password_entry.pack(pady=(0, 15))

        # Confirm password field
        ctk.CTkLabel(
            form_inner,
            text="Confirm Password",
            font=("Roboto", 13, "bold"),
            anchor="w"
        ).pack(anchor="w", pady=(0, 5))

        self.confirm_password_entry = ctk.CTkEntry(
            form_inner,
            width=350,
            height=40,
            placeholder_text="Confirm your password",
            font=("Roboto", 13),
            show="●",
            corner_radius=8
        )
        self.confirm_password_entry.pack(pady=(0, 20))

        # Capture face button
        self.capture_btn = ctk.CTkButton(
            form_inner,
            text="📸 Capture Face",
            width=350,
            height=45,
            font=("Roboto", 14, "bold"),
            fg_color=COLORS['info'],
            hover_color=COLORS['secondary'],
            corner_radius=8,
            command=self.capture_face_thread
        )
        self.capture_btn.pack(pady=(0, 10))

        # Status label
        self.status_label = ctk.CTkLabel(
            form_inner,
            text="",
            font=("Roboto", 12),
            text_color=COLORS['success']
        )
        self.status_label.pack(pady=(0, 15))

        # Register button
        self.register_btn = ctk.CTkButton(
            form_inner,
            text="Register",
            width=350,
            height=45,
            font=("Roboto", 15, "bold"),
            fg_color=COLORS['primary'],
            hover_color=COLORS['secondary'],
            corner_radius=8,
            command=self.register_user
        )
        self.register_btn.pack()

        # Already have account label
        login_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        login_frame.pack(pady=(10, 0))

        ctk.CTkLabel(
            login_frame,
            text="Already have an account? ",
            font=("Roboto", 12),
            text_color="gray"
        ).pack(side="left")

        login_link = ctk.CTkLabel(
            login_frame,
            text="Login here",
            font=("Roboto", 12, "bold"),
            text_color=COLORS['primary'],
            cursor="hand2"
        )
        login_link.pack(side="left")
        login_link.bind("<Button-1>", lambda e: self.on_success())

    def capture_face_thread(self):
        """Capture face in separate thread"""
        self.capture_btn.configure(state="disabled", text="Opening camera...")
        threading.Thread(target=self.capture_face, daemon=True).start()

    def capture_face(self):
        """Capture face using webcam"""
        try:
            # Capture face
            face_image = face_recognizer.capture_face()

            if face_image is not None:
                # Generate embedding
                embedding = face_recognizer.generate_embedding(face_image)

                if embedding:
                    self.face_embedding = embedding
                    self.captured = True
                    self.after(0, self.update_capture_status, True)
                else:
                    self.after(0, self.update_capture_status, False, "No face detected. Please try again.")
            else:
                self.after(0, self.update_capture_status, False, "Face capture cancelled.")
        except Exception as e:
            self.after(0, self.update_capture_status, False, f"Error: {str(e)}")

    def update_capture_status(self, success, message="Face captured successfully!"):
        """Update capture status UI"""
        if success:
            self.capture_btn.configure(
                text="✅ Face Captured",
                fg_color=COLORS['success'],
                state="disabled"
            )
            self.status_label.configure(text=message, text_color=COLORS['success'])
        else:
            self.capture_btn.configure(
                text="📸 Capture Face",
                state="normal"
            )
            self.status_label.configure(text=message, text_color=COLORS['danger'])

    def register_user(self):
        """Register new user"""
        # Get form data
        name = self.name_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()

        # Validation
        if not name:
            show_toast(self, "Please enter your full name", "error")
            return

        if not username:
            show_toast(self, "Please enter a username", "error")
            return

        if len(username) < 4:
            show_toast(self, "Username must be at least 4 characters", "error")
            return

        if not password:
            show_toast(self, "Please enter a password", "error")
            return

        if len(password) < 6:
            show_toast(self, "Password must be at least 6 characters", "error")
            return

        if password != confirm_password:
            show_toast(self, "Passwords do not match", "error")
            return

        if not self.captured:
            show_toast(self, "Please capture your face first", "error")
            return

        # ✅ CHECK FOR DUPLICATE FACE
        duplicate = db.check_duplicate_face_user(self.face_embedding)
        if duplicate:
            show_toast(
                self,
                f"⚠️ This face is already registered to user '{duplicate['name']}' ({duplicate['username']})",
                "error"
            )
            return

        # Hash password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Register in database
        success = db.register_user(username, hashed_password, name, self.face_embedding)

        if success:
            show_toast(self, f"Registration successful! Welcome {name} ✅", "success")
            self.after(2000, self.on_success)
        else:
            show_toast(self, "Username already exists. Please choose another.", "error")


def show_register_window(on_success):
    """Show registration window"""
    window = ctk.CTk()
    window.title(f"{APP_TITLE} - Register")
    center_window(window, 600, 750)
    window.resizable(False, False)

    RegisterPage(window, on_success).pack(fill="both", expand=True)

    window.mainloop()
