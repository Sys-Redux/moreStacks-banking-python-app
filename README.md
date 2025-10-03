# moreStacks Banking Application

A professional, full-featured banking application built with Python and Tkinter, featuring multiple account types, secure authentication, transaction tracking, and data persistence.

## Features

### 🔐 Authentication & Security
- **User Registration & Login**: Secure user account creation with password hashing (SHA-256)
- **Session Management**: Proper authentication flow with logout functionality
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
- tkinter (usually comes with Python)

### Setup
1. Clone or download this repository
2. Navigate to the BankApp directory:
   ```bash
   cd BankApp
   ```

3. Run the application:
   ```bash
   python main.py
   ```

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
├── database/
│   ├── __init__.py
│   └── db_manager.py       # SQLite database operations
├── models/
│   ├── __init__.py
│   └── account.py          # Account classes (Checking, Savings, Credit)
├── gui/
│   ├── __init__.py
│   ├── login_window.py     # Login and registration interface
│   └── main_window.py      # Main banking dashboard
├── BankAccount.py          # Original simple version (deprecated)
├── instructions.md         # Development roadmap
└── README.md              # This file
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

## Security Notes

⚠️ **For Educational/Demo Purposes**
- Password hashing uses SHA-256 (for production, use bcrypt or similar)
- No SSL/TLS for database (use encryption for production)
- Session management is basic (implement proper sessions for production)

## Future Enhancements

See `instructions.md` for the complete development roadmap, including:
- Data visualization with charts
- Automated interest calculations
- Budgeting tools
- Monthly statements (PDF)
- Bill payment scheduling
- Investment tracking
- Mobile-responsive design
- API integration

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
