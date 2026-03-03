

import customtkinter as ctk
from tkinter import ttk
import threading
import json
from config import COLORS, IMAGES_PATH
from utils import show_toast, generate_student_id, validate_email, validate_phone
from face_recognition_module import face_recognizer
from db import db
import os


class StudentManagement(ctk.CTkFrame):
    """Student management interface"""

    def __init__(self, parent, current_user=None):
        super().__init__(parent, fg_color=COLORS['bg_light'])
        self.parent = parent
        self.current_user = current_user or {}
        self.students = []
        self.face_embedding = None
        self.face_captured = False

        self.create_ui()
        self.load_students()

    def create_ui(self):
        """Create student management UI"""
        # Header
        header_frame = ctk.CTkFrame(self, fg_color=COLORS['primary'], height=80)
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)

        header_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=30, pady=20)

        ctk.CTkLabel(
            header_content,
            text="👥 Student Management",
            font=("Roboto", 24, "bold"),
            text_color="white"
        ).pack(side="left")

        # Add student button (admin only)
        if self.current_user.get('role') == 'admin':
            add_btn = ctk.CTkButton(
                header_content,
                text="➕ Add New Student",
                font=("Roboto", 14, "bold"),
                fg_color=COLORS['success'],
                hover_color=COLORS['info'],
                height=40,
                corner_radius=8,
                command=self.show_add_student_form
            )
            add_btn.pack(side="right")

        # Main content
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Search frame
        search_frame = ctk.CTkFrame(content_frame, fg_color="white", corner_radius=10)
        search_frame.pack(fill="x", pady=(0, 15))

        search_inner = ctk.CTkFrame(search_frame, fg_color="transparent")
        search_inner.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(
            search_inner,
            text="🔍 Search:",
            font=("Roboto", 13, "bold")
        ).pack(side="left", padx=(0, 10))

        self.search_entry = ctk.CTkEntry(
            search_inner,
            width=250,
            height=35,
            placeholder_text="Search by name...",
            font=("Roboto", 13),
            corner_radius=8
        )
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self.search_students())

        ctk.CTkLabel(
            search_inner,
            text="Filter by:",
            font=("Roboto", 13, "bold")
        ).pack(side="left", padx=(20, 10))

        self.search_type = ctk.CTkComboBox(
            search_inner,
            width=150,
            height=35,
            values=["Name", "Roll No", "Department"],
            font=("Roboto", 13),
            corner_radius=8,
            command=lambda e: self.search_students()
        )
        self.search_type.set("Name")
        self.search_type.pack(side="left", padx=(0, 10))

        # Refresh button
        refresh_btn = ctk.CTkButton(
            search_inner,
            text="🔄 Refresh",
            width=100,
            height=35,
            font=("Roboto", 13, "bold"),
            fg_color=COLORS['info'],
            hover_color=COLORS['secondary'],
            corner_radius=8,
            command=self.load_students
        )
        refresh_btn.pack(side="left")

        # Students table frame
        table_frame = ctk.CTkFrame(content_frame, fg_color="white", corner_radius=10)
        table_frame.pack(fill="both", expand=True)

        # Treeview for students
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", 
                       background="white",
                       foreground="black",
                       rowheight=35,
                       fieldbackground="white",
                       font=("Roboto", 11))
        style.configure("Treeview.Heading",
                       background=COLORS['primary'],
                       foreground="white",
                       font=("Roboto", 12, "bold"))
        style.map("Treeview",
                 background=[("selected", COLORS['info'])])

        # Create treeview
        tree_container = ctk.CTkFrame(table_frame, fg_color="transparent")
        tree_container.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("ID", "Student ID", "Name", "Roll No", "Department", "Year", "Email", "Phone")
        self.tree = ttk.Treeview(tree_container, columns=columns, show="tree headings", height=15)

        # Configure columns
        self.tree.column("#0", width=0, stretch=False)
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Student ID", width=120, anchor="center")
        self.tree.column("Name", width=180, anchor="w")
        self.tree.column("Roll No", width=100, anchor="center")
        self.tree.column("Department", width=150, anchor="center")
        self.tree.column("Year", width=80, anchor="center")
        self.tree.column("Email", width=200, anchor="w")
        self.tree.column("Phone", width=120, anchor="center")

        # Configure headings
        for col in columns:
            self.tree.heading(col, text=col, anchor="center")

        # Scrollbars
        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        # Alternate row colors
        self.tree.tag_configure("evenrow", background="#f8fafc")
        self.tree.tag_configure("oddrow", background="white")

        # Action buttons frame
        action_frame = ctk.CTkFrame(table_frame, fg_color="transparent")
        action_frame.pack(fill="x", padx=10, pady=10)

        edit_btn = ctk.CTkButton(
            action_frame,
            text="✏️ Edit Selected",
            width=150,
            height=40,
            font=("Roboto", 13, "bold"),
            fg_color=COLORS['warning'],
            hover_color="#d97706",
            corner_radius=8,
            command=self.edit_student
        )
        edit_btn.pack(side="left", padx=(0, 10))

        delete_btn = ctk.CTkButton(
            action_frame,
            text="🗑️ Delete Selected",
            width=150,
            height=40,
            font=("Roboto", 13, "bold"),
            fg_color=COLORS['danger'],
            hover_color="#dc2626",
            corner_radius=8,
            command=self.delete_student
        )
        delete_btn.pack(side="left")

        # Register face for selected student (available to admin and teacher)
        register_face_btn = ctk.CTkButton(
            action_frame,
            text="📸 Register Face",
            width=170,
            height=40,
            font=("Roboto", 13, "bold"),
            fg_color=COLORS['info'],
            hover_color=COLORS['secondary'],
            corner_radius=8,
            command=self.register_face_for_selected
        )
        register_face_btn.pack(side="left", padx=(10,0))

        # Stats label
        self.stats_label = ctk.CTkLabel(
            action_frame,
            text="Total Students: 0",
            font=("Roboto", 13, "bold"),
            text_color=COLORS['primary']
        )
        self.stats_label.pack(side="right")

    def load_students(self):
        """Load all students from database"""
        self.students = db.get_all_students()
        self.display_students(self.students)

    def display_students(self, students):
        """Display students in treeview"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add students
        for idx, student in enumerate(students):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=(
                student['id'],
                student['student_id'],
                student['name'],
                student['roll_no'],
                student['department'],
                student['year'],
                student['email'] or "N/A",
                student['phone'] or "N/A"
            ), tags=(tag,))

        # Update stats
        self.stats_label.configure(text=f"Total Students: {len(students)}")

    def search_students(self):
        """Search students based on filter"""
        search_term = self.search_entry.get().strip()
        search_type = self.search_type.get().lower().replace(" ", "_")

        if not search_term:
            self.load_students()
            return

        results = db.search_students(search_term, search_type)
        self.display_students(results)

    def show_add_student_form(self):
        """Show add student form in dialog"""
        self.form_window = ctk.CTkToplevel(self)
        self.form_window.title("Add New Student")
        self.form_window.geometry("550x680+10+5")
        self.form_window.resizable(False, False)
        self.form_window.grab_set()


        self.create_add_form(self.form_window)

    def create_add_form(self, window):
        """Create add student form"""
        self.face_captured = False
        self.face_embedding = None

        # Main frame
        main_frame = ctk.CTkScrollableFrame(window, fg_color=COLORS['bg_light'])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        ctk.CTkLabel(
            main_frame,
            text="➕ Add New Student",
            font=("Roboto", 22, "bold"),
            text_color=COLORS['primary']
        ).pack(pady=(0, 20))

        # Form frame
        form_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=10)
        form_frame.pack(fill="x", pady=(0, 10))

        form_inner = ctk.CTkFrame(form_frame, fg_color="transparent")
        form_inner.pack(padx=30, pady=30)

        # Student ID (auto-generated)
        ctk.CTkLabel(form_inner, text="Student ID (Auto-generated)", font=("Roboto", 12, "bold"), anchor="w").pack(anchor="w", pady=(0, 5))
        self.student_id_var = ctk.StringVar(value=generate_student_id())
        student_id_entry = ctk.CTkEntry(form_inner, width=450, height=35, textvariable=self.student_id_var, state="disabled", font=("Roboto", 12))
        student_id_entry.pack(pady=(0, 15))

        # Name
        ctk.CTkLabel(form_inner, text="Full Name *", font=("Roboto", 12, "bold"), anchor="w").pack(anchor="w", pady=(0, 5))
        self.name_var = ctk.StringVar()
        ctk.CTkEntry(form_inner, width=450, height=35, textvariable=self.name_var, placeholder_text="Enter full name", font=("Roboto", 12)).pack(pady=(0, 15))

        # Roll No
        ctk.CTkLabel(form_inner, text="Roll Number *", font=("Roboto", 12, "bold"), anchor="w").pack(anchor="w", pady=(0, 5))
        self.roll_no_var = ctk.StringVar()
        ctk.CTkEntry(form_inner, width=450, height=35, textvariable=self.roll_no_var, placeholder_text="Enter roll number", font=("Roboto", 12)).pack(pady=(0, 15))

        # Department
        ctk.CTkLabel(form_inner, text="Department *", font=("Roboto", 12, "bold"), anchor="w").pack(anchor="w", pady=(0, 5))
        self.department_var = ctk.StringVar()
        ctk.CTkComboBox(
            form_inner, width=450, height=35,
            variable=self.department_var,
            values=["Computer Application", "Commerce", "Management Studies", "Geology", "Psychology", "Social Work"],
            font=("Roboto", 12)
        ).pack(pady=(0, 15))

        # Year
        ctk.CTkLabel(form_inner, text="Year *", font=("Roboto", 12, "bold"), anchor="w").pack(anchor="w", pady=(0, 5))
        self.year_var = ctk.StringVar()
        ctk.CTkComboBox(
            form_inner, width=450, height=35,
            variable=self.year_var,
            values=["1st Year", "2nd Year", "3rd Year", "4th Year"],
            font=("Roboto", 12)
        ).pack(pady=(0, 15))

        # Email
        ctk.CTkLabel(form_inner, text="Email", font=("Roboto", 12, "bold"), anchor="w").pack(anchor="w", pady=(0, 5))
        self.email_var = ctk.StringVar()
        ctk.CTkEntry(form_inner, width=450, height=35, textvariable=self.email_var, placeholder_text="student@example.com", font=("Roboto", 12)).pack(pady=(0, 15))

        # Phone
        ctk.CTkLabel(form_inner, text="Phone", font=("Roboto", 12, "bold"), anchor="w").pack(anchor="w", pady=(0, 5))
        self.phone_var = ctk.StringVar()
        ctk.CTkEntry(form_inner, width=450, height=35, textvariable=self.phone_var, placeholder_text="10-digit phone number", font=("Roboto", 12)).pack(pady=(0, 15))

        # Capture face button
        self.capture_face_btn = ctk.CTkButton(
            form_inner,
            text="📸 Capture Face",
            width=450, height=40,
            font=("Roboto", 13, "bold"),
            fg_color=COLORS['info'],
            hover_color=COLORS['secondary'],
            command=self.capture_student_face_thread
        )
        self.capture_face_btn.pack(pady=(0, 10))

        # Capture status
        self.capture_status = ctk.CTkLabel(form_inner, text="", font=("Roboto", 11), text_color=COLORS['success'])
        self.capture_status.pack(pady=(0, 15))

        # Buttons
        button_frame = ctk.CTkFrame(form_inner, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))

        ctk.CTkButton(
            button_frame,
            text="✅ Add Student",
            width=220, height=40,
            font=("Roboto", 14, "bold"),
            fg_color=COLORS['success'],
            hover_color=COLORS['info'],
            command=self.save_student
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            button_frame,
            text="❌ Cancel",
            width=220, height=40,
            font=("Roboto", 14, "bold"),
            fg_color=COLORS['danger'],
            hover_color="#dc2626",
            command=self.form_window.destroy
        ).pack(side="left")

    def capture_student_face_thread(self):
        """Capture student face in thread"""
        self.capture_face_btn.configure(state="disabled", text="Opening camera...")
        threading.Thread(target=self.capture_student_face, daemon=True).start()

    def capture_student_face(self):
        """Capture student face"""
        try:
            face_image = face_recognizer.capture_face()

            if face_image is not None:
                embedding = face_recognizer.generate_embedding(face_image)

                if embedding:
                    self.face_embedding = embedding
                    self.face_captured = True
                    self.form_window.after(0, self.update_face_capture_status, True)
                else:
                    self.form_window.after(0, self.update_face_capture_status, False, "No face detected")
            else:
                self.form_window.after(0, self.update_face_capture_status, False, "Capture cancelled")
        except Exception as e:
            self.form_window.after(0, self.update_face_capture_status, False, str(e))

    def update_face_capture_status(self, success, message=""):
        """Update face capture status"""
        if success:
            self.capture_face_btn.configure(text="✅ Face Captured", fg_color=COLORS['success'], state="disabled")
            self.capture_status.configure(text="Face captured successfully!", text_color=COLORS['success'])
        else:
            self.capture_face_btn.configure(text="📸 Capture Face", state="normal")
            self.capture_status.configure(text=f"Error: {message}", text_color=COLORS['danger'])

    def save_student(self):
        """Save student to database"""
        # Get values
        student_id = self.student_id_var.get()
        name = self.name_var.get().strip()
        roll_no = self.roll_no_var.get().strip()
        department = self.department_var.get().strip()
        year = self.year_var.get().strip()
        email = self.email_var.get().strip()
        phone = self.phone_var.get().strip()

        # Validation
        if not name:
            show_toast(self.form_window, "Please enter student name", "error")
            return

        if not roll_no:
            show_toast(self.form_window, "Please enter roll number", "error")
            return

        if not department:
            show_toast(self.form_window, "Please select department", "error")
            return

        if not year:
            show_toast(self.form_window, "Please select year", "error")
            return

        if email and not validate_email(email):
            show_toast(self.form_window, "Invalid email format", "error")
            return

        if phone and not validate_phone(phone):
            show_toast(self.form_window, "Phone must be 10 digits", "error")
            return

        if not self.face_captured:
            show_toast(self.form_window, "Please capture student face", "error")
            return

        # ✅ CHECK FOR DUPLICATE FACE IN STUDENTS
        duplicate_student = db.check_duplicate_face_student(self.face_embedding)
        if duplicate_student:
            show_toast(
                self.form_window,
                f"⚠️ This face is already registered to student '{duplicate_student['name']}' (Roll: {duplicate_student['roll_no']})",
                "error"
            )
            return

        # ✅ CHECK FOR DUPLICATE FACE IN USERS
        duplicate_user = db.check_duplicate_face_user(self.face_embedding)
        if duplicate_user:
            show_toast(
                self.form_window,
                f"⚠️ This face is already registered as user '{duplicate_user['name']}' ({duplicate_user['username']})",
                "error"
            )
            return

        # Save photo path
        photo_path = f"{IMAGES_PATH}{student_id}.jpg"

        # Add to database
        success = db.add_student(student_id, name, roll_no, department, year, email, phone, photo_path,
                                 self.face_embedding)

        if success:
            show_toast(self.form_window, f"Student {name} added successfully! ✅", "success")
            self.form_window.after(2000, self.form_window.destroy)
            self.load_students()
        else:
            show_toast(self.form_window, "Student ID or Roll No already exists", "error")

    def register_face_for_selected(self):
        """Allow teacher/admin to capture/assign face to selected student"""
        selected = self.tree.selection()
        if not selected:
            show_toast(self, "Please select a student to register face", "warning")
            return

        values = self.tree.item(selected[0])['values']
        # Tree columns: (id, student_id, name, ...)
        student_id = values[1]
        student = db.get_student_by_id(student_id)
        if not student:
            show_toast(self, "Student not found", "error")
            return

        # Open a small dialog to capture face
        dialog = ctk.CTkToplevel(self)
        dialog.title("Register Face")
        dialog.geometry("500x250")
        dialog.grab_set()
        dialog.configure(fg_color=COLORS['bg_light'])

        # Header
        header = ctk.CTkFrame(dialog, fg_color=COLORS['primary'], height=70, corner_radius=0)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        header_inner = ctk.CTkFrame(header, fg_color="transparent")
        header_inner.pack(fill="both", expand=True, padx=25, pady=15)

        ctk.CTkLabel(header_inner, text=f"📸 Register Face for {student['name']}", font=("Roboto", 16, "bold"), text_color="white").pack(anchor="w")

        # Content
        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=25, pady=25)

        content_box = ctk.CTkFrame(frame, fg_color="white", corner_radius=10, border_width=2, border_color=COLORS['primary'])
        content_box.pack(fill="both", expand=True, padx=0, pady=(0, 15))

        inner = ctk.CTkFrame(content_box, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(inner, text="Ready to capture face?", font=("Roboto", 13), text_color=COLORS['dark']).pack(pady=(0, 10))

        status_label = ctk.CTkLabel(inner, text="", font=("Roboto", 12, "bold"), text_color=COLORS['success'])
        status_label.pack(pady=(0, 10))

        def start_capture():
            capture_btn.configure(state="disabled", text="Opening camera...")
            status_label.configure(text="")
            dialog.update_idletasks()
            try:
                face_image = face_recognizer.capture_face()
                if face_image is None:
                    status_label.configure(text="Capture cancelled", text_color=COLORS['warning'])
                    capture_btn.configure(state="normal", text="📸 Capture Face Again")
                    return
                embedding = face_recognizer.generate_embedding(face_image)
                if not embedding:
                    status_label.configure(text="No face detected. Try again.", text_color=COLORS['danger'])
                    capture_btn.configure(state="normal", text="📸 Capture Face Again")
                    return

                # Update in DB
                photo_path = f"{student['student_id']}.jpg"
                ok = db.update_student_face(student['student_id'], embedding, photo_path)
                if ok:
                    status_label.configure(text="✅ Face registered successfully!", text_color=COLORS['success'])
                    capture_btn.configure(state="disabled", text="✅ Done")
                    self.after(1500, lambda: (dialog.destroy(), self.load_students()))
                else:
                    status_label.configure(text="Failed to save face to database", text_color=COLORS['danger'])
                    capture_btn.configure(state="normal", text="📸 Capture Face Again")
            except Exception as e:
                status_label.configure(text=f"Error: {str(e)}", text_color=COLORS['danger'])
                capture_btn.configure(state="normal", text="📸 Capture Face Again")

        # Buttons frame
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x")

        capture_btn = ctk.CTkButton(btn_frame, text="📸 Capture Face", font=("Roboto", 13, "bold"), fg_color=COLORS['info'], hover_color=COLORS['secondary'], height=40, corner_radius=8, command=start_capture)
        capture_btn.pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_frame, text="❌ Close", font=("Roboto", 13, "bold"), fg_color="#e5e7eb", text_color=COLORS['dark'], hover_color="#d1d5db", height=40, corner_radius=8, command=dialog.destroy).pack(side="left")

    def edit_student(self):
        """Edit selected student"""
        selected = self.tree.selection()
        if not selected:
            show_toast(self, "Please select a student to edit", "warning")
            return

        values = self.tree.item(selected[0])['values']
        student_id = values[0]

        # Create edit dialog
        edit_window = ctk.CTkToplevel(self)
        edit_window.title("Edit Student")
        edit_window.geometry("520x680+10+5")
        edit_window.resizable(False, False)
        edit_window.grab_set()



        # Outer frame
        outer_frame = ctk.CTkFrame(edit_window, fg_color=COLORS['bg_light'])
        outer_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ctk.CTkLabel(
            outer_frame,
            text="✏️ Edit Student Details",
            font=("Roboto", 22, "bold"),
            text_color=COLORS['primary']
        )
        title_label.pack(pady=(10, 15))

        # Divider line
        ctk.CTkFrame(outer_frame, height=2, fg_color=COLORS['primary']).pack(fill="x")

        # Form grid layout
        form_frame = ctk.CTkFrame(outer_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=10)

        def add_field(label, variable, widget_type="entry", values=None):
            """Helper to add labeled field neatly"""
            field_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
            field_frame.pack(fill="x", pady=8)

            ctk.CTkLabel(field_frame, text=label, font=("Roboto", 13, "bold"), anchor="w").pack(anchor="w", pady=(0, 5))

            if widget_type == "entry":
                ctk.CTkEntry(field_frame, width=460, height=38, textvariable=variable, font=("Roboto", 13)).pack()
            elif widget_type == "combo":
                ctk.CTkComboBox(field_frame, width=460, height=38, variable=variable, values=values,
                                font=("Roboto", 13)).pack()

        # Variables
        name_var = ctk.StringVar(value=values[2])
        roll_var = ctk.StringVar(value=values[3])
        dept_var = ctk.StringVar(value=values[4])
        year_var = ctk.StringVar(value=values[5])
        email_var = ctk.StringVar(value=values[6] if values[6] != "N/A" else "")
        phone_var = ctk.StringVar(value=values[7] if values[7] != "N/A" else "")

        # Fields
        add_field("Full Name *", name_var)
        add_field("Roll Number *", roll_var)
        add_field("Department *", dept_var, "combo",
                  ["Computer Application", "Commerce", "Management Studies", "Geology", "Psychology", "Social Work"])
        add_field("Year *", year_var, "combo",
                  ["1st Year", "2nd Year", "3rd Year", "4th Year"])
        add_field("Email", email_var)
        add_field("Phone", phone_var)

        # Buttons
        button_frame = ctk.CTkFrame(outer_frame, fg_color="transparent")
        button_frame.pack(pady=10)

        def update_student_data():
            name = name_var.get().strip()
            roll = roll_var.get().strip()
            dept = dept_var.get().strip()
            year = year_var.get().strip()
            email = email_var.get().strip()
            phone = phone_var.get().strip()

            if not name or not roll or not dept or not year:
                show_toast(edit_window, "Please fill all required fields", "error")
                return
            if email and not validate_email(email):
                show_toast(edit_window, "Invalid email format", "error")
                return
            if phone and not validate_phone(phone):
                show_toast(edit_window, "Phone must be 10 digits", "error")
                return

            success = db.update_student(student_id, name, roll, dept, year, email, phone)
            if success:
                show_toast(edit_window, "Student updated successfully! ✅", "success")
                edit_window.after(2000, edit_window.destroy)
                self.load_students()
            else:
                show_toast(edit_window, "Failed to update student", "error")

        ctk.CTkButton(
            button_frame,
            text="✅ Update",
            width=220,
            height=45,
            font=("Roboto", 14, "bold"),
            fg_color=COLORS['success'],
            hover_color=COLORS['info'],
            corner_radius=10,
            command=update_student_data
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            button_frame,
            text="❌ Cancel",
            width=220,
            height=45,
            font=("Roboto", 14, "bold"),
            fg_color=COLORS['danger'],
            hover_color="#dc2626",
            corner_radius=10,
            command=edit_window.destroy
        ).pack(side="left")

    def delete_student(self):
        """Delete selected student"""
        selected = self.tree.selection()
        if not selected:
            show_toast(self, "Please select a student to delete", "warning")
            return

        values = self.tree.item(selected[0])['values']
        student_id = values[0]
        name = values[2]

        # Confirmation dialog
        confirm_window = ctk.CTkToplevel(self)
        confirm_window.title("Confirm Delete")
        confirm_window.geometry("400x200")
        confirm_window.resizable(False, False)
        confirm_window.grab_set()
        confirm_window.transient(self)

        # Center window
        confirm_window.update_idletasks()
        width = confirm_window.winfo_width()
        height = confirm_window.winfo_height()
        x = (confirm_window.winfo_screenwidth() // 2) - (width // 2)
        y = (confirm_window.winfo_screenheight() // 2) - (height // 2)
        confirm_window.geometry(f"{width}x{height}+{x}+{y}")

        frame = ctk.CTkFrame(confirm_window, fg_color=COLORS['bg_light'])
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="⚠️ Confirm Deletion", font=("Roboto", 18, "bold"), text_color=COLORS['danger']).pack(pady=(0, 15))
        ctk.CTkLabel(frame, text=f"Are you sure you want to delete\n{name}?", font=("Roboto", 13), wraplength=350).pack(pady=(0, 20))

        def confirm_delete():
            success = db.delete_student(student_id)
            if success:
                show_toast(self, f"Student {name} deleted successfully", "success")
                confirm_window.destroy()
                self.load_students()
            else:
                show_toast(confirm_window, "Failed to delete student", "error")

        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.pack()

        ctk.CTkButton(button_frame, text="✅ Yes, Delete", width=150, height=40, font=("Roboto", 12, "bold"),
                     fg_color=COLORS['danger'], hover_color="#dc2626", command=confirm_delete).pack(side="left", padx=(0, 10))
        ctk.CTkButton(button_frame, text="❌ Cancel", width=150, height=40, font=("Roboto", 12, "bold"),
                     fg_color="gray", hover_color="#6b7280", command=confirm_window.destroy).pack(side="left")
