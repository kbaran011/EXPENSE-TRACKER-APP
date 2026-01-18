import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression
import sqlite3
from datetime import datetime, date

DB_FILE = "expenses.db"


# ---------- Database helpers ----------

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Expenses table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            source TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        """
    )

    # Budgets table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL UNIQUE,
            monthly_budget REAL NOT NULL
        );
        """
    )

    conn.commit()
    conn.close()


def load_expenses() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT date AS Date, category AS Category, amount AS Amount FROM expenses ORDER BY date;",
        conn,
    )
    conn.close()
    if not df.empty:
        df["Date"] = pd.to_datetime(df["Date"])
    return df


def load_budgets() -> dict:
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT category AS Category, monthly_budget AS Budget FROM budgets ORDER BY category;",
        conn,
    )
    conn.close()
    if df.empty:
        return {}
    return dict(zip(df["Category"], df["Budget"]))


def set_budget(category: str, amount: float):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO budgets (category, monthly_budget)
        VALUES (?, ?)
        ON CONFLICT(category) DO UPDATE SET monthly_budget = excluded.monthly_budget;
        """,
        (category, float(amount)),
    )
    conn.commit()
    conn.close()


def add_expense(date_value, category: str, amount: float, source: str = "manual"):
    conn = get_connection()
    cur = conn.cursor()
    if isinstance(date_value, (datetime, date)):
        date_str = date_value.strftime("%Y-%m-%d")
    else:
        date_str = str(date_value)
    cur.execute(
        "INSERT INTO expenses (date, category, amount, source) VALUES (?, ?, ?, ?);",
        (date_str, category, float(amount), source),
    )
    conn.commit()
    conn.close()


def get_budget_vs_actual(expense_df: pd.DataFrame, budgets: dict) -> pd.DataFrame:
    if expense_df.empty or not budgets:
        return pd.DataFrame(
            columns=["Category", "Actual", "Budget", "Variance", "Variance_%"]
        )

    cat_totals = (
        expense_df.groupby("Category")["Amount"]
        .sum()
        .reset_index()
        .rename(columns={"Amount": "Actual"})
    )
    cat_totals["Budget"] = cat_totals["Category"].map(budgets).fillna(0.0)
    cat_totals["Variance"] = cat_totals["Actual"] - cat_totals["Budget"]
    cat_totals["Variance_%"] = np.where(
        cat_totals["Budget"] > 0,
        cat_totals["Variance"] / cat_totals["Budget"],
        np.nan,
    )
    return cat_totals


def auto_category(description: str) -> str:
    if not isinstance(description, str):
        return "Uncategorized"

    desc = description.upper()
    if "UBER" in desc or "LYFT" in desc or "TAXI" in desc:
        return "Transport"
    if "STARBUCKS" in desc or "COFFEE" in desc:
        return "Coffee"
    if "WALMART" in desc or "GROCERY" in desc or "SUPERMARKET" in desc:
        return "Groceries"
    if "RENT" in desc:
        return "Rent"
    if "NETFLIX" in desc or "SPOTIFY" in desc or "SUBSCRIPTION" in desc:
        return "Subscriptions"
    if "GYM" in desc or "FITNESS" in desc:
        return "Fitness"
    return "Uncategorized"


# ---------- Streamlit app ----------

init_db()

st.title("Personal Expense Tracker with Financial Insights")

menu = st.sidebar.selectbox(
    "Menu",
    [
        "Add Expense",
        "View Analysis",
        "Budget vs Actual",
        "Visualize Data",
        "Set Budget",
        "Forecast Expenses",
        "Import CSV Data",
    ],
)

# Always load fresh snapshots from the DB for this run
expense_data = load_expenses()
budgets = load_budgets()


# 1. Add Expense
if menu == "Add Expense":
    st.header("Add an Expense")
    date_input = st.date_input("Date")
    category_input = st.text_input("Category")
    amount_input = st.number_input("Amount", min_value=0.0, step=0.01)

    if st.button("Add Expense"):
        if not category_input:
            st.error("Please enter a category.")
        elif amount_input <= 0:
            st.error("Amount must be greater than 0.")
        else:
            add_expense(date_input, category_input, amount_input, source="manual")
            st.success("Expense added successfully! Please rerun or change page to refresh views.")


# 2. View Analysis
elif menu == "View Analysis":
    st.header("Expense Analysis")

    if expense_data.empty:
        st.write("No expenses recorded yet.")
    else:
        total_expenses = expense_data["Amount"].sum()
        st.metric("Total Expenses", f"${total_expenses:,.2f}")

        st.subheader("Raw Expense Table")
        st.dataframe(expense_data.sort_values("Date", ascending=False))

        category_totals = (
            expense_data.groupby("Category")["Amount"].sum().sort_values(ascending=False)
        )
        st.subheader("Expenses by Category")
        st.table(category_totals)

        highest_category = category_totals.idxmax()
        highest_amount = category_totals.max()
        st.write(
            f"**Highest Spending Category:** {highest_category} (${highest_amount:,.2f})"
        )

        # Rolling metrics
        expense_data_sorted = expense_data.sort_values("Date")
        expense_data_sorted["Month"] = expense_data_sorted["Date"].dt.to_period("M")
        monthly_totals = (
            expense_data_sorted.groupby("Month")["Amount"].sum().reset_index()
        )
        monthly_totals["Month"] = monthly_totals["Month"].dt.to_timestamp()
        monthly_totals["Rolling_3M"] = (
            monthly_totals["Amount"].rolling(window=3).mean()
        )

        st.subheader("Monthly Totals and 3-Month Rolling Average")
        fig, ax = plt.subplots()
        ax.plot(
            monthly_totals["Month"],
            monthly_totals["Amount"],
            marker="o",
            label="Monthly Total",
        )
        ax.plot(
            monthly_totals["Month"],
            monthly_totals["Rolling_3M"],
            marker="o",
            linestyle="--",
            label="3-Month Rolling Avg",
        )
        ax.set_xlabel("Month")
        ax.set_ylabel("Amount")
        ax.set_title("Monthly Expenses & Rolling Average")
        ax.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)


# 3. Budget vs Actual
elif menu == "Budget vs Actual":
    st.header("Budget vs Actual Analysis")

    if expense_data.empty:
        st.write("No expenses recorded yet.")
    elif not budgets:
        st.write("No budgets set yet. Go to 'Set Budget' to add some.")
    else:
        variance_df = get_budget_vs_actual(expense_data, budgets)
        st.subheader("Budget vs Actual by Category")
        st.dataframe(
            variance_df.style.format(
                {
                    "Actual": "{:,.2f}",
                    "Budget": "{:,.2f}",
                    "Variance": "{:,.2f}",
                    "Variance_%": "{:.1%}",
                }
            )
        )

        # Simple bar chart of variance
        st.subheader("Variance by Category")
        fig, ax = plt.subplots()
        ax.bar(variance_df["Category"], variance_df["Variance"])
        ax.set_xlabel("Category")
        ax.set_ylabel("Variance (Actual - Budget)")
        ax.set_title("Budget Variance by Category")
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)


# 4. Visualize Data
elif menu == "Visualize Data":
    st.header("Visualize Data")

    if expense_data.empty:
        st.write("No expenses recorded yet.")
    else:
        # Category totals
        category_totals = (
            expense_data.groupby("Category")["Amount"].sum().sort_values(ascending=False)
        )

        st.subheader("Spending by Category")
        fig1, ax1 = plt.subplots()
        ax1.pie(
            category_totals,
            labels=category_totals.index,
            autopct="%1.1f%%",
            startangle=140,
        )
        ax1.axis("equal")
        st.pyplot(fig1)

        # Monthly bar chart
        st.subheader("Monthly Expenses")
        expense_data["Month"] = expense_data["Date"].dt.to_period("M")
        monthly_totals = (
            expense_data.groupby("Month")["Amount"].sum().reset_index()
        )
        monthly_totals["Month"] = monthly_totals["Month"].dt.to_timestamp()

        fig2, ax2 = plt.subplots()
        ax2.bar(monthly_totals["Month"], monthly_totals["Amount"])
        ax2.set_title("Monthly Expenses")
        ax2.set_xlabel("Month")
        ax2.set_ylabel("Total Expenses")
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig2)


# 5. Set Budget
elif menu == "Set Budget":
    st.header("Set Budget")

    category = st.text_input("Category")
    budget = st.number_input("Monthly Budget Amount", min_value=0.0, step=0.01)

    if st.button("Save Budget"):
        if not category:
            st.error("Please enter a category.")
        elif budget <= 0:
            st.error("Budget must be greater than 0.")
        else:
            set_budget(category, budget)
            st.success(f"Budget for {category} set to ${budget:,.2f}.")

    st.subheader("Current Budgets")
    if budgets:
        budget_df = pd.DataFrame(
            list(budgets.items()), columns=["Category", "Monthly Budget"]
        )
        st.table(budget_df)
    else:
        st.write("No budgets defined yet.")


# 6. Forecast Expenses
elif menu == "Forecast Expenses":
    st.header("Forecast Future Expenses")

    months_ahead = st.slider("Months to Forecast", 1, 12, 3)

    if st.button("Run Forecast"):
        if expense_data.empty:
            st.write("No expenses recorded yet.")
        else:
            df = expense_data.copy()
            df["Month"] = df["Date"].dt.to_period("M")
            monthly_totals = (
                df.groupby("Month")["Amount"].sum().reset_index()
            )
            monthly_totals["Month"] = monthly_totals["Month"].dt.to_timestamp()
            monthly_totals["Month_Index"] = np.arange(len(monthly_totals))

            X = monthly_totals[["Month_Index"]].values
            y = monthly_totals["Amount"].values

            if len(monthly_totals) < 4:
                # Too few points for meaningful train/test split, fall back to simple fit
                model = LinearRegression()
                model.fit(X, y)
                train_r2 = model.score(X, y)
                test_mae = None
            else:
                # Use all but last 3 months for training, last up to 3 months as test
                split_idx = max(1, len(monthly_totals) - 3)
                X_train, X_test = X[:split_idx], X[split_idx:]
                y_train, y_test = y[:split_idx], y[split_idx:]

                model = LinearRegression()
                model.fit(X_train, y_train)
                train_r2 = model.score(X_train, y_train)

                if len(X_test) > 0:
                    y_pred_test = model.predict(X_test)
                    test_mae = np.mean(np.abs(y_test - y_pred_test))
                else:
                    test_mae = None

            future_indices = np.arange(
                len(monthly_totals), len(monthly_totals) + months_ahead
            ).reshape(-1, 1)
            future_expenses = model.predict(future_indices)

            st.subheader("Model Performance")
            st.write(f"Train R²: **{train_r2:.3f}**")
            if test_mae is not None:
                st.write(f"Test MAE (last {len(X_test)} months): **${test_mae:,.2f}**")

            forecast_df = pd.DataFrame(
                {
                    "Month_Index": future_indices.flatten(),
                    "Predicted Expense": future_expenses,
                }
            )
            st.subheader("Forecasted Expenses (Next Months)")
            st.table(forecast_df[["Month_Index", "Predicted Expense"]])

            # Plot historical + forecast
            fig, ax = plt.subplots()
            ax.plot(
                monthly_totals["Month_Index"],
                monthly_totals["Amount"],
                marker="o",
                label="Historical",
            )
            ax.plot(
                forecast_df["Month_Index"],
                forecast_df["Predicted Expense"],
                marker="o",
                linestyle="--",
                label="Forecast",
            )
            ax.set_title("Expense Forecast")
            ax.set_xlabel("Month Index")
            ax.set_ylabel("Total Expenses")
            ax.legend()
            plt.tight_layout()
            st.pyplot(fig)


# 7. Import CSV Data
elif menu == "Import CSV Data":
    st.header("Import Bank Statement CSV")

    uploaded = st.file_uploader("Upload CSV file", type=["csv"])
    if uploaded is not None:
        df_raw = pd.read_csv(uploaded)
        st.write("Preview of uploaded data:")
        st.dataframe(df_raw.head())

        columns = list(df_raw.columns)
        date_col = st.selectbox("Select Date column", columns)
        amount_col = st.selectbox("Select Amount column", columns)
        desc_col = st.selectbox(
            "Select Description column (optional)", ["(none)"] + columns
        )

        if st.button("Import Rows"):
            imported_count = 0
            for _, row in df_raw.iterrows():
                try:
                    dt_val = pd.to_datetime(row[date_col]).date()
                    amt_val = float(row[amount_col])
                    if desc_col != "(none)":
                        cat_val = auto_category(row[desc_col])
                    else:
                        cat_val = "Uncategorized"

                    if amt_val != 0:
                        add_expense(dt_val, cat_val, amt_val, source="import")
                        imported_count += 1
                except Exception:
                    # Skip problematic rows
                    continue

            st.success(f"Imported {imported_count} rows into the database.")
            st.info("Change page or rerun the app to see updated views.")
