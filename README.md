# moreStacks Banking Application

A professional, full-featured banking application built with Python and Tkinter, featuring multiple account types, secure authentication, transaction tracking, and data persistence.

**Version 2.5.0** - Now with Session Management & Timeout Security!

## Recent Updates (v2.5.0)

### 🔒 Session Management & Security
- ✅ **Automatic session timeout** (15 minutes default, configurable)
- ✅ **Activity-based tracking** - Mouse/keyboard activity resets timer
- ✅ **Session warning system** - Alert 1 minute before expiration
- ✅ **Automatic logout** - Secure cleanup on session expiration
- ✅ **Background cleanup** - Expired sessions removed every 60 seconds
- ✅ **50 comprehensive tests** - Full coverage of session functionality

See [`docs/RELEASE_NOTES_V2.5.md`](docs/RELEASE_NOTES_V2.5.md) for complete details.

### 🐛 Previous Updates (v1.1.0)
- ✅ **Popup windows now close automatically** after successful operations
- ✅ **New accounts appear immediately** without requiring logout/login
- ✅ **Account dropdown refreshes** in real-time when accounts are created
- ✅ **60% reduction in duplicate code** through DRY principles
- ✅ **Centralized GUI utilities** for consistent styling

See `REFACTORING_REPORT.md` for detailed technical information.

## Features

### 🔐 Authentication & Security
- **User Registration & Login**: Secure user account creation with bcrypt password hashing
- **Session Management**: Automatic timeout after 15 minutes of inactivity
- **Activity Tracking**: Mouse/keyboard activity extends session automatically
- **Session Warnings**: Alert before timeout with option to extend
- **Account Lockout**: Protection against brute force (5 failed attempts, 15-minute lockout)
- **Password Validation**: Strong password requirements enforced
- **Multi-user Support**: Each user can have multiple bank accounts

### 💳 Account Types
1. **Checking Account**
   - Standard deposit and withdrawal
   - Overdraft protection (up to $500)
   - No withdrawal limits

2. **Savings Account**
   - Interest-bearing (2% annual rate)
   - Minimum balance requirement ($100)
   - Monthly withdrawal limit (6 transactions)
   - Interest calculation and application

3. **Credit Account**
   - Credit limit ($5,000 default)
   - Interest charges on outstanding balance (18% APR)
   - Payment tracking
   - Available credit display

### 💰 Transaction Management
- **Deposit Money**: Add funds to any account
- **Withdraw Money**: Remove funds with validation
- **Transfer Between Accounts**: Move money between your accounts instantly
- **Transaction Categories**: Organize transactions (Food & Dining, Shopping, Bills, etc.)
- **Transaction History**: Full history with filtering by category
- **Export to CSV**: Download transaction records for external analysis

### 📊 Analytics & Insights (NEW in v1.2.0!)
- **Spending by Category**: Interactive pie chart showing where your money goes
- **Balance History**: Line graph tracking your balance trends over time
- **Monthly Comparison**: Bar chart comparing income vs expenses
- **All Accounts Overview**: Quick visual snapshot of all account balances
- **Professional Charts**: Powered by matplotlib with beautiful visualizations
- **Real-time Data**: Charts update automatically from your transaction history

### 📊 Data Persistence
- **SQLite Database**: All data is permanently stored
- **Transaction Records**: Complete audit trail of all operations
- **Account Balance Tracking**: Real-time balance updates
- **User Information Storage**: Profile and account details

### 🎨 Professional UI/UX
- Clean, modern interface with professional banking colors
- Intuitive navigation and account switching
- Real-time balance updates
- Responsive buttons and forms
- Error handling with user-friendly messages

## Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Option 1: One-Click Setup (Easiest!)

**Windows:**
```bash
# Double-click setup.bat or run:
setup.bat
```

**Linux/macOS:**
```bash
# Double-click setup.sh or run:
./setup.sh
```

The setup script will:
1. ✅ Check your Python version
2. ✅ Install all dependencies automatically
3. ✅ Launch the application

### Option 2: Manual Setup
```bash
# 1. Navigate to the project directory
cd BankApp

# 2. Install dependencies (includes matplotlib for analytics)
pip install -r requirements.txt

# 3. Run the application
python main.py
```

### Option 3: Python Setup Script
```bash
python setup.py
```

**That's it!** All features including the Analytics Dashboard will be available.

## Usage

### First Time Setup
1. Launch the application: `python main.py`
2. Click "Create New Account" on the login screen
3. Fill in your details:
   - Full Name
   - Username (minimum 3 characters)
   - Password (minimum 6 characters)
   - Email (optional)
4. Click "Create Account"
5. A default checking account will be created automatically

### Login
1. Enter your username and password
2. Click "Sign In"
3. You'll be taken to your dashboard

### Managing Accounts
- **View Accounts**: Use the dropdown at the top-left to switch between accounts
- **Create New Account**: Click "+ New Account" button
  - Choose account type (Checking, Savings, or Credit)
  - Set initial deposit amount
- **Check Balance**: Your current balance is displayed prominently for the selected account

### Making Transactions
1. Select the account from the dropdown
2. Enter the amount
3. Choose a category (optional but recommended)
4. Click the appropriate button:
   - **Deposit**: Add money to account
   - **Withdraw**: Remove money from account
   - **Transfer**: Move money to another account

### Viewing Transaction History
- All transactions appear in the right panel
- Use the filter dropdown to view specific categories
- Export transactions to CSV for record-keeping

### Using Analytics Dashboard (NEW!)
1. Click the **"📊 Analytics"** button in the top-right corner
2. Explore different chart types:
   - **Spending by Category**: See where your money goes
   - **Balance History**: Track your balance over time
   - **Monthly Comparison**: Compare income vs expenses
   - **All Accounts Overview**: See all balances at once
3. Charts update automatically as you make transactions
4. Window is resizable for better viewing

**Tip:** Make several transactions across different categories to see the most insightful charts!

### Account-Specific Features

#### Savings Account
- Interest is calculated but must be applied manually (feature for future automation)
- Monthly withdrawal limit enforced
- Minimum balance maintained

#### Credit Account
- Shows available credit
- Deposits are payments toward your balance
- Withdrawals are charges/purchases
- Interest calculated on outstanding balance

## Project Structure

```
BankApp/
├── main.py                 # Application entry point
├── config.py               # Configuration file (account defaults, security settings)
├── README.md              # This file
│
├── database/              # Database layer
│   ├── __init__.py
│   └── db_manager.py       # SQLite database operations
│
├── models/                # Business logic
│   ├── __init__.py
│   └── account.py          # Account classes (Checking, Savings, Credit)
│
├── gui/                   # User interface
│   ├── __init__.py
│   ├── gui_utils.py        # Shared GUI utilities and styling
│   ├── login_window.py     # Login and registration interface
│   ├── main_window.py      # Main banking dashboard
│   └── charts_window.py    # Analytics and data visualization
│
├── utils/                 # Utility functions
│   ├── password_validator.py  # Password strength validation
│   └── interest_scheduler.py  # Automated interest calculation
│
├── tests/                 # Test suite (120 tests, 84% coverage)
│   ├── test_accounts.py    # Account model tests (34 tests)
│   ├── test_database.py    # Database operation tests (31 tests)
│   ├── test_integration.py # End-to-end tests (11 tests)
│   ├── test_security.py    # Security feature tests (20 tests)
│   └── test_interest.py    # Interest system tests (21 tests)
│
└── docs/                  # 📚 Documentation
    ├── RoadMap.md          # Strategic development roadmap
    ├── QUICKSTART.md       # 60-second getting started guide
    ├── INSTALLATION.md     # Detailed installation instructions
    ├── TESTING.md          # Testing guide and best practices
    ├── SECURITY.md         # Security implementation guide (439 lines)
    ├── INTEREST.md         # Interest automation guide (368 lines)
    ├── RELEASE_NOTES_V2.4.md  # Version 2.4 changelog
    └── CLEANUP_SUMMARY.md  # Recent refactoring documentation
```

## Database Schema

### Users Table
- user_id (Primary Key)
- username (Unique)
- password_hash
- full_name
- email
- phone
- created_at
- last_login

### Accounts Table
- account_id (Primary Key)
- user_id (Foreign Key)
- account_number (Unique)
- account_type
- balance
- interest_rate
- credit_limit
- status
- created_at

### Transactions Table
- transaction_id (Primary Key)
- account_id (Foreign Key)
- transaction_type
- amount
- category
- description
- balance_after
- timestamp

### Transfers Table
- transfer_id (Primary Key)
- from_account_id (Foreign Key)
- to_account_id (Foreign Key)
- amount
- description
- timestamp

## Features Demonstration

### Example Workflow
1. **Register**: Create user "John Doe" with username "johndoe"
2. **Login**: Sign in with credentials
3. **Create Accounts**:
   - Add a Savings account with $5,000 initial deposit
   - Add a Credit account
4. **Transactions**:
   - Deposit $2,000 to Checking (category: Salary)
   - Withdraw $500 for rent (category: Bills & Utilities)
   - Transfer $1,000 to Savings
5. **Track**: View filtered transaction history
6. **Export**: Download CSV report

## Configuration

The application uses `config.py` for centralized configuration:

### Customizable Settings
- **Account Defaults**: Overdraft limits, interest rates, credit limits
- **Security Settings**: Password requirements, lockout duration, bcrypt rounds
- **Interest Automation**: Cycle days, calculation parameters
- **Transaction Categories**: Customizable category list
- **GUI Settings**: Window dimensions, currency formatting, date formats

To customize, edit `config.py` and restart the application. All settings are documented with comments.

## Security Notes

✅ **Version 2.5 Security Features**
- **Session timeout** management (15-minute default, configurable)
- **Activity tracking** - Automatic session extension on user activity
- **Session warnings** - Alert 1 minute before expiration with extend option
- **Automatic logout** - Secure cleanup when session expires
- **Password hashing** using **bcrypt** (industry standard, 10 rounds)
- **Account lockout** after 5 failed login attempts (15-minute duration)
- **Password strength validation** (8+ chars, uppercase, lowercase, digit, special)
- **SQL injection protection** via parameterized queries
- **Complete audit trail** of all transactions
- **170 security tests** with 83% code coverage

⚠️ **Still Educational/Demo**
- No SSL/TLS for database connections (use file-based SQLite)
- 2FA not yet implemented (planned for Phase 1 continuation)
- For production: add SSL/TLS, 2FA, encryption at rest, and professional security audit

## Future Enhancements

See [`docs/RoadMap.md`](docs/RoadMap.md) for the complete strategic development plan, including:
- **Phase 1** (In Progress): ~~Session timeout~~, 2FA, password expiration, enhanced audit logs
- **Phase 2**: Budgeting system, savings goals, recurring transactions
- **Phase 3**: PDF statements, advanced reporting, tax preparation
- **Phase 4**: Theme toggle, accessibility improvements, localization
- **Phase 5**: Loan management, investment portfolio, multi-currency
- **Phase 6**: Web version (Flask), mobile app, API platform

## Documentation

All comprehensive guides are in the [`docs/`](docs/) directory:

| Document | Description |
|----------|-------------|
| [QUICKSTART.md](docs/QUICKSTART.md) | Get started in 60 seconds |
| [RoadMap.md](docs/RoadMap.md) | Strategic development plan with 6 phases |
| [INSTALLATION.md](docs/INSTALLATION.md) | Detailed installation guide for all platforms |
| [TESTING.md](docs/TESTING.md) | Testing guide and best practices |
| [SECURITY.md](docs/SECURITY.md) | Security features (sessions, bcrypt, lockout) |
| [INTEREST.md](docs/INTEREST.md) | Interest automation system documentation |
| [RELEASE_NOTES_V2.5.md](docs/RELEASE_NOTES_V2.5.md) | Latest version changelog (Session Management) |
| [RELEASE_NOTES_V2.4.md](docs/RELEASE_NOTES_V2.4.md) | Previous version (bcrypt, lockout) |
| [CLEANUP_SUMMARY.md](docs/CLEANUP_SUMMARY.md) | Recent refactoring documentation |

## Technical Details

### Technologies Used
- **Python 3.x**: Core programming language
- **Tkinter**: GUI framework
- **SQLite3**: Database engine
- **CSV**: Transaction export format

### Design Patterns
- **MVC Architecture**: Separation of models, views, and data
- **Factory Pattern**: Account creation
- **Observer Pattern**: UI updates on data changes

## Troubleshooting

### Common Issues

**Issue**: "No module named 'tkinter'"
- **Solution**: Install tkinter: `sudo apt-get install python3-tk` (Linux) or reinstall Python with tkinter enabled

**Issue**: Database locked error
- **Solution**: Close all instances of the application

**Issue**: Window doesn't appear
- **Solution**: Check if the window is hidden behind other windows or minimize/maximize

## Contributing

This is an educational project. Feel free to fork and enhance with additional features!

## License

This project is open-source and available for educational purposes.

## Credits

**Developed for**: Coding Temple - Python Course
**Project**: moreStacks Banking Application
**Version**: 2.0
**Date**: October 2025

---

## Quick Start Commands

```bash
# Run the application
python main.py

# Or make it executable (Linux/Mac)
chmod +x main.py
./main.py
```

## Support

For issues or questions about this educational project, refer to the code comments and documentation within each module.

---

**moreStacks Banking** - Banking Made Simple 💰
