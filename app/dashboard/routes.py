from flask import Blueprint, render_template, jsonify, redirect, url_for, request, flash
from flask_login import login_required, current_user
from datetime import date, datetime
from sqlalchemy import func, extract
from app import db
from app.models import Expense, Income, CATEGORIES, PAYMENT_METHODS

dashboard_bp = Blueprint("dashboard", __name__)


def _summary(user_id):
    today = date.today()
    year, month = today.year, today.month

    total_expense = db.session.query(func.sum(Expense.amount)).filter_by(user_id=user_id).scalar() or 0
    total_income  = db.session.query(func.sum(Income.amount)).filter_by(user_id=user_id).scalar() or 0

    month_expense = (
        db.session.query(func.sum(Expense.amount))
        .filter(
            Expense.user_id == user_id,
            extract("year", Expense.date) == year,
            extract("month", Expense.date) == month,
        )
        .scalar() or 0
    )

    month_income = (
        db.session.query(func.sum(Income.amount))
        .filter(
            Income.user_id == user_id,
            extract("year", Income.date) == year,
            extract("month", Income.date) == month,
        )
        .scalar() or 0
    )

    # Category breakdown this month
    category_data = (
        db.session.query(Expense.category, func.sum(Expense.amount))
        .filter(
            Expense.user_id == user_id,
            extract("year", Expense.date) == year,
            extract("month", Expense.date) == month,
        )
        .group_by(Expense.category)
        .order_by(func.sum(Expense.amount).desc())
        .all()
    )

    # Monthly totals (last 6 months)
    monthly_expenses = (
        db.session.query(
            extract("year", Expense.date).label("yr"),
            extract("month", Expense.date).label("mo"),
            func.sum(Expense.amount).label("total"),
        )
        .filter(Expense.user_id == user_id)
        .group_by("yr", "mo")
        .order_by("yr", "mo")
        .limit(6)
        .all()
    )

    net_balance = round(float(total_income) - float(total_expense), 2)
    month_net   = round(float(month_income) - float(month_expense), 2)

    # Savings rate %
    if month_income > 0:
        savings_rate = round((month_net / float(month_income)) * 100, 1)
    else:
        savings_rate = 0.0

    budget_used_pct = 0
    if current_user.monthly_budget and current_user.monthly_budget > 0:
        budget_used_pct = min(round((float(month_expense) / current_user.monthly_budget) * 100, 1), 100)

    return {
        "total_expense":   round(float(total_expense), 2),
        "total_income":    round(float(total_income), 2),
        "month_expense":   round(float(month_expense), 2),
        "month_income":    round(float(month_income), 2),
        "net_balance":     net_balance,
        "month_net":       month_net,
        "savings_rate":    savings_rate,
        "budget_used_pct": budget_used_pct,
        "category_labels": [r[0] for r in category_data],
        "category_values": [round(float(r[1]), 2) for r in category_data],
        "monthly_exp_labels": [f"{int(r.yr)}-{int(r.mo):02d}" for r in monthly_expenses],
        "monthly_exp_values": [round(float(r.total), 2) for r in monthly_expenses],
        "has_data": total_expense > 0 or total_income > 0,
    }


@dashboard_bp.route("/", methods=["GET"])
def home():
    """Public landing page — redirects logged-in users straight to dashboard."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    return render_template("home.html")


@dashboard_bp.route("/dashboard", methods=["GET", "POST"])
@login_required
def index():
    today = date.today()

    if request.method == "POST":
        try:
            amount = float(request.form.get("amount", 0))
        except ValueError:
            flash("Invalid amount.", "danger")
            return redirect(url_for("dashboard.index"))

        if amount <= 0:
            flash("Amount must be greater than zero.", "danger")
            return redirect(url_for("dashboard.index"))

        date_str = request.form.get("date", today.strftime("%Y-%m-%d"))
        try:
            exp_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            exp_date = today

        action_type = request.form.get("action_type", "expense")
        description = request.form.get("description", "").strip() or "Transaction"

        if action_type == "income":
            income = Income(
                user_id=current_user.id,
                amount=amount,
                source=request.form.get("category", "Salary"),
                description=description,
                date=exp_date,
            )
            db.session.add(income)
            db.session.commit()
            flash(f"Income of {current_user.currency}{amount:.2f} added!", "success")
        else:
            expense = Expense(
                user_id=current_user.id,
                amount=amount,
                category=request.form.get("category", "Others"),
                description=description,
                date=exp_date,
                payment_method=request.form.get("payment_method", "Cash"),
            )
            db.session.add(expense)
            db.session.commit()
            flash(f"Expense of {current_user.currency}{amount:.2f} logged!", "success")

        return redirect(url_for("dashboard.index"))

    summary = _summary(current_user.id)

    # Recent expenses
    recent_expenses = (
        Expense.query.filter_by(user_id=current_user.id)
        .order_by(Expense.date.desc(), Expense.created_at.desc())
        .limit(6)
        .all()
    )

    # Top categories (for the holdings-style list)
    top_categories = (
        db.session.query(Expense.category, func.sum(Expense.amount).label("total"))
        .filter(
            Expense.user_id == current_user.id,
            extract("year", Expense.date) == today.year,
            extract("month", Expense.date) == today.month,
        )
        .group_by(Expense.category)
        .order_by(func.sum(Expense.amount).desc())
        .limit(5)
        .all()
    )

    # Prediction
    from app.ml.engine import predict_next_month
    rows = (
        db.session.query(
            extract("year", Expense.date).label("yr"),
            extract("month", Expense.date).label("mo"),
            func.sum(Expense.amount).label("total"),
        )
        .filter(Expense.user_id == current_user.id)
        .group_by("yr", "mo")
        .order_by("yr", "mo")
        .all()
    )
    monthly_totals = [float(r.total) for r in rows]
    prediction = predict_next_month(monthly_totals)

    return render_template(
        "dashboard/index.html",
        summary=summary,
        recent_expenses=recent_expenses,
        top_categories=top_categories,
        categories=CATEGORIES,
        payment_methods=PAYMENT_METHODS,
        today=today.strftime("%Y-%m-%d"),
        prediction=prediction,
    )
