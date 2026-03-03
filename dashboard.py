import customtkinter as ctk
from datetime import datetime
import threading
import json
from config import COLORS, APP_TITLE
from utils import show_toast, get_display_date, get_display_time
from student import StudentManagement
from attendance import AttendanceModule
from face_recognition_module import face_recognizer
from db import db
from user_management import UserManagement


class Dashboard(ctk.CTkFrame):
    """Main dashboard interface with enhanced styling"""

    def __init__(self, parent, user_data, on_logout):
        super().__init__(parent, fg_color=COLORS['bg_light'])
        self.parent = parent
        self.user_data = user_data
        self.on_logout = on_logout
        self.current_frame = None
        self.scrollable_frame = None
        self.graph_canvas = None

        self.create_ui()
        self.show_home()
        self.update_clock()

    def create_ui(self):
        """Create dashboard UI with enhanced styling"""
        # Sidebar with fixed width
        self.sidebar = ctk.CTkFrame(
            self, 
            fg_color=COLORS['dark'],
            width=280,
            corner_radius=0,
            border_width=0
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo/Title with modern design
        logo_frame = ctk.CTkFrame(
            self.sidebar, 
            fg_color=COLORS['primary'],
            height=120,
            corner_radius=0
        )
        logo_frame.pack(fill="x", padx=0, pady=(0, 25))
        
        logo_content = ctk.CTkFrame(logo_frame, fg_color="transparent")
        logo_content.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Logo with icon and title
        ctk.CTkLabel(
            logo_content,
            text="🎓",
            font=("Segoe UI", 44)
        ).pack(pady=(0, 10))
        
        ctk.CTkLabel(
            logo_content,
            text="Attendance",
            font=("Segoe UI", 18, "bold"),
            text_color="white"
        ).pack()
        
        ctk.CTkLabel(
            logo_content,
            text="System",
            font=("Segoe UI", 14),
            text_color="#CCCCCC"
        ).pack()

        # User info with avatar
        user_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        user_frame.pack(fill="x", padx=20, pady=(0, 30))
        
        # User avatar
        avatar_text = self.user_data['name'][0].upper()
        avatar_frame = ctk.CTkFrame(
            user_frame, 
            fg_color=COLORS['primary'],
            width=50,
            height=50,
            corner_radius=25
        )
        avatar_frame.pack(anchor="center", pady=(0, 10))
        avatar_frame.pack_propagate(False)
        
        ctk.CTkLabel(
            avatar_frame,
            text=avatar_text,
            font=("Segoe UI", 18, "bold"),
            text_color="white"
        ).pack(expand=True)
        
        ctk.CTkLabel(
            user_frame,
            text=self.user_data['name'],
            font=("Segoe UI", 16, "bold"),
            text_color="white"
        ).pack(anchor="center")
        
        role = self.user_data.get('role', 'User').title()
        role_badge = ctk.CTkFrame(
            user_frame,
            fg_color="#333333",
            height=28,
            corner_radius=14
        )
        role_badge.pack(anchor="center", pady=(5, 0))
        role_badge.pack_propagate(False)
        
        ctk.CTkLabel(
            role_badge,
            text=role,
            font=("Segoe UI", 11),
            text_color="#EEEEEE",
            padx=15
        ).pack(expand=True)

        # Navigation section
        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", padx=10, pady=(10, 0))
        
        ctk.CTkLabel(
            nav_frame,
            text="NAVIGATION",
            font=("Segoe UI", 11, "bold"),
            text_color="#888888",
            anchor="w"
        ).pack(fill="x", padx=10, pady=(0, 10))

         # Navigation buttons based on role
        role_nav = self.user_data.get('role')
        if role_nav == 'student':
            nav_buttons = [
                ("🏠", "Dashboard", self.show_home, COLORS['primary']),
                ("📊", "Attendance Report", self.show_attendance, COLORS['info']),
            ]
        else:
            nav_buttons = [
                ("🏠", "Dashboard", self.show_home, COLORS['primary']),
                ("👥", "Student Management", self.show_students, COLORS['secondary']),
                ("📸", "Mark Attendance", self.start_face_recognition, COLORS['success']),
                ("📊", "Attendance Report", self.show_attendance, COLORS['info']),
            ]

            # Admin-only: User Management
            if role_nav == 'admin':
                nav_buttons.insert(2, ("👨‍💼", "User Management", self.show_user_management, COLORS['warning']))
        for icon, text, command, color in nav_buttons:
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"   {icon}  {text}",
                font=("Segoe UI", 14),
                fg_color="transparent",
                hover_color="#444444",
                height=52,
                anchor="w",
                corner_radius=10,
                border_width=0,
                text_color="white",
                command=command
            )
            btn.pack(fill="x", padx=10, pady=2)

        # Spacer
        ctk.CTkFrame(self.sidebar, fg_color="transparent", height=20).pack()

        # Logout button
        logout_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logout_frame.pack(side="bottom", fill="x", padx=10, pady=(0, 20))
        
        logout_btn = ctk.CTkButton(
            logout_frame,
            text="🚪  Logout",
            font=("Segoe UI", 14),
            fg_color="#3A0B0B",
            hover_color="#4A0F0F",
            height=48,
            corner_radius=10,
            border_width=1,
            border_color=COLORS['danger'],
            text_color=COLORS['danger'],
            command=self.logout
        )
        logout_btn.pack(fill="x")

        # Main content area - FIXED: Use regular frame instead of scrollable
        self.content_area = ctk.CTkFrame(
            self, 
            fg_color=COLORS['bg_light'],
            corner_radius=0
        )
        self.content_area.pack(side="right", fill="both", expand=True)

    def clear_content(self):
        """Clear current content"""
        if self.current_frame:
            self.current_frame.destroy()
            self.current_frame = None
        if self.scrollable_frame:
            self.scrollable_frame.destroy()
            self.scrollable_frame = None
        if self.graph_canvas:
            try:
                self.graph_canvas.get_tk_widget().destroy()
            except:
                pass
            self.graph_canvas = None

    def show_home(self):
        """Show home/dashboard with enhanced styling"""
        self.clear_content()
        
        # Create main container with Canvas for proper scrolling
        self.scrollable_frame = ctk.CTkFrame(
            self.content_area, 
            fg_color=COLORS['bg_light']
        )
        self.scrollable_frame.pack(fill="both", expand=True)
        
        # Create canvas and scrollbar for proper scrolling
        canvas = ctk.CTkCanvas(
            self.scrollable_frame,
            bg=COLORS['bg_light'],
            highlightthickness=0
        )
        scrollbar = ctk.CTkScrollbar(
            self.scrollable_frame,
            orientation="vertical",
            command=canvas.yview
        )
        
        # Create scrollable frame inside canvas
        self.current_frame = ctk.CTkFrame(canvas, fg_color=COLORS['bg_light'])
        
        # Configure canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Create window in canvas
        canvas.create_window((0, 0), window=self.current_frame, anchor="nw")
        
        # Configure scroll region
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        self.current_frame.bind("<Configure>", configure_scroll_region)
        
        # Add mouse wheel scrolling
        def on_mouse_wheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind_all("<MouseWheel>", on_mouse_wheel)

        # If logged in user is a student, show student-specific view
        if self.user_data.get('role') == 'student':
            self.show_student_home()
            return

        # Header
        header = ctk.CTkFrame(
            self.current_frame, 
            fg_color=COLORS['primary'],
            height=160,
            corner_radius=20
        )
        header.pack(fill="x", padx=20, pady=20)
        header.pack_propagate(False)

        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=30, pady=30)

        # Title and date
        left_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        left_frame.pack(side="left", fill="y")

        ctk.CTkLabel(
            left_frame,
            text="Dashboard Overview",
            font=("Segoe UI", 32, "bold"),
            text_color="white"
        ).pack(anchor="w")

        self.date_label = ctk.CTkLabel(
            left_frame,
            text=get_display_date(),
            font=("Segoe UI", 14),
            text_color="#DDDDDD"
        )
        self.date_label.pack(anchor="w", pady=(8, 0))

        # Clock
        clock_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        clock_frame.pack(side="right", fill="y")
        
        self.clock_label = ctk.CTkLabel(
            clock_frame,
            text=get_display_time(),
            font=("Segoe UI", 36, "bold"),
            text_color="white"
        )
        self.clock_label.pack(side="right")

        ctk.CTkLabel(
            clock_frame,
            text="Live",
            font=("Segoe UI", 12),
            text_color="#CCCCCC"
        ).pack(side="right", padx=(0, 10))

        # Stats cards
        stats_container = ctk.CTkFrame(self.current_frame, fg_color="transparent")
        stats_container.pack(fill="x", padx=20, pady=(0, 20))

        # Get stats
        stats = db.get_attendance_stats()

        # Stats data
        stats_data = [
            ("👥", "Total Students", stats['total_students'], COLORS['primary']),
            ("✅", "Present Today", stats['present_today'], COLORS['success']),
            ("❌", "Absent Today", stats['absent_today'], COLORS['danger']),
        ]

        for icon, title, value, color in stats_data:
            card = ctk.CTkFrame(
                stats_container,
                fg_color="white",
                corner_radius=18,
                border_width=1,
                border_color="#E5E7EB"
            )
            card.pack(side="left", fill="both", expand=True, padx=10)
            
            # Card header with icon
            card_header = ctk.CTkFrame(card, fg_color="transparent")
            card_header.pack(fill="x", padx=25, pady=(25, 15))
            
            icon_frame = ctk.CTkFrame(
                card_header,
                fg_color=color,
                width=50,
                height=50,
                corner_radius=25
            )
            icon_frame.pack(side="left")
            icon_frame.pack_propagate(False)
            
            ctk.CTkLabel(
                icon_frame,
                text=icon,
                font=("Segoe UI", 20),
                text_color="white"
            ).pack(expand=True)
            
            ctk.CTkLabel(
                card_header,
                text=title,
                font=("Segoe UI", 14),
                text_color="#6B7280",
                anchor="w"
            ).pack(side="left", fill="x", expand=True, padx=(15, 0))
            
            # Card value
            ctk.CTkLabel(
                card,
                text=str(value),
                font=("Segoe UI", 42, "bold"),
                text_color="#1F2937"
            ).pack(pady=(0, 25))

        # Graph section
        graph_header = ctk.CTkFrame(self.current_frame, fg_color="transparent")
        graph_header.pack(fill="x", padx=20, pady=(20, 15))
        
        ctk.CTkLabel(
            graph_header,
            text="📊 Attendance Analytics",
            font=("Segoe UI", 22, "bold"),
            text_color=COLORS['dark']
        ).pack(side="left")
        
        ctk.CTkLabel(
            graph_header,
            text="Last 7 Days",
            font=("Segoe UI", 14),
            text_color="#6B7280"
        ).pack(side="right")

        # Create graph in a modern card
        graph_card = ctk.CTkFrame(
            self.current_frame,
            fg_color="white",
            corner_radius=20,
            border_width=1,
            border_color="#E5E7EB"
        )
        graph_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.create_attendance_graph(graph_card)

        # Quick actions
        actions_frame = ctk.CTkFrame(self.current_frame, fg_color="transparent")
        actions_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        ctk.CTkLabel(
            actions_frame,
            text="⚡ Quick Actions",
            font=("Segoe UI", 18, "bold"),
            text_color=COLORS['dark']
        ).pack(anchor="w", pady=(0, 15))

        # Quick action buttons
        action_buttons = [
            ("📸 Mark Attendance", self.start_face_recognition, COLORS['success']),
            ("👥 View Students", self.show_students, COLORS['primary']),
            ("📊 View Reports", self.show_attendance, COLORS['info']),
        ]

        btn_frame = ctk.CTkFrame(actions_frame, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        for text, command, color in action_buttons:
            btn = ctk.CTkButton(
                btn_frame,
                text=text,
                font=("Segoe UI", 14),
                fg_color=color,
                hover_color=color,
                height=45,
                corner_radius=12,
                border_width=0,
                command=command
            )
            btn.pack(side="left", padx=(0, 15))

    def create_attendance_graph(self, parent):
        """Create attendance trend graph"""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure
            import matplotlib.dates as mdates
            
            # Get trend data
            trend_data = db.get_attendance_trend(days=7)

            if not trend_data:
                no_data_frame = ctk.CTkFrame(parent, fg_color="transparent")
                no_data_frame.pack(expand=True, fill="both", pady=50)
                
                ctk.CTkLabel(
                    no_data_frame,
                    text="📈",
                    font=("Segoe UI", 48),
                    text_color="#D1D5DB"
                ).pack(pady=(0, 20))
                
                ctk.CTkLabel(
                    no_data_frame,
                    text="No attendance data available yet",
                    font=("Segoe UI", 16),
                    text_color="#9CA3AF"
                ).pack()
                
                ctk.CTkLabel(
                    no_data_frame,
                    text="Start marking attendance to see analytics",
                    font=("Segoe UI", 13),
                    text_color="#D1D5DB"
                ).pack(pady=(5, 0))
                return

            # Extract data
            dates = [item['date'] for item in trend_data]
            counts = [item['count'] for item in trend_data]
            percentages = [item['percentage'] for item in trend_data]

            # Create figure
            fig = Figure(figsize=(12, 5), facecolor='white', dpi=100)
            ax = fig.add_subplot(111)
            
            # Set background
            fig.patch.set_facecolor('white')
            ax.set_facecolor('white')

            # Plot line chart
            line = ax.plot(dates, counts,
                           marker='o',
                           markersize=8,
                           linewidth=3,
                           color=COLORS['success'],
                           markerfacecolor='white',
                           markeredgecolor=COLORS['success'],
                           markeredgewidth=2,
                           label='Students Present')

            # Add fill under curve
            ax.fill_between(dates, counts, 0, alpha=0.15, color=COLORS['success'])

            # Add value labels
            for i, (date, count, pct) in enumerate(zip(dates, counts, percentages)):
                ax.annotate(f'{count}',
                            xy=(date, count),
                            xytext=(0, 10),
                            textcoords='offset points',
                            ha='center',
                            fontsize=10,
                            fontweight='bold',
                            color=COLORS['dark'])

            # Styling
            ax.set_xlabel('Date', fontsize=12, fontweight='600', color='#4B5563')
            ax.set_ylabel('Students Present', fontsize=12, fontweight='600', color='#4B5563')
            
            # Format x-axis dates
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
            ax.xaxis.set_major_locator(mdates.DayLocator())
            fig.autofmt_xdate(rotation=45, ha='right')

            # Grid
            ax.grid(True, alpha=0.2, linestyle='-', linewidth=0.8, color='#D1D5DB')
            ax.set_axisbelow(True)

            # Set y-axis limits
            y_max = max(counts) if counts else 0
            ax.set_ylim(bottom=0, top=y_max * 1.1 if y_max > 0 else 10)

            # Remove spines
            for spine in ['top', 'right']:
                ax.spines[spine].set_visible(False)
            
            for spine in ['left', 'bottom']:
                ax.spines[spine].set_color('#E5E7EB')
                ax.spines[spine].set_linewidth(1)

            # Tight layout
            fig.tight_layout()

            # Embed in Tkinter
            canvas_frame = ctk.CTkFrame(parent, fg_color="white")
            canvas_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            self.graph_canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
            self.graph_canvas.draw()
            self.graph_canvas.get_tk_widget().pack(fill="both", expand=True)

        except Exception as e:
            # Simple fallback
            error_frame = ctk.CTkFrame(parent, fg_color="transparent")
            error_frame.pack(expand=True, fill="both", pady=50)
            
            ctk.CTkLabel(
                error_frame,
                text="📊",
                font=("Segoe UI", 48),
                text_color="#D1D5DB"
            ).pack(pady=(0, 20))
            
            ctk.CTkLabel(
                error_frame,
                text="Attendance Analytics",
                font=("Segoe UI", 16),
                text_color="#9CA3AF"
            ).pack()

    def update_clock(self):
        """Update clock every second safely"""
        try:
            if hasattr(self, 'clock_label') and self.clock_label and self.clock_label.winfo_exists():
                self.clock_label.configure(text=get_display_time())
            if hasattr(self, 'date_label') and self.date_label and self.date_label.winfo_exists():
                self.date_label.configure(text=get_display_date())
            self.after(1000, self.update_clock)
        except:
            pass

    def show_students(self):
        """Show student management"""
        self.clear_content()
        self.current_frame = StudentManagement(self.content_area, self.user_data)
        self.current_frame.pack(fill="both", expand=True)

    def show_user_management(self):
        """Show admin user management"""
        self.clear_content()
        self.current_frame = UserManagement(self.content_area)
        self.current_frame.pack(fill="both", expand=True)

    def show_student_home(self):
        """Show a simplified dashboard for students"""
        self.clear_content()
        
        # Create scrollable container for student view
        self.scrollable_frame = ctk.CTkFrame(
            self.content_area, 
            fg_color=COLORS['bg_light']
        )
        self.scrollable_frame.pack(fill="both", expand=True)
        
        # Create canvas for scrolling
        canvas = ctk.CTkCanvas(
            self.scrollable_frame,
            bg=COLORS['bg_light'],
            highlightthickness=0
        )
        scrollbar = ctk.CTkScrollbar(
            self.scrollable_frame,
            orientation="vertical",
            command=canvas.yview
        )
        
        # Create main frame
        frame = ctk.CTkFrame(canvas, fg_color=COLORS['bg_light'])
        
        # Configure canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Create window in canvas
        canvas.create_window((0, 0), window=frame, anchor="nw")
        
        # Configure scroll region
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        frame.bind("<Configure>", configure_scroll_region)
        
        # Add mouse wheel scrolling
        def on_mouse_wheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind_all("<MouseWheel>", on_mouse_wheel)

        # Header
        header_frame = ctk.CTkFrame(frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(
            header_frame,
            text="My Dashboard",
            font=("Segoe UI", 28, "bold"),
            text_color=COLORS['dark']
        ).pack(side="left")
        
        ctk.CTkLabel(
            header_frame,
            text=f"👤 {self.user_data.get('name', 'Student')}",
            font=("Segoe UI", 14),
            text_color="#6B7280"
        ).pack(side="right")

        # Get student's linked student_id
        student_id = self.user_data.get('student_id')
        if not student_id:
            no_profile_frame = ctk.CTkFrame(frame, fg_color="white", corner_radius=15)
            no_profile_frame.pack(fill="x", padx=20, pady=10)
            
            ctk.CTkLabel(
                no_profile_frame,
                text="No student profile linked to your account.",
                font=("Segoe UI", 14),
                text_color="gray"
            ).pack(padx=30, pady=30)
            return

        stats = db.get_student_attendance_percentage(student_id)

        # Summary card
        summary_card = ctk.CTkFrame(
            frame,
            fg_color="white",
            corner_radius=18,
            border_width=1,
            border_color="#E5E7EB"
        )
        summary_card.pack(fill="x", padx=20, pady=(0, 20))

        # Create progress bar for attendance
        inner = ctk.CTkFrame(summary_card, fg_color="transparent")
        inner.pack(padx=30, pady=30, fill="x")
        
        ctk.CTkLabel(
            inner,
            text="🎯 Attendance Performance",
            font=("Segoe UI", 18, "bold"),
            text_color=COLORS['dark']
        ).pack(anchor="w", pady=(0, 20))
        
        # Percentage display
        percentage_frame = ctk.CTkFrame(inner, fg_color="transparent")
        percentage_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            percentage_frame,
            text=f"{stats['percentage']}%",
            font=("Segoe UI", 56, "bold"),
            text_color=COLORS['primary']
        ).pack(side="left")
        
        # Progress bar
        progress_frame = ctk.CTkFrame(percentage_frame, fg_color="transparent")
        progress_frame.pack(side="left", fill="x", expand=True, padx=(30, 0))
        
        progress_bg = ctk.CTkFrame(progress_frame, fg_color="#E5E7EB", height=12, corner_radius=6)
        progress_bg.pack(fill="x", pady=(10, 0))
        progress_bg.pack_propagate(False)
        
        progress_width = min(stats['percentage'], 100)
        progress_fill = ctk.CTkFrame(
            progress_bg, 
            fg_color=COLORS['success'],
            width=int(progress_width * 2),
            height=12,
            corner_radius=6
        )
        progress_fill.pack(side="left")
        
        # Stats details
        details_frame = ctk.CTkFrame(inner, fg_color="transparent")
        details_frame.pack(fill="x")
        
        stats_details = [
            ("✅ Present", f"{stats['present']} sessions", COLORS['success']),
            ("📋 Total", f"{stats['total_days']} sessions", "#374151"),
            ("🎯 Goal", "75% required", COLORS['warning'])
        ]
        
        for icon, text, color in stats_details:
            detail = ctk.CTkFrame(details_frame, fg_color="transparent")
            detail.pack(side="left", padx=(0, 30))
            
            ctk.CTkLabel(
                detail,
                text=icon,
                font=("Segoe UI", 16),
                text_color=color
            ).pack(side="left", padx=(0, 8))
            
            ctk.CTkLabel(
                detail,
                text=text,
                font=("Segoe UI", 13),
                text_color="#6B7280"
            ).pack(side="left")

        # Recent attendance records
        records_header = ctk.CTkFrame(frame, fg_color="transparent")
        records_header.pack(fill="x", padx=20, pady=(10, 10))
        
        ctk.CTkLabel(
            records_header,
            text="📝 Recent Attendance",
            font=("Segoe UI", 20, "bold"),
            text_color=COLORS['dark']
        ).pack(side="left")
        
        ctk.CTkLabel(
            records_header,
            text="Last 15 sessions",
            font=("Segoe UI", 13),
            text_color="#6B7280"
        ).pack(side="right")

        records = db.get_attendance(name=None, date=None, department=None)
        recs = [r for r in (records or []) if r.get('student_id') == student_id]

        lst_card = ctk.CTkFrame(
            frame,
            fg_color="white",
            corner_radius=15,
            border_width=1,
            border_color="#E5E7EB"
        )
        lst_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        if recs:
            # Add records
            for r in recs[:15]:
                record_frame = ctk.CTkFrame(lst_card, fg_color="transparent")
                record_frame.pack(fill="x", padx=20, pady=8)
                
                # Date
                ctk.CTkLabel(
                    record_frame,
                    text=r['date'],
                    font=("Segoe UI", 12),
                    text_color="#1F2937",
                    anchor="w",
                    width=100
                ).pack(side="left")
                
                # Time
                time_str = r.get('time', 'N/A')
                ctk.CTkLabel(
                    record_frame,
                    text=time_str,
                    font=("Segoe UI", 12),
                    text_color="#6B7280",
                    anchor="w",
                    width=80
                ).pack(side="left")
                
                # Status
                status_color = COLORS['success'] if r['status'] == 'Present' else COLORS['danger']
                status_bg = "#D1FAE5" if r['status'] == 'Present' else "#FEE2E2"
                
                status_frame = ctk.CTkFrame(
                    record_frame,
                    fg_color=status_bg,
                    height=28,
                    corner_radius=14
                )
                status_frame.pack(side="left", padx=(0, 20))
                status_frame.pack_propagate(False)
                
                ctk.CTkLabel(
                    status_frame,
                    text=r['status'],
                    font=("Segoe UI", 11, "bold"),
                    text_color=status_color,
                    padx=15
                ).pack(expand=True)
                
                # Department
                ctk.CTkLabel(
                    record_frame,
                    text=r.get('department', 'N/A'),
                    font=("Segoe UI", 12),
                    text_color="#6B7280",
                    anchor="w"
                ).pack(side="left", fill="x", expand=True)
        else:
            ctk.CTkLabel(
                lst_card,
                text="No attendance records found",
                font=("Segoe UI", 14),
                text_color="#9CA3AF"
            ).pack(pady=50)

    def show_attendance(self):
        """Show attendance records"""
        self.clear_content()
        self.current_frame = AttendanceModule(self.content_area, self.user_data)
        self.current_frame.pack(fill="both", expand=True)

    def start_face_recognition(self):
        """Start face recognition for attendance marking"""
        confirm_window = ctk.CTkToplevel(self)
        confirm_window.title("Mark Attendance")
        confirm_window.geometry("500x280")
        confirm_window.resizable(False, False)
        confirm_window.grab_set()
        
        # Center window
        confirm_window.update_idletasks()
        width = confirm_window.winfo_width()
        height = confirm_window.winfo_height()
        x = (confirm_window.winfo_screenwidth() // 2) - (width // 2)
        y = (confirm_window.winfo_screenheight() // 2) - (height // 2)
        confirm_window.geometry(f"{width}x{height}+{x}+{y}")

        # Create modal content
        modal_frame = ctk.CTkFrame(
            confirm_window, 
            fg_color="white",
            corner_radius=20,
            border_width=1,
            border_color="#E5E7EB"
        )
        modal_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Icon/Header
        icon_frame = ctk.CTkFrame(modal_frame, fg_color="transparent")
        icon_frame.pack(pady=(25, 15))
        
        ctk.CTkLabel(
            icon_frame,
            text="📸",
            font=("Segoe UI", 48)
        ).pack()

        # Title
        ctk.CTkLabel(
            modal_frame,
            text="Start Face Recognition",
            font=("Segoe UI", 22, "bold"),
            text_color=COLORS['dark']
        ).pack(pady=(0, 10))

        # Description
        ctk.CTkLabel(
            modal_frame,
            text="Camera will open for real-time attendance marking.\nStudents will be automatically recognized and marked present.",
            font=("Segoe UI", 13),
            text_color="#6B7280",
            wraplength=400,
            justify="center"
        ).pack(pady=(0, 30))

        # Buttons
        button_frame = ctk.CTkFrame(modal_frame, fg_color="transparent")
        button_frame.pack(pady=(0, 25))

        def start_recognition():
            confirm_window.destroy()
            threading.Thread(target=self.run_face_recognition, daemon=True).start()

        ctk.CTkButton(
            button_frame,
            text="🚀 Start Recognition",
            width=180,
            height=45,
            font=("Segoe UI", 14, "bold"),
            fg_color=COLORS['success'],
            hover_color=COLORS['success'],
            corner_radius=12,
            command=start_recognition
        ).pack(side="left", padx=(0, 15))

        ctk.CTkButton(
            button_frame,
            text="Cancel",
            width=180,
            height=45,
            font=("Segoe UI", 14),
            fg_color="transparent",
            hover_color="#F3F4F6",
            text_color="#6B7280",
            border_width=1,
            border_color="#D1D5DB",
            corner_radius=12,
            command=confirm_window.destroy
        ).pack(side="left")

        # Footer note
        ctk.CTkLabel(
            modal_frame,
            text="Press ESC to stop the camera",
            font=("Segoe UI", 11),
            text_color="#9CA3AF"
        ).pack(pady=(10, 0))

    def run_face_recognition(self):
        """Run face recognition for attendance"""
        try:
            # Get all students with embeddings
            students = db.get_all_students()

            if not students:
                self.after(0, lambda: show_toast(self, "No students registered", "warning"))
                return

            # Create database of embeddings
            database_students = {}
            for student in students:
                if student['face_embedding']:
                    try:
                        embedding = json.loads(student['face_embedding'])
                        database_students[student['student_id']] = embedding
                    except:
                        pass

            if not database_students:
                self.after(0, lambda: show_toast(self, "No student face data found", "warning"))
                return

            # Callback for marking attendance
            def mark_attendance_callback(student_id):
                student = db.get_student_by_id(student_id)
                if student:
                    success, message = db.mark_attendance(
                        student_id,
                        student['name'],
                        student['department'],
                        datetime.now().date(),
                        datetime.now().time()
                    )

                    if success:
                        self.after(0, lambda: show_toast(self, f"✅ Attendance marked for {student['name']}", "success"))
                        return True
                    else:
                        self.after(0, lambda: show_toast(self, message, "warning"))
                        return False
                return False

            # Start detection - call the existing face recognition module
            marked_count = face_recognizer.detect_and_mark_attendance(database_students, mark_attendance_callback)

            # Show completion message
            self.after(0, lambda: show_toast(self, f"Attendance marking completed. Total: {marked_count}", "info"))

            # Refresh if on home
            if hasattr(self.current_frame, 'stats_label'):
                self.after(1000, self.show_home)

        except Exception as e:
            self.after(0, lambda: show_toast(self, f"Recognition error: {str(e)}", "error"))

    def logout(self):
        """Logout user"""
        confirm_window = ctk.CTkToplevel(self)
        confirm_window.title("Confirm Logout")
        confirm_window.geometry("400x220")
        confirm_window.resizable(False, False)
        confirm_window.grab_set()
        
        # Center window
        confirm_window.update_idletasks()
        width = confirm_window.winfo_width()
        height = confirm_window.winfo_height()
        x = (confirm_window.winfo_screenwidth() // 2) - (width // 2)
        y = (confirm_window.winfo_screenheight() // 2) - (height // 2)
        confirm_window.geometry(f"{width}x{height}+{x}+{y}")

        # Modal content
        modal_frame = ctk.CTkFrame(
            confirm_window, 
            fg_color="white",
            corner_radius=20,
            border_width=1,
            border_color="#E5E7EB"
        )
        modal_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Warning icon
        ctk.CTkLabel(
            modal_frame,
            text="⚠️",
            font=("Segoe UI", 44),
            text_color=COLORS['warning']
        ).pack(pady=(20, 10))

        # Title
        ctk.CTkLabel(
            modal_frame,
            text="Confirm Logout",
            font=("Segoe UI", 20, "bold"),
            text_color=COLORS['dark']
        ).pack(pady=(0, 10))

        # Message
        ctk.CTkLabel(
            modal_frame,
            text="Are you sure you want to logout?",
            font=("Segoe UI", 13),
            text_color="#6B7280"
        ).pack(pady=(0, 25))

        # Buttons
        button_frame = ctk.CTkFrame(modal_frame, fg_color="transparent")
        button_frame.pack()

        ctk.CTkButton(
            button_frame,
            text="Yes, Logout",
            width=140,
            height=40,
            font=("Segoe UI", 13, "bold"),
            fg_color=COLORS['danger'],
            hover_color=COLORS['danger'],
            corner_radius=10,
            command=lambda: (confirm_window.destroy(), self.on_logout())
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            button_frame,
            text="Cancel",
            width=140,
            height=40,
            font=("Segoe UI", 13),
            fg_color="transparent",
            hover_color="#F3F4F6",
            text_color="#6B7280",
            border_width=1,
            border_color="#D1D5DB",
            corner_radius=10,
            command=confirm_window.destroy
        ).pack(side="left")


