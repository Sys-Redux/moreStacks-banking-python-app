import tkinter as tk
from tkinter import messagebox
from database.db_manager import DatabaseManager
from gui.gui_utils import COLORS, FONTS, create_header_frame, create_labeled_entry, create_button, create_divider, create_modal_dialog, create_button_pair


class LoginWindow:
    """Login and registration window for moreStacks Banking."""

    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        self.db = DatabaseManager()

        # Window setup
        self.root.title("moreStacks Banking - Login")
        self.root.geometry("450x700")
        self.root.resizable(False, False)
        self.root.configure(bg=COLORS['background'])

        self.create_widgets()

    def create_widgets(self):
        """Create login interface widgets."""
        # Header
        create_header_frame(self.root, "moreStacks", "Banking Made Simple")

        # Main frame
        main_frame = tk.Frame(self.root, bg=COLORS['white'], padx=40, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        # Title
        login_title = tk.Label(
            main_frame,
            text="Sign In",
            font=FONTS['title_small'],
            bg=COLORS['white'],
            fg=COLORS['primary']
        )
        login_title.pack(pady=(0, 20))

        # Username and Password entries
        self.username_entry = create_labeled_entry(main_frame, "Username:", pady_top=10)
        self.password_entry = create_labeled_entry(main_frame, "Password:", show="●", pady_top=15)

        # Bind Enter key to login
        self.password_entry.bind('<Return>', lambda e: self.login())

        # Login button
        create_button(
            main_frame,
            "Sign In",
            self.login,
            color_key='accent',
            fill=tk.X,
            pady=(25, 10)
        )

        # Divider
        create_divider(main_frame, "OR", pady=20)

        # New user prompt
        new_user_text = tk.Label(
            main_frame,
            text="Don't have an account?",
            font=FONTS['label'],
            bg=COLORS['white'],
            fg=COLORS['text_primary']
        )
        new_user_text.pack(pady=(10, 5))

        # Register button
        create_button(
            main_frame,
            "Create New Account",
            self.show_register,
            color_key='secondary',
            fill=tk.X,
            pady=(5, 15),
            padx=5
        )

        # Footer
        footer = tk.Label(
            self.root,
            text="© 2025 moreStacks Banking. All rights reserved.",
            font=FONTS['tiny'],
            bg=COLORS['background'],
            fg=COLORS['text_secondary']
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
        self.window = create_modal_dialog(parent, "moreStacks Banking - Register", 450, 700)

        self.create_widgets()

    def create_widgets(self):
        """Create registration interface widgets."""
        # Header
        header_frame = tk.Frame(self.window, bg=COLORS['primary'], height=100)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        title = tk.Label(
            header_frame,
            text="Create Account",
            font=FONTS['title_medium'],
            bg=COLORS['primary'],
            fg=COLORS['white']
        )
        title.pack(pady=30)

        # Main frame
        main_frame = tk.Frame(self.window, bg=COLORS['white'], padx=40, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        # Full Name, Username, Password, Confirm Password, Email
        self.full_name_entry = create_labeled_entry(main_frame, "Full Name:", pady_top=0)
        self.username_entry = create_labeled_entry(main_frame, "Username:")
        self.password_entry = create_labeled_entry(main_frame, "Password:", show="●")
        self.confirm_entry = create_labeled_entry(main_frame, "Confirm Password:", show="●")
        self.email_entry = create_labeled_entry(main_frame, "Email (optional):")

        # Buttons
        create_button(
            main_frame,
            "Create Account",
            self.register,
            color_key='accent',
            fill=tk.X,
            pady=(25, 10)
        )

        cancel_btn = tk.Button(
            main_frame,
            text="Cancel",
            font=FONTS['label'],
            bg=COLORS['white'],
            fg=COLORS['text_secondary'],
            bd=0,
            cursor="hand2",
            command=self.window.destroy
        )
        cancel_btn.pack()

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
