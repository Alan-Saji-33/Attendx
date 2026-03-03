import customtkinter as ctk
from tkinter import ttk
import threading
from config import COLORS
from utils import show_toast, format_date, format_time, get_current_date, export_to_excel, LoadingDialog
from db import db
from datetime import datetime, timedelta
from tkcalendar import DateEntry

class AttendanceModule(ctk.CTkFrame):
    """Attendance viewing and management interface"""

    def __init__(self, parent, current_user=None):
        super().__init__(parent, fg_color=COLORS['bg_light'])
        self.parent = parent
        self.current_user = current_user or {}
        self.attendance_records = []
        self.current_filtered_records = []
        self.create_ui()
        self.load_attendance()

    def create_ui(self):
        """Create attendance UI"""
        # Header
        header_frame = ctk.CTkFrame(self, fg_color=COLORS['primary'], height=90, corner_radius=0)
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)

        header_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=30, pady=20)

        ctk.CTkLabel(
            header_content,
            text="📊 Attendance Records",
            font=("Roboto", 28, "bold"),
            text_color="white"
        ).pack(side="left")
        ctk.CTkLabel(
            header_content,
            text="Track and manage student attendance",
            font=("Roboto", 11),
            text_color="#e0e0e0"
        ).pack(side="left", padx=(15, 0), pady=(16, 0))

        # Auto-mark absent button (only for admin/teacher)
        if getattr(self, 'current_user', {}).get('role') in ('admin', 'teacher'):
            auto_mark_frame = ctk.CTkFrame(header_content, fg_color="transparent")
            auto_mark_frame.pack(side="right", padx=(0, 15))
            
            auto_mark_btn = ctk.CTkButton(
                auto_mark_frame,
                text="⚠️ Auto-Mark Absent",
                font=("Roboto", 12, "bold"),
                fg_color=COLORS['warning'],
                hover_color="#d97706",
                height=35,
                width=140,
                corner_radius=6,
                command=self.auto_mark_absent_dialog
            )
            auto_mark_btn.pack(side="right")

        # Export buttons frame
        export_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        export_frame.pack(side="right", padx=(0, 10))
        
        # Export All button
        export_all_btn = ctk.CTkButton(
            export_frame,
            text="📥 Export All",
            font=("Roboto", 12, "bold"),
            fg_color=COLORS['primary'],
            hover_color=COLORS['secondary'],
            height=35,
            width=120,
            corner_radius=6,
            command=self.export_to_excel_thread
        )
        export_all_btn.pack(side="right", padx=(5, 0))
        
        # Export Present button
        export_present_btn = ctk.CTkButton(
            export_frame,
            text="✅ Export Present",
            font=("Roboto", 12, "bold"),
            fg_color=COLORS['success'],
            hover_color="#059669",
            height=35,
            width=130,
            corner_radius=6,
            command=lambda: self.export_filtered_records("Present")
        )
        export_present_btn.pack(side="right", padx=(5, 0))
        
        # Export Absent button
        export_absent_btn = ctk.CTkButton(
            export_frame,
            text="❌ Export Absent",
            font=("Roboto", 12, "bold"),
            fg_color=COLORS['danger'],
            hover_color="#dc2626",
            height=35,
            width=130,
            corner_radius=6,
            command=lambda: self.export_filtered_records("Absent")
        )
        export_absent_btn.pack(side="right")

        # Main content
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Filter frame
        filter_frame = ctk.CTkFrame(content_frame, fg_color="white", corner_radius=12, border_width=2, border_color=COLORS['primary'])
        filter_frame.pack(fill="x", pady=(0, 15))

        filter_inner = ctk.CTkFrame(filter_frame, fg_color="transparent")
        filter_inner.pack(fill="x", padx=20, pady=15)

        # Date filter label
        ctk.CTkLabel(filter_inner, text="📅 Date:", font=("Roboto", 13, "bold")).pack(side="left", padx=(0, 10))

        today = datetime.now().date()
        self.date_picker = DateEntry(
            filter_inner,
            width=15,
            background=COLORS['primary'],
            foreground='white',
            borderwidth=2,
            font=("Roboto", 14),
            date_pattern='yyyy-mm-dd',
            state='readonly',
            maxdate=today
        )
        self.date_picker.pack(side="left", padx=(0, 10))
        self.date_picker.bind("<<DateEntrySelected>>", lambda e: self.apply_filters())

        # Quick date buttons
        today_btn = ctk.CTkButton(
            filter_inner,
            text="Today",
            width=80,
            height=35,
            font=("Roboto", 12, "bold"),
            fg_color=COLORS['info'],
            hover_color=COLORS['secondary'],
            command=self.set_today
        )
        today_btn.pack(side="left", padx=(0, 5))

        yesterday_btn = ctk.CTkButton(
            filter_inner,
            text="Yesterday",
            width=90,
            height=35,
            font=("Roboto", 12, "bold"),
            fg_color=COLORS['info'],
            hover_color=COLORS['secondary'],
            command=self.set_yesterday
        )
        yesterday_btn.pack(side="left", padx=(0, 15))

        # Status filter
        ctk.CTkLabel(filter_inner, text="📋 Status:", font=("Roboto", 13, "bold")).pack(side="left", padx=(0, 10))

        self.status_filter = ctk.CTkComboBox(
            filter_inner,
            width=120,
            height=35,
            values=["All", "Present", "Absent"],
            font=("Roboto", 12)
        )
        self.status_filter.set("All")
        self.status_filter.pack(side="left", padx=(0, 15))

        # Department filter
        ctk.CTkLabel(filter_inner, text="🏢 Department:", font=("Roboto", 13, "bold")).pack(side="left", padx=(0, 10))

        self.dept_filter = ctk.CTkComboBox(
            filter_inner,
            width=180,
            height=35,
            values=["All", "Computer Application", "Commerce", "Management Studies", "Geology", "Psychology", "Social Work"],
            font=("Roboto", 12)
        )
        self.dept_filter.set("All")
        self.dept_filter.pack(side="left", padx=(0, 15))

        # Search button
        search_btn = ctk.CTkButton(
            filter_inner,
            text="🔍 Filter",
            width=100,
            height=35,
            font=("Roboto", 13, "bold"),
            fg_color=COLORS['primary'],
            hover_color=COLORS['secondary'],
            command=self.apply_filters
        )
        search_btn.pack(side="left", padx=(0, 10))

        # Clear button
        clear_btn = ctk.CTkButton(
            filter_inner,
            text="🔄 Clear",
            width=100,
            height=35,
            font=("Roboto", 13, "bold"),
            fg_color="gray",
            hover_color="#6b7280",
            command=self.clear_filters
        )
        clear_btn.pack(side="left")

        # Stats frame
        stats_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        # Stats labels
        self.total_label = ctk.CTkLabel(
            stats_frame,
            text="Total: 0",
            font=("Roboto", 12),
            text_color=COLORS['dark']
        )
        self.total_label.pack(side="left", padx=(0, 20))
        
        self.present_label = ctk.CTkLabel(
            stats_frame,
            text="✅ Present: 0",
            font=("Roboto", 12, "bold"),
            text_color=COLORS['success']
        )
        self.present_label.pack(side="left", padx=(0, 20))
        
        self.absent_label = ctk.CTkLabel(
            stats_frame,
            text="❌ Absent: 0",
            font=("Roboto", 12, "bold"),
            text_color=COLORS['danger']
        )
        self.absent_label.pack(side="left")

        # Table frame
        table_frame = ctk.CTkFrame(content_frame, fg_color="white", corner_radius=12, border_width=2, border_color=COLORS['primary'])
        table_frame.pack(fill="both", expand=True)

        # Treeview styling
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
        style.map("Treeview", background=[("selected", COLORS['info'])])

        # Create treeview
        tree_container = ctk.CTkFrame(table_frame, fg_color="transparent")
        tree_container.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("ID", "Student ID", "Name", "Department", "Date", "Time", "Status")
        self.tree = ttk.Treeview(tree_container, columns=columns, show="tree headings", height=15)

        # Configure columns
        self.tree.column("#0", width=0, stretch=False)
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Student ID", width=120, anchor="center")
        self.tree.column("Name", width=200, anchor="w")
        self.tree.column("Department", width=180, anchor="center")
        self.tree.column("Date", width=120, anchor="center")
        self.tree.column("Time", width=100, anchor="center")
        self.tree.column("Status", width=100, anchor="center")

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

        # Alternate row colors and status colors
        self.tree.tag_configure("evenrow", background="#f8fafc")
        self.tree.tag_configure("oddrow", background="white")
        self.tree.tag_configure("present", foreground=COLORS['success'])
        self.tree.tag_configure("absent", foreground=COLORS['danger'])

        # Action buttons
        action_frame = ctk.CTkFrame(table_frame, fg_color="transparent")
        action_frame.pack(fill="x", padx=10, pady=10)

        delete_btn = ctk.CTkButton(
            action_frame,
            text="🗑️ Delete Selected",
            width=150,
            height=40,
            font=("Roboto", 13, "bold"),
            fg_color=COLORS['danger'],
            hover_color="#dc2626",
            corner_radius=8,
            command=self.delete_record
        )
        delete_btn.pack(side="left", padx=(0, 10))

        # Manual mark button (teachers/admins)
        if getattr(self, 'current_user', {}).get('role') in ('admin', 'teacher'):
            manual_mark_btn = ctk.CTkButton(
                action_frame,
                text="✍️ Manual Mark",
                width=150,
                height=40,
                font=("Roboto", 13, "bold"),
                fg_color=COLORS['warning'],
                hover_color="#d97706",
                corner_radius=8,
                command=self.manual_mark_dialog
            )
            manual_mark_btn.pack(side="left", padx=(10, 0))

        # Records label
        self.records_label = ctk.CTkLabel(
            action_frame,
            text="Showing 0 records",
            font=("Roboto", 13, "bold"),
            text_color=COLORS['primary']
        )
        self.records_label.pack(side="right")

    def auto_mark_absent_dialog(self):
        """Open dialog for auto-marking absent students"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Auto-Mark Absent Students")
        dialog.geometry("600x500")
        dialog.grab_set()
        dialog.configure(fg_color=COLORS['bg_light'])

        # Header
        header = ctk.CTkFrame(dialog, fg_color=COLORS['warning'], height=70, corner_radius=0)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        header_inner = ctk.CTkFrame(header, fg_color="transparent")
        header_inner.pack(fill="both", expand=True, padx=25, pady=15)

        ctk.CTkLabel(header_inner, text="⚠️ Auto-Mark Absent Students", font=("Roboto", 18, "bold"), text_color="white").pack(anchor="w")
        ctk.CTkLabel(header_inner, text="Mark students as absent who were not recognized today", font=("Roboto", 11), text_color="#fef3c7").pack(anchor="w", pady=(5, 0))

        # Content
        main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=25, pady=25)

        # Info box
        info_box = ctk.CTkFrame(main_frame, fg_color="#fef3c7", corner_radius=8, border_width=1, border_color="#fbbf24")
        info_box.pack(fill="x", pady=(0, 20))
        
        info_inner = ctk.CTkFrame(info_box, fg_color="transparent")
        info_inner.pack(fill="both", padx=15, pady=15)
        
        ctk.CTkLabel(info_inner, 
                    text="This will mark all students as 'Absent' who:\n• Have not been recognized via face recognition today\n• Are not already marked 'Present'\n• If a student scans later, status will update to 'Present'",
                    font=("Roboto", 12),
                    text_color="#92400e",
                    justify="left").pack(anchor="w")

        # Date selection
        date_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        date_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(date_frame, text="📅 Select Date:", font=("Roboto", 13, "bold"), text_color=COLORS['dark']).pack(anchor="w", pady=(0, 8))
        
        today = datetime.now().date()
        date_picker = DateEntry(
            date_frame,
            width=15,
            background=COLORS['primary'],
            foreground='white',
            borderwidth=2,
            font=("Roboto", 14),
            date_pattern='yyyy-mm-dd',
            state='readonly',
            maxdate=today
        )
        date_picker.set_date(today)
        date_picker.pack(anchor="w")

        # Department filter for auto-mark
        dept_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        dept_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(dept_frame, text="🏢 Department (Optional):", font=("Roboto", 13, "bold"), text_color=COLORS['dark']).pack(anchor="w", pady=(0, 8))
        
        auto_dept_filter = ctk.CTkComboBox(
            dept_frame,
            width=300,
            height=35,
            values=["All Departments"] + ["Computer Application", "Commerce", "Management Studies", "Geology", "Psychology", "Social Work"],
            font=("Roboto", 12)
        )
        auto_dept_filter.set("All Departments")
        auto_dept_filter.pack(anchor="w")

        # Preview section
        preview_frame = ctk.CTkFrame(main_frame, fg_color="#f8fafc", corner_radius=8, border_width=1, border_color="#e5e7eb")
        preview_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        ctk.CTkLabel(preview_frame, text="Students who will be marked absent:", font=("Roboto", 13, "bold"), text_color=COLORS['dark']).pack(anchor="w", padx=15, pady=10)
        
        # Text widget for preview
        preview_text = ctk.CTkTextbox(preview_frame, height=80, font=("Roboto", 11))
        preview_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        preview_text.insert("1.0", "Click 'Preview' to see affected students")
        preview_text.configure(state="disabled")

        def preview_affected():
            """Preview students who will be marked absent"""
            selected_date = date_picker.get_date().strftime("%Y-%m-%d")
            dept = auto_dept_filter.get() if auto_dept_filter.get() != "All Departments" else None
            
            # Get all students
            all_students = db.get_all_students()
            if dept:
                all_students = [s for s in all_students if s.get('department') == dept]
            
            # Get today's attendance
            today_attendance = db.get_attendance(date=selected_date, department=dept)
            present_ids = {record['student_id'] for record in today_attendance if record.get('status') == 'Present'}
            
            # Find absent students
            absent_students = []
            for student in all_students:
                if student['student_id'] not in present_ids:
                    absent_students.append(student)
            
            preview_text.configure(state="normal")
            preview_text.delete("1.0", "end")
            
            if not absent_students:
                preview_text.insert("1.0", "No students to mark as absent.\nAll students are already marked 'Present' or have attendance records.")
            else:
                preview_text.insert("1.0", f"Total students to mark absent: {len(absent_students)}\n\n")
                for student in absent_students[:50]:  # Show first 50
                    preview_text.insert("end", f"• {student['name']} ({student['student_id']}) - {student['department']}\n")
                
                if len(absent_students) > 50:
                    preview_text.insert("end", f"\n... and {len(absent_students) - 50} more students")
            
            preview_text.configure(state="disabled")
            
            return len(absent_students)

        def mark_absent_now():
            """Mark absent students"""
            selected_date = date_picker.get_date().strftime("%Y-%m-%d")
            dept = auto_dept_filter.get() if auto_dept_filter.get() != "All Departments" else None
            
            # Show loading
            loading = LoadingDialog(dialog, "Marking Absent", "Processing...")
            
            try:
                # Get all students
                all_students = db.get_all_students()
                if dept:
                    all_students = [s for s in all_students if s.get('department') == dept]
                
                # Get today's attendance
                today_attendance = db.get_attendance(date=selected_date, department=dept)
                present_ids = {record['student_id'] for record in today_attendance if record.get('status') == 'Present'}
                
                # Mark absent students
                absent_count = 0
                current_time = datetime.now().time()
                
                for student in all_students:
                    if student['student_id'] not in present_ids:
                        # Check if student already has attendance record for today
                        existing_record = None
                        for record in today_attendance:
                            if record['student_id'] == student['student_id']:
                                existing_record = record
                                break
                        
                        if existing_record:
                            # Update existing record to Absent
                            success, message = db.mark_attendance(
                                student['student_id'],
                                student['name'],
                                student['department'],
                                selected_date,
                                current_time,
                                "Absent",
                                update=True
                            )
                        else:
                            # Create new absent record
                            success, message = db.mark_attendance(
                                student['student_id'],
                                student['name'],
                                student['department'],
                                selected_date,
                                current_time,
                                "Absent"
                            )
                        
                        if success:
                            absent_count += 1
                
                loading.close()
                
                if absent_count > 0:
                    show_toast(dialog, f"✅ Marked {absent_count} students as absent", "success")
                    dialog.destroy()
                    self.apply_filters()  # Refresh the view
                else:
                    show_toast(dialog, "No students needed to be marked as absent", "info")
                    
            except Exception as e:
                loading.close()
                show_toast(dialog, f"Error: {str(e)}", "error")

        # Buttons frame
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        ctk.CTkButton(btn_frame, text="👁️ Preview", font=("Roboto", 13, "bold"), 
                     fg_color=COLORS['info'], hover_color=COLORS['secondary'], 
                     height=40, width=120, corner_radius=8, command=preview_affected).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(btn_frame, text="✅ Mark Absent", font=("Roboto", 13, "bold"), 
                     fg_color=COLORS['warning'], hover_color="#d97706", 
                     height=40, width=130, corner_radius=8, command=mark_absent_now).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(btn_frame, text="❌ Cancel", font=("Roboto", 13, "bold"), 
                     fg_color="#e5e7eb", text_color=COLORS['dark'], hover_color="#d1d5db", 
                     height=40, width=120, corner_radius=8, command=dialog.destroy).pack(side="left")

    def update_stats_labels(self, records):
        """Update the statistics labels based on current records"""
        total = len(records)
        present = sum(1 for r in records if r.get('status') == 'Present')
        absent = sum(1 for r in records if r.get('status') == 'Absent')
        
        self.total_label.configure(text=f"Total: {total}")
        self.present_label.configure(text=f"✅ Present: {present}")
        self.absent_label.configure(text=f"❌ Absent: {absent}")
        self.records_label.configure(text=f"Showing {total} records")

    def set_today(self):
        """Set date to today and apply filter"""
        today = datetime.now().date()
        self.date_picker.set_date(today)
        self.apply_filters()

    def set_yesterday(self):
        """Set date to yesterday and apply filter"""
        yesterday = datetime.now() - timedelta(days=1)
        self.date_picker.set_date(yesterday.date())
        self.apply_filters()

    def load_attendance(self):
        """Load all attendance records"""
        self.attendance_records = db.get_attendance()
        self.current_filtered_records = self.attendance_records.copy()
        self.display_records(self.current_filtered_records)

    def display_records(self, records):
        """Display attendance records in treeview"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for idx, record in enumerate(records):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            status_tag = "present" if record.get('status') == 'Present' else "absent"
            
            self.tree.insert("", "end", values=(
                record['id'],
                record['student_id'],
                record['name'],
                record['department'] or "N/A",
                format_date(record['date']),
                format_time(record['time']),
                record['status']
            ), tags=(tag, status_tag))

        self.update_stats_labels(records)
        self.current_filtered_records = records

    def apply_filters(self):
        """Apply filters to attendance records"""
        date = self.date_picker.get_date().strftime("%Y-%m-%d")
        department = self.dept_filter.get()
        status = self.status_filter.get()

        date_filter = date if date else None
        dept_filter = department if department != "All" else None
        
        records = db.get_attendance(date=date_filter, department=dept_filter)
        
        if status != "All":
            records = [r for r in records if r.get('status', '').lower() == status.lower()]
            
        self.display_records(records)

    def clear_filters(self):
        """Clear all filters"""
        today = datetime.now().date()
        self.date_picker.set_date(today)
        self.dept_filter.set("All")
        self.status_filter.set("All")
        self.load_attendance()

    def delete_record(self):
        """Delete selected attendance record"""
        selected = self.tree.selection()
        if not selected:
            show_toast(self, "Please select a record to delete", "warning")
            return

        values = self.tree.item(selected[0])['values']
        record_id = values[0]
        name = values[2]

        confirm_window = ctk.CTkToplevel(self)
        confirm_window.title("Confirm Delete")
        confirm_window.geometry("400x180")
        confirm_window.resizable(False, False)
        confirm_window.grab_set()
        confirm_window.transient(self)

        confirm_window.update_idletasks()
        width = confirm_window.winfo_width()
        height = confirm_window.winfo_height()
        x = (confirm_window.winfo_screenwidth() // 2) - (width // 2)
        y = (confirm_window.winfo_screenheight() // 2) - (height // 2)
        confirm_window.geometry(f"{width}x{height}+{x}+{y}")

        frame = ctk.CTkFrame(confirm_window, fg_color=COLORS['bg_light'])
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="⚠️ Confirm Deletion", font=("Roboto", 16, "bold"), text_color=COLORS['danger']).pack(pady=(0, 10))
        ctk.CTkLabel(frame, text=f"Delete attendance record for {name}?", font=("Roboto", 12)).pack(pady=(0, 20))

        def confirm_delete():
            success = db.delete_attendance(record_id)
            if success:
                show_toast(self, "Record deleted successfully", "success")
                confirm_window.destroy()
                self.apply_filters()
            else:
                show_toast(confirm_window, "Failed to delete record", "error")

        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.pack()

        ctk.CTkButton(button_frame, text="✅ Yes", width=130, height=35, font=("Roboto", 12, "bold"),
                     fg_color=COLORS['danger'], hover_color="#dc2626", command=confirm_delete).pack(side="left", padx=(0, 10))
        ctk.CTkButton(button_frame, text="❌ No", width=130, height=35, font=("Roboto", 12, "bold"),
                     fg_color="gray", hover_color="#6b7280", command=confirm_window.destroy).pack(side="left")

    def export_to_excel_thread(self):
        """Export all attendance to Excel in thread"""
        threading.Thread(target=self.export_attendance, daemon=True).start()

    def export_filtered_records(self, status):
        """Export filtered records by status"""
        threading.Thread(target=lambda: self.export_attendance(status), daemon=True).start()

    def export_attendance(self, status_filter=None):
        """Export attendance records to Excel"""
        try:
            self.loading_dialog = LoadingDialog(self, "Exporting", "Preparing Excel file...")
            
            records_to_export = self.current_filtered_records
            
            if status_filter:
                records_to_export = [r for r in records_to_export if r.get('status', '').lower() == status_filter.lower()]
            
            if not records_to_export:
                self.after(0, lambda: show_toast(self, f"No {status_filter.lower() if status_filter else ''} records to export", "warning"))
                self.after(0, lambda: self.loading_dialog.close())
                return

            export_data = []
            for record in records_to_export:
                export_data.append([
                    record['student_id'],
                    record['name'],
                    record['department'] or "N/A",
                    format_date(record['date']),
                    format_time(record['time']),
                    record['status']
                ])

            date_str = self.date_picker.get_date().strftime("%Y%m%d")
            if status_filter:
                filename = f"attendance_{status_filter.lower()}_{date_str}.xlsx"
            else:
                filename = f"attendance_all_{date_str}.xlsx"
                
            headers = ["Student ID", "Name", "Department", "Date", "Time", "Status"]
            filepath = export_to_excel(export_data, filename, headers)

            self.after(0, lambda: self.loading_dialog.close())

            if filepath:
                status_text = status_filter if status_filter else "All"
                self.after(0, lambda: show_toast(self, f"Exported {len(records_to_export)} {status_text.lower()} records to {filename} ✅", "success"))
            else:
                self.after(0, lambda: show_toast(self, "Export failed", "error"))

        except Exception as e:
            self.after(0, lambda: self.loading_dialog.close())
            self.after(0, lambda: show_toast(self, f"Export error: {str(e)}", "error"))

    def manual_mark_dialog(self):
        """Open dialog for manual marking of attendance"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Manual Attendance Mark")
        dialog.geometry("560x400")
        dialog.grab_set()
        dialog.configure(fg_color=COLORS['bg_light'])

        header = ctk.CTkFrame(dialog, fg_color=COLORS['primary'], height=70, corner_radius=0)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        header_inner = ctk.CTkFrame(header, fg_color="transparent")
        header_inner.pack(fill="both", expand=True, padx=25, pady=15)

        ctk.CTkLabel(header_inner, text="✍️ Mark Attendance Manually", font=("Roboto", 18, "bold"), text_color="white").pack(anchor="w")

        main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=25, pady=25)

        form_box = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=10, border_width=2, border_color=COLORS['primary'])
        form_box.pack(fill="both", expand=True, pady=(0, 15))

        form_inner = ctk.CTkFrame(form_box, fg_color="transparent")
        form_inner.pack(fill="both", expand=True, padx=25, pady=25)

        students = db.get_all_students() or []
        student_map = {f"{s['student_id']} - {s['name']}": s for s in students}

        sel_var = ctk.StringVar()
        status_var = ctk.StringVar(value="Present")

        ctk.CTkLabel(form_inner, text="📚 Select Student *", font=("Roboto", 13, "bold"), text_color=COLORS['dark']).pack(anchor="w", pady=(0, 8))
        dropdown = ctk.CTkComboBox(form_inner, values=list(student_map.keys()), variable=sel_var, width=500, height=40, font=("Roboto", 12), corner_radius=8)
        dropdown.pack(pady=(0, 20))

        ctk.CTkLabel(form_inner, text="📋 Status *", font=("Roboto", 13, "bold"), text_color=COLORS['dark']).pack(anchor="w", pady=(0, 8))
        ctk.CTkComboBox(form_inner, values=["Present", "Absent"], variable=status_var, width=500, height=40, font=("Roboto", 12), corner_radius=8).pack()

        def mark_now():
            sel = sel_var.get()
            if not sel:
                show_toast(dialog, "Please select a student", "error")
                return
            student = student_map.get(sel)
            status = status_var.get()
            
            # Check if student already has attendance for today
            today = datetime.now().date().strftime("%Y-%m-%d")
            existing_records = db.get_attendance(date=today, student_id=student['student_id'])
            
            if existing_records:
                # Update existing record
                success, message = db.mark_attendance(
                    student['student_id'],
                    student['name'],
                    student['department'],
                    datetime.now().date(),
                    datetime.now().time(),
                    status,
                    update=True
                )
            else:
                # Create new record
                success, message = db.mark_attendance(
                    student['student_id'],
                    student['name'],
                    student['department'],
                    datetime.now().date(),
                    datetime.now().time(),
                    status
                )
            
            if success:
                show_toast(dialog, f"✅ Marked {student['name']} as {status}", "success")
                dialog.destroy()
                self.apply_filters()
            else:
                show_toast(dialog, message, "warning")

        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x")

        ctk.CTkButton(btn_frame, text="✅ Mark Attendance", font=("Roboto", 14, "bold"), fg_color=COLORS['success'], hover_color="#059669", height=40, corner_radius=8, command=mark_now).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_frame, text="❌ Cancel", font=("Roboto", 14, "bold"), fg_color="#e5e7eb", text_color=COLORS['dark'], hover_color="#d1d5db", height=40, corner_radius=8, command=dialog.destroy).pack(side="left")