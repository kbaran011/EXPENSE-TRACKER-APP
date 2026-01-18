def forecast_expenses(months_ahead: int = 3):
    expense_data = load_expenses()
    if expense_data.empty:
        print("\nNo expenses recorded yet to forecast.")
        return

    print("\n--- Expense Forecast ---")

    expense_data["Month"] = expense_data["Date"].dt.to_period("M")
    monthly_totals = (
        expense_data.groupby("Month")["Amount"].sum().reset_index()
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

    future_indices = np.arange(len(monthly_totals), len(monthly_totals) + months_ahead).reshape(-1, 1)
    future_expenses = model.predict(future_indices)

    print(f"Train R²: {train_r2:.3f}")
    if test_mae is not None:
        print(f"Test MAE (last {len(X_test)} months): ${test_mae:,.2f}")

    print(f"\nPredicted expenses for the next {months_ahead} months:")
    for i, expense in enumerate(future_expenses, 1):
        print(f"Month {i}: ${expense:.2f}")

    plt.figure(figsize=(10, 6))
    plt.plot(monthly_totals["Month_Index"], y, label="Historical", marker="o")
    plt.plot(future_indices.flatten(), future_expenses, label="Forecast", linestyle="--", marker="o")
    plt.xlabel("Month Index")
    plt.ylabel("Total Expenses")
    plt.title("Expense Forecast")
    plt.legend()
    plt.tight_layout()
    plt.show()
