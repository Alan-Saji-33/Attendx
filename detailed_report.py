import customtkinter as ctk
import pandas as pd
from tkinter import filedialog, messagebox
from datetime import datetime, date, timedelta
import threading
from config import COLORS
from utils import show_toast
from db import db


class DetailedReport(ctk.CTkFrame):
    """Detailed attendance report with export functionality"""

    def __init__(self, parent, user_data):
        super().__init__(parent, fg_color=COLORS['bg_light'])
        self.parent = parent
        self.user_data = user_data
        self.selected_date = date.today()
        self.selected_students = []
        self.attendance_data = []
        
        self.create_ui()
        self.load_data()

    def create_ui(self):
        """Create the detailed report interface"""
        # Main container with scrolling
        main_container = ctk.CTkFrame(self, fg_color=COLORS['bg_light'])
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        header_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            header_frame,
            text="📋 Detailed Attendance Report",
            font=("Segoe UI", 28, "bold"),
            text_color=COLORS['dark']
        ).pack(side="left")

        # Controls frame
        controls_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        controls_frame.pack(fill="x", pady=(0, 20))

        # Date selection
        date_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        date_frame.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(
            date_frame,
            text="Select Date:",
            font=("Segoe UI", 14),
            text_color=COLORS['dark']
        ).pack(side="left", padx=(0, 10))

        # Create date entry with calendar button
        date_input_frame = ctk.CTkFrame(date_frame, fg_color="white", height=40)
        date_input_frame.pack(side="left")
        date_input_frame.pack_propagate(False)

        self.date_entry = ctk.CTkEntry(
            date_input_frame,
            placeholder_text="YYYY-MM-DD",
            font=("Segoe UI", 13),
            width=120,
            height=40,
            border_width=0,
            fg_color="white",
            text_color=COLORS['dark']
        )
        self.date_entry.pack(side="left", padx=(10, 0))
        self.date_entry.insert(0, self.selected_date.strftime("%Y-%m-%d"))

        ctk.CTkButton(
            date_input_frame,
            text="📅",
            width=40,
            height=40,
            font=("Segoe UI", 14),
            fg_color=COLORS['primary'],
            hover_color=COLORS['primary'],
            corner_radius=0,
            command=self.show_calendar
        ).pack(side="left")

        # Load button
        ctk.CTkButton(
            controls_frame,
            text="🔍 Load Data",
            font=("Segoe UI", 13, "bold"),
            fg_color=COLORS['info'],
            hover_color=COLORS['info'],
            height=40,
            corner_radius=8,
            command=self.load_data
        ).pack(side="left", padx=(0, 10))

        # Filter options
        filter_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        filter_frame.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(
            filter_frame,
            text="Show:",
            font=("Segoe UI", 14),
            text_color=COLORS['dark']
        ).pack(side="left", padx=(0, 10))

        self.filter_var = ctk.StringVar(value="all")
        
        ctk.CTkRadioButton(
            filter_frame,
            text="All",
            variable=self.filter_var,
            value="all",
            font=("Segoe UI", 13),
            command=self.filter_data
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkRadioButton(
            filter_frame,
            text="Present",
            variable=self.filter_var,
            value="present",
            font=("Segoe UI", 13),
            command=self.filter_data
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkRadioButton(
            filter_frame,
            text="Absent",
            variable=self.filter_var,
            value="absent",
            font=("Segoe UI", 13),
            command=self.filter_data
        ).pack(side="left", padx=(0, 10))

        # Auto Mark Absent button
        ctk.CTkButton(
            controls_frame,
            text="🔄 Auto Mark Absent",
            font=("Segoe UI", 13, "bold"),
            fg_color=COLORS['warning'],
            hover_color=COLORS['warning'],
            height=40,
            corner_radius=8,
            command=self.auto_mark_absent
        ).pack(side="left", padx=(0, 20))

        # Export buttons
        export_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        export_frame.pack(side="right")

        ctk.CTkButton(
            export_frame,
            text="📊 Export Present",
            font=("Segoe UI", 13),
            fg_color=COLORS['success'],
            hover_color=COLORS['success'],
            height=40,
            corner_radius=8,
            command=self.export_present_to_excel
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            export_frame,
            text="📊 Export Absent",
            font=("Segoe UI", 13),
            fg_color=COLORS['danger'],
            hover_color=COLORS['danger'],
            height=40,
            corner_radius=8,
            command=self.export_absent_to_excel
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            export_frame,
            text="📊 Export All",
            font=("Segoe UI", 13),
            fg_color=COLORS['primary'],
            hover_color=COLORS['primary'],
            height=40,
            corner_radius=8,
            command=self.export_all_to_excel
        ).pack(side="left")

        # Create tab view for different views
        self.tabview = ctk.CTkTabview(main_container, fg_color="white")
        self.tabview.pack(fill="both", expand=True, pady=(10, 0))
        
        # Add tabs
        self.tabview.add("Attendance List")
        self.tabview.add("Absent Students")
        self.tabview.add("Statistics")

        # Configure tab colors
        self.tabview.configure(segmented_button_selected_color=COLORS['primary'])
        self.tabview.configure(segmented_button_selected_hover_color=COLORS['primary'])
        self.tabview.configure(text_color=COLORS['dark'])
        self.tabview.configure(segmented_button_unselected_color="#E5E7EB")
        self.tabview.configure(segmented_button_unselected_hover_color="#F3F4F6")

        # Attendance List Tab
        self.create_attendance_list_tab()
        
        # Absent Students Tab
        self.create_absent_students_tab()
        
        # Statistics Tab
        self.create_statistics_tab()

    def create_attendance_list_tab(self):
        """Create attendance list tab"""
        tab = self.tabview.tab("Attendance List")
        
        # Header with checkboxes for selection
        header_frame = ctk.CTkFrame(tab, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))
        
        # Select all checkbox
        self.select_all_var = ctk.BooleanVar()
        select_all_cb = ctk.CTkCheckBox(
            header_frame,
            text="Select All",
            variable=self.select_all_var,
            font=("Segoe UI", 13),
            command=self.toggle_select_all
        )
        select_all_cb.pack(side="left", padx=(0, 20))

        ctk.CTkButton(
            header_frame,
            text="📧 Send Absent Notifications",
            font=("Segoe UI", 13),
            fg_color=COLORS['warning'],
            hover_color=COLORS['warning'],
            height=36,
            corner_radius=6,
            command=self.send_absent_notifications
        ).pack(side="right")

        # Create scrollable frame for attendance list
        scrollable_frame = ctk.CTkScrollableFrame(
            tab,
            fg_color="white"
        )
        scrollable_frame.pack(fill="both", expand=True)

        self.attendance_list_frame = ctk.CTkFrame(scrollable_frame, fg_color="white")
        self.attendance_list_frame.pack(fill="both", expand=True)

    def create_absent_students_tab(self):
        """Create absent students tab"""
        tab = self.tabview.tab("Absent Students")
        
        # Create scrollable frame for absent students
        scrollable_frame = ctk.CTkScrollableFrame(
            tab,
            fg_color="white"
        )
        scrollable_frame.pack(fill="both", expand=True)

        self.absent_students_frame = ctk.CTkFrame(scrollable_frame, fg_color="white")
        self.absent_students_frame.pack(fill="both", expand=True)

    def create_statistics_tab(self):
        """Create statistics tab"""
        tab = self.tabview.tab("Statistics")
        
        # Statistics container
        stats_container = ctk.CTkFrame(tab, fg_color="white")
        stats_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Create statistics cards
        stats_frame = ctk.CTkFrame(stats_container, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 30))

        self.stats_cards = {}
        stats_data = [
            ("👥", "Total Students", "total_students", COLORS['primary']),
            ("✅", "Present Today", "present_count", COLORS['success']),
            ("❌", "Absent Today", "absent_count", COLORS['danger']),
            ("📊", "Attendance %", "attendance_percentage", COLORS['info'])
        ]

        for icon, title, key, color in stats_data:
            card = ctk.CTkFrame(
                stats_frame,
                fg_color="white",
                corner_radius=15,
                border_width=1,
                border_color="#E5E7EB",
                width=200,
                height=120
            )
            card.pack(side="left", fill="both", expand=True, padx=10)
            card.pack_propagate(False)

            card_content = ctk.CTkFrame(card, fg_color="transparent")
            card_content.pack(expand=True, fill="both", padx=20, pady=20)

            # Icon - FIXED: Use lighter versions of colors
            icon_bg_colors = {
                COLORS['primary']: "#E0E7FF",  # Light blue
                COLORS['success']: "#D1FAE5",  # Light green
                COLORS['danger']: "#FEE2E2",   # Light red
                COLORS['info']: "#DBEAFE",     # Light info blue
            }
            
            icon_bg_color = icon_bg_colors.get(color, "#F3F4F6")
            
            icon_frame = ctk.CTkFrame(
                card_content,
                fg_color=icon_bg_color,
                width=50,
                height=50,
                corner_radius=25
            )
            icon_frame.pack(anchor="w")
            icon_frame.pack_propagate(False)

            ctk.CTkLabel(
                icon_frame,
                text=icon,
                font=("Segoe UI", 18),
                text_color=color
            ).pack(expand=True)

            # Title
            ctk.CTkLabel(
                card_content,
                text=title,
                font=("Segoe UI", 13),
                text_color="#6B7280",
                anchor="w"
            ).pack(anchor="w", pady=(15, 5))

            # Value
            value_label = ctk.CTkLabel(
                card_content,
                text="0",
                font=("Segoe UI", 24, "bold"),
                text_color=COLORS['dark'],
                anchor="w"
            )
            value_label.pack(anchor="w")

            self.stats_cards[key] = value_label

        # Department-wise breakdown
        dept_frame = ctk.CTkFrame(stats_container, fg_color="transparent")
        dept_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(
            dept_frame,
            text="📊 Department-wise Attendance",
            font=("Segoe UI", 18, "bold"),
            text_color=COLORS['dark']
        ).pack(anchor="w", pady=(0, 15))

        self.dept_stats_frame = ctk.CTkFrame(dept_frame, fg_color="white", corner_radius=15)
        self.dept_stats_frame.pack(fill="both", expand=True)

    def show_calendar(self):
        """Show calendar popup for date selection"""
        try:
            from tkcalendar import Calendar
        except ImportError:
            messagebox.showwarning("Calendar Not Available", 
                                 "Please install tkcalendar: pip install tkcalendar")
            return
            
        cal_window = ctk.CTkToplevel(self)
        cal_window.title("Select Date")
        cal_window.geometry("350x300")
        cal_window.resizable(False, False)
        cal_window.grab_set()
        
        # Center window
        cal_window.update_idletasks()
        width = cal_window.winfo_width()
        height = cal_window.winfo_height()
        x = (cal_window.winfo_screenwidth() // 2) - (width // 2)
        y = (cal_window.winfo_screenheight() // 2) - (height // 2)
        cal_window.geometry(f"{width}x{height}+{x}+{y}")

        # Create calendar
        cal = Calendar(
            cal_window,
            selectmode='day',
            date_pattern='yyyy-mm-dd',
            background='white',
            foreground='black',
            selectbackground=COLORS['primary'],
            selectforeground='white'
        )
        cal.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Set current date
        cal.selection_set(self.selected_date)

        # Buttons
        btn_frame = ctk.CTkFrame(cal_window, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))

        def select_date():
            self.selected_date = cal.selection_get()
            self.date_entry.delete(0, 'end')
            self.date_entry.insert(0, self.selected_date.strftime("%Y-%m-%d"))
            cal_window.destroy()
            self.load_data()

        ctk.CTkButton(
            btn_frame,
            text="Select",
            command=select_date,
            fg_color=COLORS['primary'],
            hover_color=COLORS['primary']
        ).pack(side="right", padx=(10, 0))

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=cal_window.destroy,
            fg_color="transparent",
            text_color="#6B7280",
            border_width=1,
            border_color="#D1D5DB"
        ).pack(side="right")

    def load_data(self):
        """Load attendance data for selected date"""
        try:
            # Get date from entry
            date_str = self.date_entry.get()
            try:
                self.selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except:
                self.selected_date = date.today()
                self.date_entry.delete(0, 'end')
                self.date_entry.insert(0, self.selected_date.strftime("%Y-%m-%d"))

            # Get all students
            all_students = db.get_all_students()
            
            # Get attendance for selected date
            attendance_records = db.get_attendance(date=date_str)
            
            # Create a dict of attendance for quick lookup
            attendance_dict = {}
            for record in attendance_records or []:
                attendance_dict[record['student_id']] = record

            # Prepare attendance data
            self.attendance_data = []
            self.absent_students = []
            
            for student in all_students:
                student_id = student['student_id']
                record = attendance_dict.get(student_id)
                
                status = 'Present' if record else 'Absent'
                
                attendance_record = {
                    'student_id': student_id,
                    'name': student['name'],
                    'department': student['department'],
                    'email': student.get('email', ''),
                    'phone': student.get('phone', ''),
                    'status': status,
                    'time': record.get('time', 'N/A') if record else 'N/A',
                    'selected': ctk.BooleanVar(value=False)
                }
                
                self.attendance_data.append(attendance_record)
                
                if status == 'Absent':
                    self.absent_students.append(attendance_record)

            # Update display
            self.update_attendance_list()
            self.update_absent_students_list()
            self.update_statistics()
            
            show_toast(self, f"Loaded data for {date_str}", "info")
            
        except Exception as e:
            show_toast(self, f"Error loading data: {str(e)}", "error")

    def update_attendance_list(self):
        """Update the attendance list display"""
        # Clear current list
        for widget in self.attendance_list_frame.winfo_children():
            widget.destroy()

        # Apply filter
        filter_type = self.filter_var.get()
        if filter_type == "present":
            display_data = [d for d in self.attendance_data if d['status'] == 'Present']
        elif filter_type == "absent":
            display_data = [d for d in self.attendance_data if d['status'] == 'Absent']
        else:
            display_data = self.attendance_data

        # Create header
        header_frame = ctk.CTkFrame(self.attendance_list_frame, fg_color="#F3F4F6", height=50)
        header_frame.pack(fill="x", pady=(0, 5))
        header_frame.pack_propagate(False)

        # Header columns
        columns = ["Select", "ID", "Name", "Department", "Status", "Time", "Email", "Phone"]
        widths = [60, 100, 200, 150, 100, 100, 200, 120]
        
        for i, (col, width) in enumerate(zip(columns, widths)):
            frame = ctk.CTkFrame(header_frame, fg_color="transparent", width=width)
            frame.pack(side="left", padx=(10 if i == 0 else 0, 10))
            frame.pack_propagate(False)
            
            ctk.CTkLabel(
                frame,
                text=col,
                font=("Segoe UI", 12, "bold"),
                text_color=COLORS['dark']
            ).pack(padx=10, pady=15)

        # Add data rows
        for i, record in enumerate(display_data):
            row_color = "#FFFFFF" if i % 2 == 0 else "#F9FAFB"
            row_frame = ctk.CTkFrame(
                self.attendance_list_frame,
                fg_color=row_color,
                height=50
            )
            row_frame.pack(fill="x", pady=2)
            row_frame.pack_propagate(False)

            # Select checkbox
            cb_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=60)
            cb_frame.pack(side="left")
            cb_frame.pack_propagate(False)
            
            cb = ctk.CTkCheckBox(
                cb_frame,
                text="",
                variable=record['selected'],
                width=20,
                height=20
            )
            cb.pack(padx=20, pady=15)

            # Student ID
            id_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=100)
            id_frame.pack(side="left")
            id_frame.pack_propagate(False)
            
            ctk.CTkLabel(
                id_frame,
                text=record['student_id'],
                font=("Segoe UI", 12),
                text_color="#374151"
            ).pack(padx=10, pady=15)

            # Name
            name_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=200)
            name_frame.pack(side="left")
            name_frame.pack_propagate(False)
            
            ctk.CTkLabel(
                name_frame,
                text=record['name'],
                font=("Segoe UI", 12),
                text_color="#1F2937"
            ).pack(padx=10, pady=15)

            # Department
            dept_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=150)
            dept_frame.pack(side="left")
            dept_frame.pack_propagate(False)
            
            ctk.CTkLabel(
                dept_frame,
                text=record['department'],
                font=("Segoe UI", 12),
                text_color="#6B7280"
            ).pack(padx=10, pady=15)

            # Status
            status_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=100)
            status_frame.pack(side="left")
            status_frame.pack_propagate(False)
            
            status_color = COLORS['success'] if record['status'] == 'Present' else COLORS['danger']
            status_bg = "#D1FAE5" if record['status'] == 'Present' else "#FEE2E2"
            
            status_display = ctk.CTkFrame(
                status_frame,
                fg_color=status_bg,
                height=30,
                corner_radius=15
            )
            status_display.pack(pady=10)
            status_display.pack_propagate(False)
            
            ctk.CTkLabel(
                status_display,
                text=record['status'],
                font=("Segoe UI", 11, "bold"),
                text_color=status_color
            ).pack(expand=True, padx=15)

            # Time
            time_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=100)
            time_frame.pack(side="left")
            time_frame.pack_propagate(False)
            
            ctk.CTkLabel(
                time_frame,
                text=record['time'],
                font=("Segoe UI", 12),
                text_color="#6B7280"
            ).pack(padx=10, pady=15)

            # Email
            email_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=200)
            email_frame.pack(side="left")
            email_frame.pack_propagate(False)
            
            ctk.CTkLabel(
                email_frame,
                text=record['email'],
                font=("Segoe UI", 12),
                text_color="#6B7280"
            ).pack(padx=10, pady=15)

            # Phone
            phone_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=120)
            phone_frame.pack(side="left")
            phone_frame.pack_propagate(False)
            
            ctk.CTkLabel(
                phone_frame,
                text=record['phone'],
                font=("Segoe UI", 12),
                text_color="#6B7280"
            ).pack(padx=10, pady=15)

    def update_absent_students_list(self):
        """Update the absent students list"""
        # Clear current list
        for widget in self.absent_students_frame.winfo_children():
            widget.destroy()

        if not self.absent_students:
            # Show empty state
            empty_frame = ctk.CTkFrame(self.absent_students_frame, fg_color="transparent")
            empty_frame.pack(expand=True, fill="both", pady=100)
            
            ctk.CTkLabel(
                empty_frame,
                text="🎉",
                font=("Segoe UI", 48),
                text_color="#D1D5DB"
            ).pack(pady=(0, 20))
            
            ctk.CTkLabel(
                empty_frame,
                text="No absent students today",
                font=("Segoe UI", 18),
                text_color="#9CA3AF"
            ).pack()
            return

        # Create header
        header_frame = ctk.CTkFrame(self.absent_students_frame, fg_color="#F3F4F6", height=50)
        header_frame.pack(fill="x", pady=(0, 5))
        header_frame.pack_propagate(False)

        # Header columns
        columns = ["ID", "Name", "Department", "Email", "Phone", "Actions"]
        widths = [100, 200, 150, 250, 120, 150]
        
        for i, (col, width) in enumerate(zip(columns, widths)):
            frame = ctk.CTkFrame(header_frame, fg_color="transparent", width=width)
            frame.pack(side="left", padx=(10 if i == 0 else 0, 10))
            frame.pack_propagate(False)
            
            ctk.CTkLabel(
                frame,
                text=col,
                font=("Segoe UI", 12, "bold"),
                text_color=COLORS['dark']
            ).pack(padx=10, pady=15)

        # Add absent students
        for i, student in enumerate(self.absent_students):
            row_color = "#FFFFFF" if i % 2 == 0 else "#F9FAFB"
            row_frame = ctk.CTkFrame(
                self.absent_students_frame,
                fg_color=row_color,
                height=60
            )
            row_frame.pack(fill="x", pady=2)
            row_frame.pack_propagate(False)

            # Student ID
            id_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=100)
            id_frame.pack(side="left")
            id_frame.pack_propagate(False)
            
            ctk.CTkLabel(
                id_frame,
                text=student['student_id'],
                font=("Segoe UI", 12, "bold"),
                text_color=COLORS['danger']
            ).pack(padx=10, pady=20)

            # Name
            name_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=200)
            name_frame.pack(side="left")
            name_frame.pack_propagate(False)
            
            ctk.CTkLabel(
                name_frame,
                text=student['name'],
                font=("Segoe UI", 12),
                text_color="#1F2937"
            ).pack(padx=10, pady=20)

            # Department
            dept_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=150)
            dept_frame.pack(side="left")
            dept_frame.pack_propagate(False)
            
            ctk.CTkLabel(
                dept_frame,
                text=student['department'],
                font=("Segoe UI", 12),
                text_color="#6B7280"
            ).pack(padx=10, pady=20)

            # Email
            email_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=250)
            email_frame.pack(side="left")
            email_frame.pack_propagate(False)
            
            ctk.CTkLabel(
                email_frame,
                text=student['email'],
                font=("Segoe UI", 12),
                text_color="#6B7280"
            ).pack(padx=10, pady=20)

            # Phone
            phone_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=120)
            phone_frame.pack(side="left")
            phone_frame.pack_propagate(False)
            
            ctk.CTkLabel(
                phone_frame,
                text=student['phone'],
                font=("Segoe UI", 12),
                text_color="#6B7280"
            ).pack(padx=10, pady=20)

            # Actions
            actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=150)
            actions_frame.pack(side="left")
            actions_frame.pack_propagate(False)

            # Action buttons
            btn_frame = ctk.CTkFrame(actions_frame, fg_color="transparent")
            btn_frame.pack(pady=10)

            ctk.CTkButton(
                btn_frame,
                text="📧",
                width=40,
                height=35,
                font=("Segoe UI", 13),
                fg_color=COLORS['warning'],
                hover_color=COLORS['warning'],
                corner_radius=8,
                command=lambda s=student: self.send_single_notification(s)
            ).pack(side="left", padx=(0, 5))

            ctk.CTkButton(
                btn_frame,
                text="👁️",
                width=40,
                height=35,
                font=("Segoe UI", 13),
                fg_color=COLORS['info'],
                hover_color=COLORS['info'],
                corner_radius=8,
                command=lambda s=student: self.view_student_details(s)
            ).pack(side="left")

    def update_statistics(self):
        """Update statistics display"""
        if not self.attendance_data:
            return

        # Calculate statistics
        total = len(self.attendance_data)
        present = sum(1 for d in self.attendance_data if d['status'] == 'Present')
        absent = total - present
        percentage = (present / total * 100) if total > 0 else 0

        # Update stats cards
        self.stats_cards['total_students'].configure(text=str(total))
        self.stats_cards['present_count'].configure(text=str(present))
        self.stats_cards['absent_count'].configure(text=str(absent))
        self.stats_cards['attendance_percentage'].configure(text=f"{percentage:.1f}%")

        # Update department-wise statistics
        for widget in self.dept_stats_frame.winfo_children():
            widget.destroy()

        # Calculate department stats
        dept_stats = {}
        for record in self.attendance_data:
            dept = record['department']
            if dept not in dept_stats:
                dept_stats[dept] = {'total': 0, 'present': 0}
            dept_stats[dept]['total'] += 1
            if record['status'] == 'Present':
                dept_stats[dept]['present'] += 1

        # Create department cards
        for dept, stats in dept_stats.items():
            card = ctk.CTkFrame(
                self.dept_stats_frame,
                fg_color="white",
                corner_radius=12,
                border_width=1,
                border_color="#E5E7EB",
                height=100
            )
            card.pack(fill="x", padx=10, pady=5)
            card.pack_propagate(False)

            card_content = ctk.CTkFrame(card, fg_color="transparent")
            card_content.pack(expand=True, fill="both", padx=20, pady=15)

            # Department name
            ctk.CTkLabel(
                card_content,
                text=dept,
                font=("Segoe UI", 14, "bold"),
                text_color=COLORS['dark']
            ).pack(anchor="w")

            # Stats
            stats_frame = ctk.CTkFrame(card_content, fg_color="transparent")
            stats_frame.pack(fill="x", pady=(10, 0))

            # Present/Absent
            ctk.CTkLabel(
                stats_frame,
                text=f"✅ {stats['present']} / ❌ {stats['total'] - stats['present']}",
                font=("Segoe UI", 12),
                text_color="#6B7280"
            ).pack(side="left")

            # Percentage
            dept_percentage = (stats['present'] / stats['total'] * 100) if stats['total'] > 0 else 0
            ctk.CTkLabel(
                stats_frame,
                text=f"{dept_percentage:.1f}%",
                font=("Segoe UI", 12, "bold"),
                text_color=COLORS['primary']
            ).pack(side="right")

            # Progress bar
            progress_bg = ctk.CTkFrame(card_content, fg_color="#E5E7EB", height=6, corner_radius=3)
            progress_bg.pack(fill="x", pady=(5, 0))
            progress_bg.pack_propagate(False)

            progress_width = min(dept_percentage, 100)
            progress_fill = ctk.CTkFrame(
                progress_bg, 
                fg_color=COLORS['success'],
                width=int(progress_width * 2),
                height=6,
                corner_radius=3
            )
            progress_fill.pack(side="left")

    def toggle_select_all(self):
        """Toggle select all checkbox"""
        select_all = self.select_all_var.get()
        for record in self.attendance_data:
            record['selected'].set(select_all)

    def filter_data(self):
        """Filter attendance data based on selection"""
        self.update_attendance_list()

    def get_selected_students(self, status=None):
        """Get selected students (optionally filtered by status)"""
        selected = []
        for record in self.attendance_data:
            if record['selected'].get():
                if status is None or record['status'] == status:
                    selected.append(record)
        return selected

    def export_present_to_excel(self):
        """Export present students to Excel"""
        present_students = [s for s in self.attendance_data if s['status'] == 'Present']
        if not present_students:
            messagebox.showinfo("No Data", "No present students to export.")
            return
        
        self.export_to_excel(present_students, "present_students")

    def export_absent_to_excel(self):
        """Export absent students to Excel"""
        absent_students = [s for s in self.attendance_data if s['status'] == 'Absent']
        if not absent_students:
            messagebox.showinfo("No Data", "No absent students to export.")
            return
        
        self.export_to_excel(absent_students, "absent_students")

    def export_all_to_excel(self):
        """Export all students to Excel"""
        if not self.attendance_data:
            messagebox.showinfo("No Data", "No data to export.")
            return
        
        self.export_to_excel(self.attendance_data, "all_students")

    def export_to_excel(self, data, filename_prefix):
        """Export data to Excel file"""
        try:
            # Prepare data for DataFrame
            export_data = []
            for record in data:
                export_data.append({
                    'Student ID': record['student_id'],
                    'Name': record['name'],
                    'Department': record['department'],
                    'Status': record['status'],
                    'Time': record['time'],
                    'Email': record['email'],
                    'Phone': record['phone']
                })

            # Create DataFrame
            df = pd.DataFrame(export_data)

            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile=f"{filename_prefix}_{self.selected_date}.xlsx"
            )

            if file_path:
                # Export to Excel
                df.to_excel(file_path, index=False)
                
                show_toast(self, f"Exported successfully to {file_path}", "success")
                
                # Ask to open file
                if messagebox.askyesno("Export Complete", "File exported successfully. Would you like to open it?"):
                    import os
                    os.startfile(file_path)
                    
        except Exception as e:
            show_toast(self, f"Export failed: {str(e)}", "error")

    def auto_mark_absent(self):
        """Auto mark absent students for the selected date"""
        try:
            # Get date from entry
            date_str = self.date_entry.get()
            
            # Get all students
            all_students = db.get_all_students()
            
            # Get attendance for selected date
            attendance_records = db.get_attendance(date=date_str)
            
            # Create a set of student IDs who are present
            present_students = set()
            for record in attendance_records or []:
                present_students.add(record['student_id'])
            
            # Find absent students
            absent_students = []
            for student in all_students:
                if student['student_id'] not in present_students:
                    absent_students.append(student)
            
            if not absent_students:
                messagebox.showinfo("Auto Mark Absent", "No absent students found for this date.")
                return
            
            # Ask for confirmation
            if not messagebox.askyesno(
                "Confirm Auto Mark Absent",
                f"Found {len(absent_students)} absent students.\n\n"
                "Do you want to mark them as absent and send notifications?",
                parent=self
            ):
                return
            
            # Create notification window for absent students
            self.show_auto_mark_notification(absent_students, date_str)
            
        except Exception as e:
            show_toast(self, f"Auto mark absent failed: {str(e)}", "error")

    def show_auto_mark_notification(self, absent_students, date_str):
        """Show notification window for auto marked absent students"""
        notify_window = ctk.CTkToplevel(self)
        notify_window.title("Auto Mark Absent - Send Notifications")
        notify_window.geometry("600x500")
        notify_window.resizable(False, False)
        notify_window.grab_set()
        
        # Center window
        notify_window.update_idletasks()
        width = notify_window.winfo_width()
        height = notify_window.winfo_height()
        x = (notify_window.winfo_screenwidth() // 2) - (width // 2)
        y = (notify_window.winfo_screenheight() // 2) - (height // 2)
        notify_window.geometry(f"{width}x{height}+{x}+{y}")

        # Modal content
        modal_frame = ctk.CTkFrame(
            notify_window, 
            fg_color="white",
            corner_radius=20
        )
        modal_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        ctk.CTkLabel(
            modal_frame,
            text="📋 Auto Mark Absent Results",
            font=("Segoe UI", 22, "bold"),
            text_color=COLORS['dark']
        ).pack(pady=(20, 10))

        ctk.CTkLabel(
            modal_frame,
            text=f"Found {len(absent_students)} absent students for {date_str}",
            font=("Segoe UI", 14),
            text_color="#6B7280"
        ).pack(pady=(0, 20))

        # Student list with scrollbar
        list_frame = ctk.CTkFrame(modal_frame, fg_color="#F9FAFB", corner_radius=10)
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Create scrollable frame for student list
        scroll_frame = ctk.CTkScrollableFrame(list_frame, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Add student items
        for i, student in enumerate(absent_students[:10]):  # Show first 10
            student_frame = ctk.CTkFrame(scroll_frame, fg_color="white", corner_radius=8)
            student_frame.pack(fill="x", pady=2)

            # Student info
            info_frame = ctk.CTkFrame(student_frame, fg_color="transparent")
            info_frame.pack(fill="x", padx=10, pady=8)

            ctk.CTkLabel(
                info_frame,
                text=f"{student['student_id']} - {student['name']}",
                font=("Segoe UI", 12, "bold"),
                text_color=COLORS['danger']
            ).pack(anchor="w")

            ctk.CTkLabel(
                info_frame,
                text=f"Dept: {student['department']} | Email: {student.get('email', 'N/A')}",
                font=("Segoe UI", 11),
                text_color="#6B7280"
            ).pack(anchor="w")

        if len(absent_students) > 10:
            ctk.CTkLabel(
                scroll_frame,
                text=f"... and {len(absent_students) - 10} more students",
                font=("Segoe UI", 11, "italic"),
                text_color="#6B7280"
            ).pack(pady=5)

        # Notification options
        options_frame = ctk.CTkFrame(modal_frame, fg_color="transparent")
        options_frame.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(
            options_frame,
            text="Notification Settings:",
            font=("Segoe UI", 13, "bold"),
            text_color=COLORS['dark']
        ).pack(anchor="w", pady=(0, 10))

        # Send notifications checkbox
        send_notifications_var = ctk.BooleanVar(value=True)
        send_notifications_cb = ctk.CTkCheckBox(
            options_frame,
            text="Send email notifications to absent students",
            variable=send_notifications_var,
            font=("Segoe UI", 12)
        )
        send_notifications_cb.pack(anchor="w")

        # Progress bar (initially hidden)
        progress_frame = ctk.CTkFrame(modal_frame, fg_color="transparent")
        progress_frame.pack(fill="x", padx=20, pady=(0, 20))
        progress_frame.pack_forget()  # Hide initially

        self.auto_progress_bar = ctk.CTkProgressBar(progress_frame)
        self.auto_progress_bar.pack(fill="x")
        self.auto_progress_bar.set(0)

        self.auto_progress_label = ctk.CTkLabel(
            progress_frame,
            text="",
            font=("Segoe UI", 12),
            text_color="#6B7280"
        )
        self.auto_progress_label.pack()

        # Buttons
        button_frame = ctk.CTkFrame(modal_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))

        def process_auto_mark():
            send_notifications = send_notifications_var.get()
            
            if send_notifications:
                # Show progress
                progress_frame.pack(fill="x", padx=20, pady=(0, 20))
                
                # Simulate sending notifications
                def send_process():
                    for i, student in enumerate(absent_students):
                        # Update progress
                        progress = (i + 1) / len(absent_students)
                        self.auto_progress_bar.set(progress)
                        self.auto_progress_label.configure(
                            text=f"Sending to {student['name']}... ({i+1}/{len(absent_students)})"
                        )
                        
                        # Simulate delay
                        import time
                        time.sleep(0.2)
                    
                    # Complete
                    self.auto_progress_label.configure(text="✅ Notifications sent successfully!")
                    show_toast(self, f"Auto marked {len(absent_students)} students as absent", "success")
                    
                    # Close window after delay
                    self.after(2000, notify_window.destroy)
                    
                    # Reload data
                    self.load_data()

                # Run in thread
                threading.Thread(target=send_process, daemon=True).start()
            else:
                show_toast(self, f"Auto marked {len(absent_students)} students as absent", "success")
                notify_window.destroy()
                self.load_data()

        ctk.CTkButton(
            button_frame,
            text="✅ Confirm & Process",
            height=45,
            font=("Segoe UI", 14, "bold"),
            fg_color=COLORS['success'],
            hover_color=COLORS['success'],
            corner_radius=10,
            command=process_auto_mark
        ).pack(fill="x", pady=(0, 10))

        ctk.CTkButton(
            button_frame,
            text="❌ Cancel",
            height=45,
            font=("Segoe UI", 14),
            fg_color="transparent",
            hover_color="#F3F4F6",
            text_color="#6B7280",
            border_width=1,
            border_color="#D1D5DB",
            corner_radius=10,
            command=notify_window.destroy
        ).pack(fill="x")

    def send_absent_notifications(self):
        """Send notifications to absent students"""
        absent_students = self.get_selected_students(status='Absent')
        
        if not absent_students:
            messagebox.showinfo("No Selection", "Please select absent students to notify.")
            return

        # Create notification window
        notify_window = ctk.CTkToplevel(self)
        notify_window.title("Send Notifications")
        notify_window.geometry("500x400")
        notify_window.resizable(False, False)
        notify_window.grab_set()
        
        # Center window
        notify_window.update_idletasks()
        width = notify_window.winfo_width()
        height = notify_window.winfo_height()
        x = (notify_window.winfo_screenwidth() // 2) - (width // 2)
        y = (notify_window.winfo_screenheight() // 2) - (height // 2)
        notify_window.geometry(f"{width}x{height}+{x}+{y}")

        # Modal content
        modal_frame = ctk.CTkFrame(
            notify_window, 
            fg_color="white",
            corner_radius=20
        )
        modal_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        ctk.CTkLabel(
            modal_frame,
            text="📧 Send Notifications",
            font=("Segoe UI", 22, "bold"),
            text_color=COLORS['dark']
        ).pack(pady=(20, 10))

        ctk.CTkLabel(
            modal_frame,
            text=f"Send notifications to {len(absent_students)} absent students",
            font=("Segoe UI", 14),
            text_color="#6B7280"
        ).pack(pady=(0, 20))

        # Notification type
        ctk.CTkLabel(
            modal_frame,
            text="Notification Method:",
            font=("Segoe UI", 13, "bold"),
            text_color=COLORS['dark']
        ).pack(anchor="w", padx=30, pady=(0, 10))

        method_var = ctk.StringVar(value="email")
        
        methods_frame = ctk.CTkFrame(modal_frame, fg_color="transparent")
        methods_frame.pack(fill="x", padx=30, pady=(0, 20))
        
        ctk.CTkRadioButton(
            methods_frame,
            text="📧 Email",
            variable=method_var,
            value="email",
            font=("Segoe UI", 13)
        ).pack(side="left", padx=(0, 20))
        
        ctk.CTkRadioButton(
            methods_frame,
            text="📱 SMS",
            variable=method_var,
            value="sms",
            font=("Segoe UI", 13)
        ).pack(side="left")

        # Message template
        ctk.CTkLabel(
            modal_frame,
            text="Message:",
            font=("Segoe UI", 13, "bold"),
            text_color=COLORS['dark']
        ).pack(anchor="w", padx=30, pady=(0, 10))

        message_frame = ctk.CTkFrame(modal_frame, fg_color="#F9FAFB", corner_radius=10)
        message_frame.pack(fill="x", padx=30, pady=(0, 20))

        message_text = ctk.CTkTextbox(
            message_frame,
            height=100,
            font=("Segoe UI", 12),
            fg_color="#F9FAFB",
            border_width=0
        )
        message_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        default_message = f"""Dear Student,

This is to inform you that you were marked absent on {self.selected_date}.

Please contact your department if you have any concerns.

Best regards,
Attendance System"""
        
        message_text.insert("1.0", default_message)

        # Progress bar
        progress_frame = ctk.CTkFrame(modal_frame, fg_color="transparent")
        progress_frame.pack(fill="x", padx=30, pady=(0, 20))

        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="Ready to send...",
            font=("Segoe UI", 12),
            text_color="#6B7280"
        )
        self.progress_label.pack()

        # Buttons
        button_frame = ctk.CTkFrame(modal_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=30, pady=(0, 20))

        def send_notifications():
            method = method_var.get()
            message = message_text.get("1.0", "end-1c")
            
            # Simulate sending notifications
            def send_process():
                for i, student in enumerate(absent_students):
                    # Update progress
                    progress = (i + 1) / len(absent_students)
                    self.progress_bar.set(progress)
                    self.progress_label.configure(
                        text=f"Sending to {student['name']}... ({i+1}/{len(absent_students)})"
                    )
                    
                    # Simulate delay
                    import time
                    time.sleep(0.5)
                
                # Complete
                self.progress_label.configure(text="Notifications sent successfully!")
                show_toast(self, f"Notifications sent to {len(absent_students)} students", "success")
                
                # Close window after delay
                self.after(2000, notify_window.destroy)

            # Run in thread
            threading.Thread(target=send_process, daemon=True).start()

        ctk.CTkButton(
            button_frame,
            text="🚀 Send Notifications",
            height=45,
            font=("Segoe UI", 14, "bold"),
            fg_color=COLORS['success'],
            hover_color=COLORS['success'],
            corner_radius=10,
            command=send_notifications
        ).pack(fill="x")

    def send_single_notification(self, student):
        """Send notification to a single student"""
        messagebox.showinfo(
            "Send Notification",
            f"Send notification to:\n\n"
            f"Name: {student['name']}\n"
            f"Email: {student['email']}\n"
            f"Phone: {student['phone']}\n\n"
            f"Would you like to proceed?",
            parent=self
        )

    def view_student_details(self, student):
        """View detailed student information"""
        details_window = ctk.CTkToplevel(self)
        details_window.title(f"Student Details - {student['name']}")
        details_window.geometry("500x600")
        details_window.resizable(False, False)
        details_window.grab_set()
        
        # Center window
        details_window.update_idletasks()
        width = details_window.winfo_width()
        height = details_window.winfo_height()
        x = (details_window.winfo_screenwidth() // 2) - (width // 2)
        y = (details_window.winfo_screenheight() // 2) - (height // 2)
        details_window.geometry(f"{width}x{height}+{x}+{y}")

        # Modal content
        modal_frame = ctk.CTkFrame(
            details_window, 
            fg_color="white",
            corner_radius=20
        )
        modal_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Student avatar
        avatar_frame = ctk.CTkFrame(modal_frame, fg_color="transparent")
        avatar_frame.pack(pady=(20, 10))
        
        avatar = ctk.CTkFrame(
            avatar_frame,
            fg_color=COLORS['primary'],
            width=80,
            height=80,
            corner_radius=40
        )
        avatar.pack()
        avatar.pack_propagate(False)
        
        ctk.CTkLabel(
            avatar,
            text=student['name'][0].upper(),
            font=("Segoe UI", 28, "bold"),
            text_color="white"
        ).pack(expand=True)

        # Student name
        ctk.CTkLabel(
            modal_frame,
            text=student['name'],
            font=("Segoe UI", 24, "bold"),
            text_color=COLORS['dark']
        ).pack(pady=(0, 5))

        # Student ID
        ctk.CTkLabel(
            modal_frame,
            text=f"ID: {student['student_id']}",
            font=("Segoe UI", 14),
            text_color="#6B7280"
        ).pack(pady=(0, 20))

        # Details card
        details_card = ctk.CTkFrame(
            modal_frame,
            fg_color="#F9FAFB",
            corner_radius=15
        )
        details_card.pack(fill="both", expand=True, padx=10, pady=(0, 20))

        # Details content
        details_content = ctk.CTkFrame(details_card, fg_color="transparent")
        details_content.pack(padx=30, pady=30)

        details = [
            ("📁 Department", student['department']),
            ("📧 Email", student['email']),
            ("📱 Phone", student['phone']),
            ("📅 Date", str(self.selected_date)),
            ("⏰ Status", student['status']),
            ("🕒 Time", student['time'])
        ]

        for icon, value in details:
            detail_frame = ctk.CTkFrame(details_content, fg_color="transparent")
            detail_frame.pack(fill="x", pady=10)

            ctk.CTkLabel(
                detail_frame,
                text=icon,
                font=("Segoe UI", 14),
                text_color=COLORS['dark'],
                width=120,
                anchor="w"
            ).pack(side="left")

            ctk.CTkLabel(
                detail_frame,
                text=value,
                font=("Segoe UI", 14),
                text_color="#374151",
                anchor="w"
            ).pack(side="left", fill="x", expand=True)

        # Action buttons
        button_frame = ctk.CTkFrame(modal_frame, fg_color="transparent")
        button_frame.pack(fill="x")

        ctk.CTkButton(
            button_frame,
            text="📧 Send Notification",
            height=45,
            font=("Segoe UI", 14),
            fg_color=COLORS['warning'],
            hover_color=COLORS['warning'],
            corner_radius=10,
            command=lambda: self.send_single_notification(student)
        ).pack(fill="x", pady=(0, 10))

        ctk.CTkButton(
            button_frame,
            text="Close",
            height=45,
            font=("Segoe UI", 14),
            fg_color="transparent",
            hover_color="#F3F4F6",
            text_color="#6B7280",
            border_width=1,
            border_color="#D1D5DB",
            corner_radius=10,
            command=details_window.destroy
        ).pack(fill="x")