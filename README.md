# Personal Expense Tracker — “Where is my money going?” 💸

Like a lot of people, I started wondering where all my money was actually going each month. Coffee? Rent? Uber? Random subscriptions I forgot about?

So I built this little project to answer that question — and to also practice some data analysis, SQL, and forecasting while I was at it. It turned into a surprisingly useful tool.

---

## 🌟 What it does (in plain English)

- I enter expenses (or import bank CSVs)
- The app categorizes them (some auto, some manual)
- It stores everything in a SQLite database
- I can analyze my spending in a browser
- It visualizes trends and categories
- I can set budgets and see how far off I am
- And finally it can **forecast future spending** based on my past months

It’s like a mini personal finance dashboard, but one I can customize and extend.

---

## 🏗 How it works under the hood (light version)

**Tech stack:**
- Python (Pandas, NumPy, Matplotlib)
- Streamlit (for the dashboard UI)
- SQLite (for storage)
- scikit-learn (LinearRegression for forecasting)
- FPDF (for automatic PDF reports)

There are two ways to use it:

1. **Streamlit Web App**  
   (interactive dashboard, charts, CSV import, budgets, forecasting)

2. **CLI Tool**  
   (console menus + PDF reporting + the same forecasting)

Both read/write to the same `expenses.db` database.

---

## 📊 Forecasting (no rocket science, but realistic)

I wanted the forecasting to feel more like an analyst would do it vs “just draw a line through points”, so I added:

- aggregation to monthly totals
- a train/test split (last 3 months held out)
- metrics:
  - Train R² (fit quality)
  - Test MAE (error on most recent months)

Then it predicts the next N months and shows a chart.

It’s intentionally simple, readable, and explainable — which matters in analytics roles more than just using overly fancy models.

---

## 🧩 Why I built it

Apart from wanting to know where my coffee money was going:

- I wanted a small portfolio project that uses **SQL**, **Python**, and **data analysis**
- I wanted it to have a **UI** instead of being only scripts
- I wanted it to be something I’d actually use again

And I do — especially the CSV import from bank statements.

---

## 🧪 How to run it

Clone and install:

```bash
git clone https://github.com/<your-username>/<repo>.git
cd <repo>
pip install -r requirements.txt
