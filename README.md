# Personal Expense Tracker

I built this project because I wanted to understand where my money was going each month and whether my spending patterns were consistent or all over the place. I was also looking for a small project that combines Python, SQL, data analysis, and some light forecasting. It turned out to be useful enough that I kept extending it.

The app has two interfaces: a Streamlit web app and a CLI tool. Both read and write to the same SQLite database. The idea was to make it easy to input data manually, import bank CSVs, analyze spending, visualize patterns, and forecast future expenses.

---

## What the app does

- Track expenses by date, category, and amount
- Store everything in a SQLite database (not CSVs)
- Import expenses from CSV files (e.g., bank statements)
- Apply basic auto-categorization rules for common transactions
- View summaries and breakdowns (e.g., totals by category)
- Add monthly budgets and compare them to actuals
- Visualize spending trends
- Forecast upcoming expenses based on historical data
- Generate PDF reports via the CLI version

It's intentionally simple, but not a toy script — it's something I actually use.

---

## Forecasting

The forecasting feature takes historical expenses, aggregates them by month, and fits a linear regression model using scikit-learn. To make it more realistic, I added a small train/test split instead of fitting on all data. The model reports:

- Train R² (fit quality)
- Test MAE on the last few months (error on hold-out period)

Then it forecasts the next N months and plots them against the historical data. The point isn't to predict the future perfectly, but to demonstrate analysis, evaluation, and a reasonable workflow for time-based data.

---

## Tech stack

- Python (Pandas, NumPy, Matplotlib)
- Streamlit (for the web dashboard)
- SQLite (for data storage)
- scikit-learn (for forecasting)
- FPDF (for generating PDF reports)

---

## How to run it

Clone the repository:
