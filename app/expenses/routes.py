from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models import Expense, CATEGORIES, PAYMENT_METHODS

expenses_bp = Blueprint("expenses", __name__)


def _parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return datetime.utcnow().date()


@expenses_bp.route("/")
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    category_filter = request.args.get("category", "")
    month_filter = request.args.get("month", "")

    query = Expense.query.filter_by(user_id=current_user.id)

    if category_filter:
        query = query.filter_by(category=category_filter)
    if month_filter:
        try:
            year, month = month_filter.split("-")
            from sqlalchemy import extract
            query = query.filter(
                extract("year", Expense.date) == int(year),
                extract("month", Expense.date) == int(month),
            )
        except ValueError:
            pass

    expenses = query.order_by(Expense.date.desc(), Expense.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )

    return render_template(
        "expenses/index.html",
        expenses=expenses,
        categories=CATEGORIES,
        payment_methods=PAYMENT_METHODS,
        category_filter=category_filter,
        month_filter=month_filter,
    )


@expenses_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        try:
            amount = float(request.form.get("amount", 0))
        except ValueError:
            flash("Invalid amount.", "danger")
            return render_template("expenses/add.html", categories=CATEGORIES,
                                   payment_methods=PAYMENT_METHODS)

        if amount <= 0:
            flash("Amount must be greater than zero.", "danger")
            return render_template("expenses/add.html", categories=CATEGORIES,
                                   payment_methods=PAYMENT_METHODS)

        expense = Expense(
            user_id=current_user.id,
            amount=amount,
            category=request.form.get("category", "Others"),
            description=request.form.get("description", "").strip(),
            date=_parse_date(request.form.get("date")),
            payment_method=request.form.get("payment_method", "Cash"),
        )
        db.session.add(expense)
        db.session.commit()
        flash("Expense added successfully!", "success")
        return redirect(url_for("expenses.index"))

    return render_template("expenses/add.html", categories=CATEGORIES,
                           payment_methods=PAYMENT_METHODS,
                           today=datetime.utcnow().date().strftime("%Y-%m-%d"))


@expenses_bp.route("/edit/<int:expense_id>", methods=["GET", "POST"])
@login_required
def edit(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()

    if request.method == "POST":
        try:
            expense.amount = float(request.form.get("amount", expense.amount))
        except ValueError:
            flash("Invalid amount.", "danger")
            return render_template("expenses/edit.html", expense=expense,
                                   categories=CATEGORIES, payment_methods=PAYMENT_METHODS)

        expense.category = request.form.get("category", expense.category)
        expense.description = request.form.get("description", expense.description).strip()
        expense.date = _parse_date(request.form.get("date"))
        expense.payment_method = request.form.get("payment_method", expense.payment_method)

        db.session.commit()
        flash("Expense updated successfully!", "success")
        return redirect(url_for("expenses.index"))

    return render_template("expenses/edit.html", expense=expense,
                           categories=CATEGORIES, payment_methods=PAYMENT_METHODS)


@expenses_bp.route("/delete/<int:expense_id>", methods=["POST"])
@login_required
def delete(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    db.session.delete(expense)
    db.session.commit()
    flash("Expense deleted.", "info")
    return redirect(url_for("expenses.index"))


@expenses_bp.route("/api/list")
@login_required
def api_list():
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).limit(50).all()
    return jsonify([e.to_dict() for e in expenses])
