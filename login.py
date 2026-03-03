import customtkinter as ctk
import hashlib
import threading
import json
from config import APP_TITLE
from utils import show_toast, center_window
from face_recognition_module import face_recognizer
from db import db

from tkfontawesome import icon_to_image  # FontAwesome renderer


THEME = {
    "primary": "#3A7BD5",
    "accent": "#00D2FF",
    "success": "#28C76F",
    "info": "#00A3E0",
    "bg": "#F2F6FF",
    "card": "#FFFFFF",
    "muted": "#7B8CA5",
    "dark": "#0F1D35",
    "border": "#D7E3F5"
}


class LoginPage(ctk.CTkFrame):

    def __init__(self, parent, on_success, on_register):
        super().__init__(parent, fg_color=THEME["bg"])
        self.parent = parent
        self.on_success = on_success
        self.on_register = on_register

        self.target_y = 0.55

        # Prepare icons (white fill for dark buttons)
        self.login_icon = icon_to_image("sign-in-alt", fill="#FFFFFF", scale_to_width=24)
        self.face_icon = icon_to_image("camera", fill="#FFFFFF", scale_to_width=24)
        self.spinner_icon = icon_to_image("spinner", fill="#FFFFFF", scale_to_width=24)

        self.create_ui()
        self.after(50, self.animate_card)

    def create_ui(self):

        header = ctk.CTkFrame(self, fg_color=THEME["primary"], height=150)
        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text="Attendance System",
            font=("Roboto", 32, "bold"),
            text_color="white"
        ).place(relx=0.5, rely=0.40, anchor="center")

        ctk.CTkLabel(
            header,
            text="Face Recognition Based Smart Login",
            font=("Roboto", 13),
            text_color="#E8F3FF"
        ).place(relx=0.5, rely=0.75, anchor="center")

        # Login Card
        self.card = ctk.CTkFrame(
            self,
            fg_color=THEME["card"],
            corner_radius=20,
            border_width=1,
            border_color=THEME["border"],
            width=460,
            height=420
        )
        self.card.place(relx=0.5, rely=0.65, anchor="center")

        form = ctk.CTkFrame(self.card, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=35, pady=30)

        ctk.CTkLabel(
            form,
            text="Login",
            font=("Roboto", 22, "bold"),
            text_color=THEME["dark"]
        ).pack(anchor="center", pady=(0, 10))

        ctk.CTkLabel(
            form,
            text="Welcome back! Please sign in.",
            font=("Roboto", 13),
            text_color=THEME["muted"]
        ).pack(anchor="center", pady=(0, 25))

        # Username
        ctk.CTkLabel(form, text="Username", text_color=THEME["muted"], font=("Roboto", 13)).pack(anchor="w")
        self.username_entry = ctk.CTkEntry(
            form, placeholder_text="Enter username",
            width=350, height=48, font=("Roboto", 15), corner_radius=12
        )
        self.username_entry.pack(pady=(6, 18))

        # Password
        ctk.CTkLabel(form, text="Password", text_color=THEME["muted"], font=("Roboto", 13)).pack(anchor="w")
        self.password_entry = ctk.CTkEntry(
            form, placeholder_text="Enter password", show="●",
            width=350, height=48, font=("Roboto", 15), corner_radius=12
        )
        self.password_entry.pack(pady=(6, 22))
        self.password_entry.bind("<Return>", lambda e: self.manual_login())

        # Login Button (FA Icon)
        self.login_btn = ctk.CTkButton(
            form,
            text="  Login",
            image=self.login_icon,
            compound="left",
            fg_color=THEME["primary"],
            hover_color=THEME["accent"],
            width=350,
            height=48,
            corner_radius=12,
            font=("Roboto", 15, "bold"),
            command=self.manual_login
        )
        self.login_btn.pack(pady=(2, 14))

        ctk.CTkLabel(
            form,
            text="──────────  OR  ──────────",
            font=("Roboto", 12),
            text_color=THEME["muted"]
        ).pack(pady=10)

        # Face Login
        self.face_login_btn = ctk.CTkButton(
            form,
            text="  Login with Face",
            image=self.face_icon,
            compound="left",
            fg_color=THEME["success"],
            hover_color=THEME["info"],
            width=350,
            height=48,
            corner_radius=12,
            font=("Roboto", 15, "bold"),
            command=self.face_login_thread
        )
        self.face_login_btn.pack(pady=(8, 0))

    # ----------------------------------------------------
    def animate_card(self):
        info = self.card.place_info()
        cur_y = float(info["rely"])
        new_y = cur_y - (cur_y - self.target_y) * 0.20

        if abs(new_y - self.target_y) < 0.001:
            self.card.place_configure(rely=self.target_y)
            return

        self.card.place_configure(rely=new_y)
        self.after(15, self.animate_card)

    # ----------------------------------------------------
    # LOGIN LOGIC (unchanged)
    # ----------------------------------------------------
    def manual_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            show_toast(self, "Please enter username and password", "error")
            return

        hashed = hashlib.sha256(password.encode()).hexdigest()
        user = db.verify_user(username, hashed)

        if user:
            show_toast(self, f"Welcome, {user['name']}!", "success")
            self.after(1200, lambda: self.on_success(user))
        else:
            show_toast(self, "Invalid username or password", "error")

    def face_login_thread(self):
        self.login_btn.configure(state="disabled")
        self.face_login_btn.configure(state="disabled", image=self.spinner_icon, text="  Opening camera…")
        threading.Thread(target=self.face_login, daemon=True).start()

    def face_login(self):
        try:
            users = db.get_all_users()

            embeddings = {}
            for u in users:
                if u.get("face_embedding"):
                    try:
                        embeddings[u["username"]] = json.loads(u["face_embedding"])
                    except:
                        pass

            if not embeddings:
                self.after(0, self.update_face_login_status, False, "No stored face data")
                return

            matched = face_recognizer.recognize_face_from_camera(embeddings)

            if matched:
                user = next((x for x in users if x["username"] == matched), None)
                if user:
                    self.after(0, self.update_face_login_status, True, f"Welcome, {user['name']}!", user)
                else:
                    self.after(0, self.update_face_login_status, False, "User not found")
            else:
                self.after(0, self.update_face_login_status, False, "Face not recognized")

        except Exception as e:
            self.after(0, self.update_face_login_status, False, f"Error: {str(e)}")

    def update_face_login_status(self, success, message, user=None):
        self.login_btn.configure(state="normal")
        self.face_login_btn.configure(state="normal", image=self.face_icon, text="  Login with Face")

        if success and user:
            show_toast(self, message, "success")
            self.after(1200, lambda: self.on_success(user))
        else:
            show_toast(self, message, "error")


def show_login_window(on_success, on_register):
    window = ctk.CTk()
    window.title(f"{APP_TITLE} - Login")
    center_window(window, 500, 650)
    window.resizable(False, False)

    LoginPage(window, on_success, on_register).pack(fill="both", expand=True)
    window.mainloop()
