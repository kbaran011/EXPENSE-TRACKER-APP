import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression
import os

# File paths
csv_file = "expenses.csv"
budget_file = "budgets.csv"

# Load expenses data
if os.path.exists(csv_file):
    expense_data = pd.read_csv(csv_file)
else:
    expense_data = pd.DataFrame(columns=["Date", "Category", "Amount"])

# Load budgets
if os.path.exists(budget_file):
    budgets = pd.read_csv(budget_file, index_col="Category").to_dict()["Budget"]
else:
    budgets = {}

# Helper function to save expenses
def save_expenses():
    expense_data.to_csv(csv_file, index=False)

# Helper function to save budgets
def save_budgets():
    budget_df = pd.DataFrame(list(budgets.items()), columns=["Category", "Budget"])
    budget_df.to_csv(budget_file, index=False)

# Streamlit app
st.title("Personal Expense Tracker with Financial Insights")

# Navigation
menu = st.sidebar.selectbox("Menu", ["Add Expense", "View Analysis", "Visualize Data", "Set Budget", "Forecast Expenses"])

# 1. Add Expense
if menu == "Add Expense":
    st.header("Add an Expense")
    date = st.date_input("Date")
    category = st.text_input("Category")
    amount = st.number_input("Amount", min_value=0.0, step=0.01)

    if st.button("Add Expense"):
        # Add expense to DataFrame
        new_expense = {"Date": date, "Category": category, "Amount": amount}
        expense_data.loc[len(expense_data)] = new_expense
        save_expenses()
        st.success("Expense added successfully!")

# 2. View Analysis
elif menu == "View Analysis":
    st.header("Expense Analysis")
    if expense_data.empty:
        st.write("No expenses recorded yet.")
    else:
        total_expenses = expense_data["Amount"].sum()
        st.write(f"Total Expenses: ${total_expenses:.2f}")

        category_totals = expense_data.groupby("Category")["Amount"].sum()
        st.write("Expenses by Category:")
        st.table(category_totals)

        highest_category = category_totals.idxmax()
        highest_amount = category_totals.max()
        st.write(f"Highest Spending Category: {highest_category} (${highest_amount:.2f})")

# 3. Visualize Data
elif menu == "Visualize Data":
    st.header("Visualize Data")
    if expense_data.empty:
        st.write("No expenses recorded yet.")
    else:
        category_totals = expense_data.groupby("Category")["Amount"].sum()

        # Pie chart
        st.subheader("Spending by Category")
        fig1, ax1 = plt.subplots()
        ax1.pie(category_totals, labels=category_totals.index, autopct="%1.1f%%", startangle=140)
        ax1.axis("equal")
        st.pyplot(fig1)

        # Bar chart
        st.subheader("Monthly Expenses")
        expense_data["Date"] = pd.to_datetime(expense_data["Date"])
        expense_data["Month"] = expense_data["Date"].dt.to_period("M")
        monthly_totals = expense_data.groupby("Month")["Amount"].sum()

        fig2, ax2 = plt.subplots()
        monthly_totals.plot(kind="bar", ax=ax2, color="skyblue")
        ax2.set_title("Monthly Expenses")
        ax2.set_xlabel("Month")
        ax2.set_ylabel("Total Expenses")
        st.pyplot(fig2)

# 4. Set Budget
elif menu == "Set Budget":
    st.header("Set Budget")
    category = st.text_input("Category")
    budget = st.number_input("Budget Amount", min_value=0.0, step=0.01)

    if st.button("Set Budget"):
        budgets[category] = budget
        save_budgets()
        st.success(f"Budget for {category} set to ${budget:.2f}.")

    st.write("Current Budgets:")
    st.table(pd.DataFrame(list(budgets.items()), columns=["Category", "Budget"]))

# 5. Forecast Expenses
elif menu == "Forecast Expenses":
    st.header("Forecast Future Expenses")
    months_ahead = st.slider("Months to Forecast", 1, 12, 3)

    if st.button("Forecast"):
        if expense_data.empty:
            st.write("No expenses recorded yet.")
        else:
            # Prepare data for regression
            expense_data["Date"] = pd.to_datetime(expense_data["Date"])
            expense_data["Month"] = expense_data["Date"].dt.to_period("M")
            monthly_totals = expense_data.groupby("Month")["Amount"].sum().reset_index()
            monthly_totals["Month_Index"] = np.arange(len(monthly_totals))
            X = monthly_totals["Month_Index"].values.reshape(-1, 1)
            y = monthly_totals["Amount"].values

            # Fit regression model
            model = LinearRegression()
            model.fit(X, y)

            # Predict future expenses
            future_months = np.arange(len(monthly_totals), len(monthly_totals) + months_ahead).reshape(-1, 1)
            future_expenses = model.predict(future_months)

            # Display forecast
            st.write("Forecasted Expenses:")
            forecast_df = pd.DataFrame({
                "Month": [f"Month {i+1}" for i in range(months_ahead)],
                "Predicted Expense": future_expenses
            })
            st.table(forecast_df)

            # Plot forecast
            fig, ax = plt.subplots()
            ax.plot(monthly_totals["Month_Index"], y, label="Historical Data", marker="o")
            ax.plot(range(len(monthly_totals), len(monthly_totals) + months_ahead), future_expenses, label="Forecast", linestyle="--", marker="o")
            ax.set_title("Expense Forecast")
            ax.set_xlabel("Month Index")
            ax.set_ylabel("Total Expenses")
            ax.legend()
            st.pyplot(fig)

