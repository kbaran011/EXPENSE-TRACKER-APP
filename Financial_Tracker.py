import pandas as pd
from datetime import datetime
import os
import matplotlib.pyplot as plt
from fpdf import FPDF
import numpy as np
from sklearn.linear_model import LinearRegression

# File path for the CSV
csv_file = "expenses.csv"

# Check if the CSV file exists, and if it does, load the existing data
if os.path.exists(csv_file):
    expense_data = pd.read_csv(csv_file)
else:
    # If the file doesn't exist, create an empty DataFrame
    expense_data = pd.DataFrame(columns=["Date", "Category", "Amount"])

# File path for the budgets CSV
budget_file = "budgets.csv"

# Check if the budgets file exists and load it, or initialize an empty dictionary
if os.path.exists(budget_file):
    budgets = pd.read_csv(budget_file, index_col="Category").to_dict()["Budget"]
else:
    budgets = {}  # Empty dictionary to store budgets


# Function to forecast future expenses
def forecast_expenses(months_ahead=3):
    # Ensure there are expenses to forecast
    if expense_data.empty:
        print("\nNo expenses recorded yet to forecast.")
        return

    print("\n--- Expense Forecast ---")

    # Convert the 'Date' column to datetime format
    expense_data["Date"] = pd.to_datetime(expense_data["Date"])
    expense_data["Month"] = expense_data["Date"].dt.to_period("M")

    # Group by month and calculate total expenses
    monthly_totals = expense_data.groupby("Month")["Amount"].sum().reset_index()
    monthly_totals["Month"] = monthly_totals["Month"].astype(str)  # Convert period to string for regression

    # Prepare data for linear regression
    monthly_totals["Month_Index"] = np.arange(len(monthly_totals))  # Create a numeric index for months
    X = monthly_totals["Month_Index"].values.reshape(-1, 1)
    y = monthly_totals["Amount"].values

    # Fit a linear regression model
    model = LinearRegression()
    model.fit(X, y)

    # Predict future expenses
    future_months = np.arange(len(monthly_totals), len(monthly_totals) + months_ahead).reshape(-1, 1)
    future_expenses = model.predict(future_months)

    # Display predictions
    print(f"\nPredicted expenses for the next {months_ahead} months:")
    for i, expense in enumerate(future_expenses, 1):
        print(f"Month {i}: ${expense:.2f}")

    # Plot historical and forecasted data
    plt.figure(figsize=(10, 6))
    plt.plot(monthly_totals["Month_Index"], y, label="Historical Data", marker="o")
    plt.plot(future_months, future_expenses, label="Forecasted Data", linestyle="--", marker="o")
    plt.xlabel("Month Index")
    plt.ylabel("Total Expenses")
    plt.title("Expense Forecast")
    plt.legend()
    plt.tight_layout()
    plt.show()

def remove_category(category):
    global expense_data, budgets
    # Check if the category exists in the expense data
    if category not in expense_data["Category"].unique():
        print(f"\nCategory '{category}' does not exist.")
        return

    # Remove all rows belonging to the category
    expense_data = expense_data[expense_data["Category"] != category]
    print(f"\nCategory '{category}' and its expenses have been removed.")

    # Remove the budget for the category, if it exists
    if category in budgets:
        del budgets[category]
        # Save updated budgets to the CSV
        budget_df = pd.DataFrame(list(budgets.items()), columns=["Category", "Budget"])
        budget_df.to_csv(budget_file, index=False)
        print(f"Budget for '{category}' has also been removed.")

    # Save the updated expense data
    expense_data.to_csv(csv_file, index=False)

def subtract_from_category(category, amount):
    global expense_data

    # Check if the category exists in the expense data
    if category not in expense_data["Category"].unique():
        print(f"\nCategory '{category}' does not exist.")
        return

    # Add a negative expense to subtract the amount
    date = datetime.now().strftime("%Y-%m-%d")
    new_entry = pd.DataFrame({"Date": [date], "Category": [category], "Amount": [-amount]})
    expense_data = pd.concat([expense_data, new_entry], ignore_index=True)

    # Save the updated expense data
    expense_data.to_csv(csv_file, index=False)
    print(f"\n${amount:.2f} has been subtracted from the '{category}' category.")



# Function to generate a PDF report
def generate_pdf_report():
    # Check if there are expenses to report
    if expense_data.empty:
        print("\nNo expenses recorded yet to generate a report.")
        return

    print("\nGenerating PDF report...")

    # Create an FPDF instance
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Add a title page
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Expense Tracker Report", ln=True, align="C")
    pdf.ln(10)

    # Total expenses
    total_expenses = expense_data["Amount"].sum()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Total Expenses: ${total_expenses:.2f}", ln=True)

    # Category-wise totals
    pdf.ln(5)
    pdf.cell(0, 10, "Expenses by Category:", ln=True)
    category_totals = expense_data.groupby("Category")["Amount"].sum()
    for category, amount in category_totals.items():
        pdf.cell(0, 10, f"  - {category}: ${amount:.2f}", ln=True)

    # Highest spending category
    highest_category = category_totals.idxmax()
    highest_amount = category_totals.max()
    pdf.ln(5)
    pdf.cell(0, 10, f"Highest Spending Category: {highest_category} (${highest_amount:.2f})", ln=True)

    # Save the text portion of the report
    pdf.ln(10)

    # Add visualizations
    pdf.add_page()

    # Save the pie chart as an image
    plot_category_spending()
    plt.savefig("category_pie_chart.png")
    pdf.image("category_pie_chart.png", x=10, y=30, w=190)
    plt.close()

    # Save the bar chart as an image
    plot_monthly_expenses()
    plt.savefig("monthly_bar_chart.png")
    pdf.add_page()
    pdf.image("monthly_bar_chart.png", x=10, y=30, w=190)
    plt.close()

    # Save the PDF
    pdf.output("Expense_Report.pdf")
    print("PDF report generated: Expense_Report.pdf")


# Function to set a budget for a category
def set_budget(category, amount):
    global budgets
    budgets[category] = amount  # Add or update the budget for the category

    # Save budgets to a CSV file
    budget_df = pd.DataFrame(list(budgets.items()), columns=["Category", "Budget"])
    budget_df.to_csv(budget_file, index=False)
    print(f"Budget for '{category}' set to ${amount:.2f}.")


# Function to add an expense
def add_expense(date, category, amount):
    global expense_data
    new_entry = pd.DataFrame({"Date": [date], "Category": [category], "Amount": [amount]})
    expense_data = pd.concat([expense_data, new_entry], ignore_index=True)

    # Check if a budget exists for the category
    if category in budgets:
        total_spent = expense_data[expense_data["Category"] == category]["Amount"].sum()
        budget = budgets[category]

        # Alert the user if they exceed 80% or 100% of the budget
        if total_spent > budget:
            print(f"⚠️ WARNING: You have exceeded the budget for '{category}'! Budget: ${budget:.2f}, Spent: ${total_spent:.2f}")
        elif total_spent > 0.8 * budget:
            print(f"⚠️ ALERT: You are close to exceeding the budget for '{category}'. Budget: ${budget:.2f}, Spent: ${total_spent:.2f}")



# Function to analyze expenses
def analyze_expenses():
    print("\n--- Expense Analysis ---")

    if expense_data.empty:
        print("No expenses recorded yet.")
        return

    # Total expenses
    total_expenses = expense_data["Amount"].sum()
    print(f"Total Expenses: ${total_expenses:.2f}")

    # Category-wise totals
    category_totals = expense_data.groupby("Category")["Amount"].sum()
    print("\nExpenses by Category:")
    print(category_totals)

    # Find the highest spending category
    highest_category = category_totals.idxmax()
    highest_amount = category_totals.max()
    print(f"\nHighest Spending Category: {highest_category} (${highest_amount:.2f})")


# Function to visualize category-wise spending
def plot_category_spending():
    if expense_data.empty:
        print("\nNo expenses recorded yet to visualize.")
        return

    category_totals = expense_data.groupby("Category")["Amount"].sum()

    # Plot a pie chart
    plt.figure(figsize=(8, 6))
    plt.pie(category_totals, labels=category_totals.index, autopct="%1.1f%%", startangle=140)
    plt.title("Spending by Category")
    plt.show()


# Function to visualize monthly expenses
def plot_monthly_expenses():
    if expense_data.empty:
        print("\nNo expenses recorded yet to visualize.")
        return

    # Convert the 'Date' column to datetime format if it's not already
    expense_data["Date"] = pd.to_datetime(expense_data["Date"])

    # Extract the month and year
    expense_data["Month"] = expense_data["Date"].dt.to_period("M")

    # Group by month
    monthly_totals = expense_data.groupby("Month")["Amount"].sum()

    # Plot a bar chart
    plt.figure(figsize=(10, 6))
    monthly_totals.plot(kind="bar", color="skyblue")
    plt.title("Monthly Expenses")
    plt.xlabel("Month")
    plt.ylabel("Total Expenses")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


# Main program loop
while True:
    print("\n--- Menu ---")
    print("1. Add an Expense")
    print("2. View Expense Analysis")
    print("3. Visualize Spending by Category")
    print("4. Visualize Monthly Expenses")
    print("5. Set Budget for a Category")
    print("6. Generate PDF Report")
    print("7. Remove an Expense Category")
    print("8. Subtract an Amount from a Category")
    print("9. Forecast Future Expenses")
    print("10. Exit")
    choice = input("Enter your choice (1/2/3/4/5/6/7/8/9/10): ")

    if choice == "1":
        print("\n--- Add an Expense ---")
        date = input("Enter the date (YYYY-MM-DD): ")
        category = input("Enter the category (e.g., Food, Transport): ")
        amount = float(input("Enter the amount: "))

        # Add the expense to the DataFrame
        add_expense(date, category, amount)

        # Save the updated DataFrame to the CSV file
        expense_data.to_csv(csv_file, index=False)
        print("\nExpense added and saved to the file!")

    elif choice == "2":
        analyze_expenses()

    elif choice == "3":
        plot_category_spending()

    elif choice == "4":
        plot_monthly_expenses()

    elif choice == "5":
        print("\n--- Set a Budget ---")
        category = input("Enter the category (e.g., Food, Transport): ")
        amount = float(input("Enter the budget amount: "))

        # Set the budget
        set_budget(category, amount)

    elif choice == "6":
        generate_pdf_report()

    elif choice == "7":
        print("\n--- Remove an Expense Category ---")
        category = input("Enter the category to remove: ")

        # Remove the category
        remove_category(category)

    elif choice == "8":
        print("\n--- Subtract an Amount from a Category ---")
        category = input("Enter the category: ")
        amount = float(input("Enter the amount to subtract: "))

        # Subtract the amount
        subtract_from_category(category, amount)

    elif choice == "9":
        print("\n--- Forecast Future Expenses ---")
        months_ahead = int(input("Enter the number of months to forecast: "))

        # Forecast expenses
        forecast_expenses(months_ahead)

    elif choice == "10":
        print("\nExiting the program. Goodbye!")
        break

    else:
        print("\nInvalid choice. Please enter a valid option.")





print("\nAll expenses recorded:")
print(expense_data)
