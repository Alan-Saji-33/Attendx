import customtkinter as ctk
from tkinter import ttk
import hashlib
from config import COLORS
from utils import show_toast
from db import db


class UserManagement(ctk.CTkFrame):
    """Admin user management: add teachers and create student logins"""

    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS['bg_light'])
        self.parent = parent
        self.create_ui()
        self.load_users()

    def create_ui(self):
        # Enhanced header with better styling
        header = ctk.CTkFrame(self, fg_color=COLORS['primary'], height=90, corner_radius=0)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=30, pady=20)

        ctk.CTkLabel(header_content, text="👨‍💼 User Management", font=("Roboto", 28, "bold"), text_color="white").pack(anchor="w")
        ctk.CTkLabel(header_content, text="Manage teachers and student accounts", font=("Roboto", 12), text_color="#e0e0e0").pack(anchor="w", pady=(3, 0))

        # Main content
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=25, pady=25)

        # Table frame with border and rounded corners
        table_frame = ctk.CTkFrame(content, fg_color="white", corner_radius=12, border_width=2, border_color=COLORS['primary'])
        table_frame.pack(fill="both", expand=True, pady=(0, 15))

        table_inner = ctk.CTkFrame(table_frame, fg_color="transparent")
        table_inner.pack(fill="both", expand=True, padx=12, pady=12)

        # Styled treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="white", foreground="#1f2937", rowheight=38, fieldbackground="white", font=("Roboto", 11))
        style.configure("Treeview.Heading", background=COLORS['primary'], foreground="white", font=("Roboto", 12, "bold"))
        style.map("Treeview", background=[("selected", COLORS['info'])], foreground=[("selected", "white")])

        cols = ("ID", "Username", "Name", "Role", "Student ID")
        self.tree = ttk.Treeview(table_inner, columns=cols, show="headings", height=12)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=100 if c != "Name" else 150, anchor="center")
        self.tree.pack(fill="both", expand=True)

        # Buttons frame
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x")

        ctk.CTkButton(btn_frame, text="➕ Add Teacher", font=("Roboto", 13, "bold"), fg_color=COLORS['success'], hover_color="#059669", height=40, corner_radius=8, command=self.open_add_teacher).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_frame, text="➕ Create Student Login", font=("Roboto", 13, "bold"), fg_color=COLORS['info'], hover_color="#0891b2", height=40, corner_radius=8, command=self.open_create_student_login).pack(side="left")

    def load_users(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        users = db.get_all_users()
        if not users:
            return
        for idx, u in enumerate(users):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert('', 'end', values=(u.get('id'), u.get('username'), u.get('name'), u.get('role'), u.get('student_id') or "-"), tags=(tag,))
        self.tree.tag_configure("evenrow", background="#f8fafc")
        self.tree.tag_configure("oddrow", background="white")

    def open_add_teacher(self):
        w = ctk.CTkToplevel(self)
        w.title("Add Teacher")
        w.geometry("520x420")
        w.grab_set()
        w.configure(fg_color=COLORS['bg_light'])

        main_frame = ctk.CTkFrame(w, fg_color=COLORS['bg_light'])
        main_frame.pack(fill="both", expand=True, padx=25, pady=25)

        ctk.CTkLabel(main_frame, text="➕ Add New Teacher", font=("Roboto", 22, "bold"), text_color=COLORS['primary']).pack(anchor="w", pady=(0, 20))

        form_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=10, border_width=2, border_color=COLORS['primary'])
        form_frame.pack(fill="both", expand=True, pady=(0, 15))

        form_inner = ctk.CTkFrame(form_frame, fg_color="transparent")
        form_inner.pack(fill="both", expand=True, padx=20, pady=20)

        name_var = ctk.StringVar()
        username_var = ctk.StringVar()
        password_var = ctk.StringVar()

        ctk.CTkLabel(form_inner, text="Full Name *", font=("Roboto", 12, "bold"), text_color=COLORS['dark']).pack(anchor="w", pady=(0, 6))
        ctk.CTkEntry(form_inner, textvariable=name_var, width=450, height=40, placeholder_text="Enter teacher's full name", font=("Roboto", 12), corner_radius=8).pack(pady=(0, 15))

        ctk.CTkLabel(form_inner, text="Username *", font=("Roboto", 12, "bold"), text_color=COLORS['dark']).pack(anchor="w", pady=(0, 6))
        ctk.CTkEntry(form_inner, textvariable=username_var, width=450, height=40, placeholder_text="Enter unique username", font=("Roboto", 12), corner_radius=8).pack(pady=(0, 15))

        ctk.CTkLabel(form_inner, text="Password *", font=("Roboto", 12, "bold"), text_color=COLORS['dark']).pack(anchor="w", pady=(0, 6))
        ctk.CTkEntry(form_inner, textvariable=password_var, width=450, height=40, placeholder_text="At least 6 characters", font=("Roboto", 12), show="●", corner_radius=8).pack()

        def add_teacher():
            name = name_var.get().strip()
            username = username_var.get().strip()
            password = password_var.get()
            if not name or not username or not password:
                show_toast(w, "Please fill all fields", "error")
                return
            if len(password) < 6:
                show_toast(w, "Password must be at least 6 characters", "error")
                return
            hashed = hashlib.sha256(password.encode()).hexdigest()
            ok = db.register_user_with_role(username, hashed, name, role='teacher')
            if ok:
                show_toast(w, f"Teacher {name} added ✅", "success")
                w.destroy()
                self.load_users()
            else:
                show_toast(w, "Failed to add teacher (username may already exist)", "error")

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")

        ctk.CTkButton(button_frame, text="✅ Add Teacher", font=("Roboto", 14, "bold"), fg_color=COLORS['success'], hover_color="#059669", height=40, corner_radius=8, command=add_teacher).pack(side="left", padx=(0, 10))
        ctk.CTkButton(button_frame, text="❌ Cancel", font=("Roboto", 14, "bold"), fg_color="#e5e7eb", text_color=COLORS['dark'], hover_color="#d1d5db", height=40, corner_radius=8, command=w.destroy).pack(side="left")

    def open_create_student_login(self):
        w = ctk.CTkToplevel(self)
        w.title("Create Student Login")
        w.geometry("560x480")
        w.grab_set()
        w.configure(fg_color=COLORS['bg_light'])

        main_frame = ctk.CTkFrame(w, fg_color=COLORS['bg_light'])
        main_frame.pack(fill="both", expand=True, padx=25, pady=25)

        ctk.CTkLabel(main_frame, text="➕ Create Student Login", font=("Roboto", 22, "bold"), text_color=COLORS['primary']).pack(anchor="w", pady=(0, 20))

        form_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=10, border_width=2, border_color=COLORS['primary'])
        form_frame.pack(fill="both", expand=True, pady=(0, 15))

        form_inner = ctk.CTkFrame(form_frame, fg_color="transparent")
        form_inner.pack(fill="both", expand=True, padx=20, pady=20)

        students = db.get_all_students() or []
        student_map = {f"{s['student_id']} - {s['name']}": s for s in students}

        sel_var = ctk.StringVar()
        username_var = ctk.StringVar()
        password_var = ctk.StringVar()

        ctk.CTkLabel(form_inner, text="Select Student *", font=("Roboto", 12, "bold"), text_color=COLORS['dark']).pack(anchor="w", pady=(0, 6))
        ctk.CTkComboBox(form_inner, values=list(student_map.keys()), variable=sel_var, width=500, height=40, font=("Roboto", 12), corner_radius=8).pack(pady=(0, 15))

        ctk.CTkLabel(form_inner, text="Username *", font=("Roboto", 12, "bold"), text_color=COLORS['dark']).pack(anchor="w", pady=(0, 6))
        ctk.CTkEntry(form_inner, textvariable=username_var, width=500, height=40, placeholder_text="Enter unique username", font=("Roboto", 12), corner_radius=8).pack(pady=(0, 15))

        ctk.CTkLabel(form_inner, text="Password *", font=("Roboto", 12, "bold"), text_color=COLORS['dark']).pack(anchor="w", pady=(0, 6))
        ctk.CTkEntry(form_inner, textvariable=password_var, width=500, height=40, placeholder_text="At least 6 characters", font=("Roboto", 12), show="●", corner_radius=8).pack()

        def create_login():
            sel = sel_var.get()
            if not sel:
                show_toast(w, "Please select a student", "error")
                return
            student = student_map.get(sel)
            username = username_var.get().strip()
            password = password_var.get()
            if not username or not password:
                show_toast(w, "Please enter username and password", "error")
                return
            if len(password) < 6:
                show_toast(w, "Password must be at least 6 characters", "error")
                return
            hashed = hashlib.sha256(password.encode()).hexdigest()
            ok = db.register_user_with_role(username, hashed, student['name'], role='student', student_id=student['student_id'])
            if ok:
                show_toast(w, f"Login created for {student['name']} ✅", "success")
                w.destroy()
                self.load_users()
            else:
                show_toast(w, "Failed to create login (username may already exist)", "error")

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")

        ctk.CTkButton(button_frame, text="✅ Create Login", font=("Roboto", 14, "bold"), fg_color=COLORS['success'], hover_color="#059669", height=40, corner_radius=8, command=create_login).pack(side="left", padx=(0, 10))
        ctk.CTkButton(button_frame, text="❌ Cancel", font=("Roboto", 14, "bold"), fg_color="#e5e7eb", text_color=COLORS['dark'], hover_color="#d1d5db", height=40, corner_radius=8, command=w.destroy).pack(side="left")
