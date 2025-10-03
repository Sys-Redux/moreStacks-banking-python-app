import tkinter as tk
from tkinter import messagebox
from database.db_manager import DatabaseManager


class LoginWindow:
    """Login and registration window for moreStacks Banking."""

    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        self.db = DatabaseManager()

        # Window setup
        self.root.title("moreStacks Banking - Login")
        self.root.geometry("450x700")  # Increased height significantly
        self.root.resizable(False, False)

        # Colors
        self.primary_color = "#1a237e"
        self.secondary_color = "#3949ab"
        self.accent_color = "#00c853"
        self.bg_color = "#f5f5f5"
        self.white = "#ffffff"

        self.root.configure(bg=self.bg_color)

        self.create_widgets()

    def create_widgets(self):
        """Create login interface widgets."""
        # Header
        header_frame = tk.Frame(self.root, bg=self.primary_color, height=120)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        title = tk.Label(
            header_frame,
            text="moreStacks",
            font=("Helvetica", 36, "bold"),
            bg=self.primary_color,
            fg=self.white
        )
        title.pack(pady=20)

        subtitle = tk.Label(
            header_frame,
            text="Banking Made Simple",
            font=("Helvetica", 12),
            bg=self.primary_color,
            fg=self.white
        )
        subtitle.pack()

        # Main frame
        main_frame = tk.Frame(self.root, bg=self.white, padx=40, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        # Title
        login_title = tk.Label(
            main_frame,
            text="Sign In",
            font=("Helvetica", 20, "bold"),
            bg=self.white,
            fg=self.primary_color
        )
        login_title.pack(pady=(0, 20))

        # Username
        username_label = tk.Label(
            main_frame,
            text="Username:",
            font=("Helvetica", 11),
            bg=self.white,
            fg=self.primary_color
        )
        username_label.pack(anchor=tk.W, pady=(10, 5))

        self.username_entry = tk.Entry(
            main_frame,
            font=("Helvetica", 12),
            bd=2,
            relief=tk.SOLID
        )
        self.username_entry.pack(fill=tk.X, ipady=8)

        # Password
        password_label = tk.Label(
            main_frame,
            text="Password:",
            font=("Helvetica", 11),
            bg=self.white,
            fg=self.primary_color
        )
        password_label.pack(anchor=tk.W, pady=(15, 5))

        self.password_entry = tk.Entry(
            main_frame,
            font=("Helvetica", 12),
            bd=2,
            relief=tk.SOLID,
            show="●"
        )
        self.password_entry.pack(fill=tk.X, ipady=8)

        # Bind Enter key to login
        self.password_entry.bind('<Return>', lambda e: self.login())

        # Login button
        login_btn = tk.Button(
            main_frame,
            text="Sign In",
            font=("Helvetica", 13, "bold"),
            bg=self.accent_color,
            fg=self.white,
            bd=0,
            pady=12,
            cursor="hand2",
            command=self.login,
            activebackground="#00e676"
        )
        login_btn.pack(fill=tk.X, pady=(25, 10))

        # Divider
        divider_frame = tk.Frame(main_frame, bg=self.white)
        divider_frame.pack(fill=tk.X, pady=20)

        tk.Frame(divider_frame, bg="#cccccc", height=1).pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(divider_frame, text=" OR ", bg=self.white, fg="#666666", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT, padx=10)
        tk.Frame(divider_frame, bg="#cccccc", height=1).pack(side=tk.RIGHT, fill=tk.X, expand=True)

        # New user prompt
        new_user_text = tk.Label(
            main_frame,
            text="Don't have an account?",
            font=("Helvetica", 11),
            bg=self.white,
            fg="#333333"
        )
        new_user_text.pack(pady=(10, 5))

        # Register button - Professional and visible
        register_btn = tk.Button(
            main_frame,
            text="Create New Account",
            font=("Helvetica", 13, "bold"),
            bg=self.secondary_color,  # Professional blue
            fg=self.white,
            bd=0,
            relief=tk.FLAT,
            pady=14,
            cursor="hand2",
            command=self.show_register,
            activebackground="#5c6bc0"
        )
        register_btn.pack(fill=tk.X, pady=(5, 15), padx=5)

        # Footer
        footer = tk.Label(
            self.root,
            text="© 2025 moreStacks Banking. All rights reserved.",
            font=("Helvetica", 9),
            bg=self.bg_color,
            fg="#666666"
        )
        footer.pack(pady=10)

    def login(self):
        """Handle login attempt."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password.")
            return

        user_id = self.db.authenticate_user(username, password)

        if user_id:
            user_info = self.db.get_user_info(user_id)
            self.on_login_success(user_id, user_info)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")
            self.password_entry.delete(0, tk.END)

    def show_register(self):
        """Show registration window."""
        RegisterWindow(self.root, self.db, self.on_registration_success)

    def on_registration_success(self, user_id, user_info):
        """Handle successful registration."""
        messagebox.showinfo("Success",
                          f"Account created successfully!\nWelcome, {user_info['full_name']}!")
        self.on_login_success(user_id, user_info)


class RegisterWindow:
    """Registration window for new users."""

    def __init__(self, parent, db, on_success):
        self.parent = parent
        self.db = db
        self.on_success = on_success

        # Create new window
        self.window = tk.Toplevel(parent)
        self.window.title("moreStacks Banking - Register")
        self.window.geometry("450x700")  # Increased height to show all fields and buttons
        self.window.resizable(False, False)

        # Colors
        self.primary_color = "#1a237e"
        self.secondary_color = "#3949ab"
        self.accent_color = "#00c853"
        self.bg_color = "#f5f5f5"
        self.white = "#ffffff"

        self.window.configure(bg=self.bg_color)

        # Make window modal
        self.window.transient(parent)
        self.window.grab_set()

        self.create_widgets()

    def create_widgets(self):
        """Create registration interface widgets."""
        # Header
        header_frame = tk.Frame(self.window, bg=self.primary_color, height=100)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        title = tk.Label(
            header_frame,
            text="Create Account",
            font=("Helvetica", 24, "bold"),
            bg=self.primary_color,
            fg=self.white
        )
        title.pack(pady=30)

        # Main frame
        main_frame = tk.Frame(self.window, bg=self.white, padx=40, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        # Full Name
        self._create_field(main_frame, "Full Name:", "full_name_entry")

        # Username
        self._create_field(main_frame, "Username:", "username_entry")

        # Password
        password_label = tk.Label(
            main_frame,
            text="Password:",
            font=("Helvetica", 11),
            bg=self.white,
            fg=self.primary_color
        )
        password_label.pack(anchor=tk.W, pady=(15, 5))

        self.password_entry = tk.Entry(
            main_frame,
            font=("Helvetica", 12),
            bd=2,
            relief=tk.SOLID,
            show="●"
        )
        self.password_entry.pack(fill=tk.X, ipady=8)

        # Confirm Password
        confirm_label = tk.Label(
            main_frame,
            text="Confirm Password:",
            font=("Helvetica", 11),
            bg=self.white,
            fg=self.primary_color
        )
        confirm_label.pack(anchor=tk.W, pady=(15, 5))

        self.confirm_entry = tk.Entry(
            main_frame,
            font=("Helvetica", 12),
            bd=2,
            relief=tk.SOLID,
            show="●"
        )
        self.confirm_entry.pack(fill=tk.X, ipady=8)

        # Email (optional)
        self._create_field(main_frame, "Email (optional):", "email_entry")

        # Register button
        register_btn = tk.Button(
            main_frame,
            text="Create Account",
            font=("Helvetica", 13, "bold"),
            bg=self.accent_color,
            fg=self.white,
            bd=0,
            pady=12,
            cursor="hand2",
            command=self.register,
            activebackground="#00e676"
        )
        register_btn.pack(fill=tk.X, pady=(25, 10))

        # Cancel button
        cancel_btn = tk.Button(
            main_frame,
            text="Cancel",
            font=("Helvetica", 11),
            bg=self.white,
            fg="#666666",
            bd=0,
            cursor="hand2",
            command=self.window.destroy
        )
        cancel_btn.pack()

    def _create_field(self, parent, label_text, entry_name):
        """Helper to create label and entry field."""
        label = tk.Label(
            parent,
            text=label_text,
            font=("Helvetica", 11),
            bg=self.white,
            fg=self.primary_color
        )
        label.pack(anchor=tk.W, pady=(15, 5))

        entry = tk.Entry(
            parent,
            font=("Helvetica", 12),
            bd=2,
            relief=tk.SOLID
        )
        entry.pack(fill=tk.X, ipady=8)
        setattr(self, entry_name, entry)

    def register(self):
        """Handle registration."""
        full_name = self.full_name_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        confirm = self.confirm_entry.get()
        email = self.email_entry.get().strip()

        # Validation
        if not full_name or not username or not password:
            messagebox.showerror("Error", "Please fill in all required fields.")
            return

        if len(username) < 3:
            messagebox.showerror("Error", "Username must be at least 3 characters.")
            return

        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters.")
            return

        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match.")
            return

        # Create user
        user_id = self.db.create_user(username, password, full_name, email)

        if user_id:
            # Create default checking account
            account_id, account_number = self.db.create_account(
                user_id, 'checking', 0
            )

            user_info = self.db.get_user_info(user_id)
            self.window.destroy()
            self.on_success(user_id, user_info)
        else:
            messagebox.showerror("Error", "Username already exists. Please choose another.")
