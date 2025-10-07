"""
Charts and Data Visualization Module
Provides interactive charts for spending analysis and balance trends
"""

import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta
from gui.gui_utils import (
    COLORS,
    FONTS,
    create_header_frame,
    create_button,
    setup_dark_theme,
)

# Matplotlib imports
import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class ChartsWindow:
    """Window for displaying various financial charts and visualizations."""

    def __init__(self, parent, user_id, db, accounts):
        self.parent = parent
        self.user_id = user_id
        self.db = db
        self.accounts = accounts

        if not accounts:
            messagebox.showinfo(
                "No Data", "Please create an account first to view charts."
            )
            return

        self.window = tk.Toplevel(parent)
        self.window.title("moreStacks Banking - Analytics Dashboard")
        self.window.geometry("1100x700")
        self.window.resizable(True, True)
        self.window.configure(bg=COLORS["bg_dark"])

        # Setup dark theme for consistent button appearance
        setup_dark_theme()

        self.create_widgets()

    def create_widgets(self):
        """Create the charts interface."""
        # Header
        create_header_frame(
            self.window,
            "Analytics Dashboard",
            "Financial Insights & Trends",
            height=100,
        )

        # Button toolbar
        toolbar = tk.Frame(self.window, bg=COLORS["bg_card"])
        toolbar.pack(fill=tk.X, padx=20, pady=(15, 10))

        button_frame = tk.Frame(toolbar, bg=COLORS["bg_card"])
        button_frame.pack(pady=8)

        create_button(
            button_frame,
            "📊 Spending by Category",
            self.show_spending_pie_chart,
            color_key="green",
            font_key="small",
            side=tk.LEFT,
            padx=5,
        )

        create_button(
            button_frame,
            "📈 Balance History",
            self.show_balance_history,
            color_key="blue",
            font_key="small",
            side=tk.LEFT,
            padx=5,
        )

        create_button(
            button_frame,
            "📉 Monthly Comparison",
            self.show_monthly_comparison,
            color_key="orange",
            font_key="small",
            side=tk.LEFT,
            padx=5,
        )

        create_button(
            button_frame,
            "🏦 All Accounts Overview",
            self.show_accounts_overview,
            color_key="blue",
            font_key="small",
            side=tk.LEFT,
            padx=5,
        )

        # Chart display area
        self.chart_frame = tk.Frame(self.window, bg=COLORS["bg_dark"])
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(5, 20))

        # Initial chart
        self.show_spending_pie_chart()

    def clear_chart_frame(self):
        """Clear the current chart."""
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

    def show_spending_pie_chart(self):
        """Display spending breakdown by category as a pie chart."""
        self.clear_chart_frame()

        # Gather spending data from all accounts
        category_totals = {}

        for account in self.accounts:
            account_data = self.db.get_spending_by_category(account.account_id)
            for row in account_data:
                category = row["category"]
                total = row["total"]
                if category in category_totals:
                    category_totals[category] += total
                else:
                    category_totals[category] = total

        if not category_totals:
            self.show_no_data_message(
                "No spending data available yet.\nMake some transactions to see your spending breakdown."
            )
            return

        # Create pie chart with dark theme
        fig = Figure(figsize=(10, 6), facecolor=COLORS["bg_dark"])
        ax = fig.add_subplot(111, facecolor=COLORS["bg_dark"])

        categories = list(category_totals.keys())
        amounts = list(category_totals.values())

        # Vibrant colors for dark theme
        colors_list = [
            "#00ff88",
            "#00d4ff",
            "#a855f7",
            "#ff6b35",
            "#ffd93d",
            "#ff4757",
            "#5f27cd",
            "#00d2d3",
            "#ff9ff3",
            "#48dbfb",
        ]

        wedges, texts, autotexts = ax.pie(
            amounts,
            labels=categories,
            autopct="%1.1f%%",
            startangle=90,
            colors=colors_list[: len(categories)],
        )

        # Improve text readability for dark theme
        for text in texts:
            text.set_fontsize(10)
            text.set_weight("bold")
            text.set_color(COLORS["text_primary"])

        for autotext in autotexts:
            autotext.set_color(COLORS["bg_dark"])
            autotext.set_fontsize(9)
            autotext.set_weight("bold")

        ax.set_title(
            "Spending by Category",
            fontsize=16,
            fontweight="bold",
            pad=20,
            color=COLORS["text_bright"],
        )
        ax.axis("equal")

        # Add total spending label
        total_spending = sum(amounts)
        fig.text(
            0.5,
            0.02,
            f"Total Spending: ${total_spending:.2f}",
            ha="center",
            fontsize=12,
            fontweight="bold",
        )

        self.embed_chart(fig)

    def show_balance_history(self):
        """Display balance trend over time."""
        self.clear_chart_frame()

        # Get transactions for the first account (or combine all)
        if not self.accounts:
            self.show_no_data_message("No accounts available.")
            return

        account = self.accounts[0]
        transactions = self.db.get_transactions(account.account_id, limit=100)

        if not transactions:
            self.show_no_data_message("No transaction history available yet.")
            return

        # Extract dates and balances
        dates = []
        balances = []

        for trans in reversed(transactions):  # Oldest first
            try:
                date = datetime.strptime(trans["timestamp"], "%Y-%m-%d %H:%M:%S")
                dates.append(date)
                balances.append(trans["balance_after"])
            except (ValueError, KeyError, TypeError):
                continue

        if not dates:
            self.show_no_data_message("Could not parse transaction dates.")
            return

        # Create line chart
        fig = Figure(figsize=(10, 6), facecolor=COLORS["white"])
        ax = fig.add_subplot(111)

        ax.plot(
            dates,
            balances,
            color=COLORS["accent"],
            linewidth=2,
            marker="o",
            markersize=4,
        )
        ax.fill_between(dates, balances, alpha=0.3, color=COLORS["accent"])

        ax.set_xlabel("Date", fontsize=12, fontweight="bold")
        ax.set_ylabel("Balance ($)", fontsize=12, fontweight="bold")
        ax.set_title(
            f"Balance History - {account.get_account_type()} ({account.account_number[-4:]})",
            fontsize=16,
            fontweight="bold",
            pad=20,
        )

        ax.grid(True, alpha=0.3, linestyle="--")
        fig.autofmt_xdate()  # Rotate date labels

        # Add current balance annotation
        if balances:
            current_balance = balances[-1]
            ax.axhline(
                y=current_balance, color="red", linestyle="--", alpha=0.5, linewidth=1
            )
            ax.text(
                0.02,
                0.98,
                f"Current: ${current_balance:.2f}",
                transform=ax.transAxes,
                fontsize=12,
                fontweight="bold",
                verticalalignment="top",
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
            )

        self.embed_chart(fig)

    def show_monthly_comparison(self):
        """Display monthly income vs expenses comparison."""
        self.clear_chart_frame()

        # Gather data from all accounts
        monthly_data = {}

        for account in self.accounts:
            transactions = self.db.get_transactions(account.account_id, limit=500)

            for trans in transactions:
                try:
                    date = datetime.strptime(trans["timestamp"], "%Y-%m-%d %H:%M:%S")
                    month_key = date.strftime("%Y-%m")

                    if month_key not in monthly_data:
                        monthly_data[month_key] = {"income": 0, "expenses": 0}

                    if trans["transaction_type"] in [
                        "Deposit",
                        "Transfer In",
                        "Payment",
                    ]:
                        monthly_data[month_key]["income"] += trans["amount"]
                    elif trans["transaction_type"] in [
                        "Withdrawal",
                        "Transfer Out",
                        "Credit Purchase",
                    ]:
                        monthly_data[month_key]["expenses"] += trans["amount"]
                except (ValueError, KeyError, TypeError):
                    continue

        if not monthly_data:
            self.show_no_data_message(
                "No transaction data available for monthly comparison."
            )
            return

        # Sort by month
        sorted_months = sorted(monthly_data.keys())
        months = [
            datetime.strptime(m, "%Y-%m").strftime("%b %Y") for m in sorted_months
        ]
        income = [monthly_data[m]["income"] for m in sorted_months]
        expenses = [monthly_data[m]["expenses"] for m in sorted_months]

        # Create bar chart
        fig = Figure(figsize=(10, 6), facecolor=COLORS["white"])
        ax = fig.add_subplot(111)

        x = range(len(months))
        width = 0.35

        bars1 = ax.bar(
            [i - width / 2 for i in x],
            income,
            width,
            label="Income",
            color=COLORS["accent"],
            alpha=0.8,
        )
        bars2 = ax.bar(
            [i + width / 2 for i in x],
            expenses,
            width,
            label="Expenses",
            color=COLORS["error"],
            alpha=0.8,
        )

        ax.set_xlabel("Month", fontsize=12, fontweight="bold")
        ax.set_ylabel("Amount ($)", fontsize=12, fontweight="bold")
        ax.set_title(
            "Monthly Income vs Expenses", fontsize=16, fontweight="bold", pad=20
        )
        ax.set_xticks(x)
        ax.set_xticklabels(months, rotation=45, ha="right")
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3, linestyle="--", axis="y")

        # Add value labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2.0,
                        height,
                        f"${height:.0f}",
                        ha="center",
                        va="bottom",
                        fontsize=8,
                    )

        fig.tight_layout()
        self.embed_chart(fig)

    def show_accounts_overview(self):
        """Display overview of all accounts."""
        self.clear_chart_frame()

        if not self.accounts:
            self.show_no_data_message("No accounts available.")
            return

        # Create overview chart with proper spacing
        fig = Figure(figsize=(10, 6), facecolor=COLORS["white"])
        ax = fig.add_subplot(111)

        account_names = []
        balances = []
        colors_list = []

        for account in self.accounts:
            name = f"{account.get_account_type()}\n{account.account_number[-4:]}"
            account_names.append(name)
            balances.append(abs(account.balance))

            # Color by account type
            if "Checking" in account.get_account_type():
                colors_list.append(COLORS["secondary"])
            elif "Savings" in account.get_account_type():
                colors_list.append(COLORS["accent"])
            else:
                colors_list.append(COLORS["warning"])

        bars = ax.bar(account_names, balances, color=colors_list, alpha=0.8)

        ax.set_ylabel("Balance ($)", fontsize=12, fontweight="bold")
        ax.set_title("All Accounts Overview", fontsize=16, fontweight="bold", pad=20)
        ax.grid(True, alpha=0.3, linestyle="--", axis="y")

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"${height:.2f}",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
            )

        # Adjust layout to prevent overlapping
        fig.subplots_adjust(bottom=0.15)

        # Add total balance with proper spacing
        total_balance = sum(balances)
        fig.text(
            0.5,
            0.03,
            f"Total Balance Across All Accounts: ${total_balance:.2f}",
            ha="center",
            fontsize=12,
            fontweight="bold",
        )

        self.embed_chart(fig)

    def show_no_data_message(self, message):
        """Display a message when no data is available."""
        label = tk.Label(
            self.chart_frame,
            text=message,
            font=FONTS["heading"],
            bg=COLORS["white"],
            fg=COLORS["text_secondary"],
            wraplength=600,
            justify=tk.CENTER,
        )
        label.pack(expand=True)

    def embed_chart(self, fig):
        """Embed a matplotlib figure into the tkinter window."""
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
