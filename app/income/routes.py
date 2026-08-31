from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models import Income, INCOME_SOURCES

income_bp = Blueprint("income", __name__)


def _parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return datetime.utcnow().date()


@income_bp.route("/")
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    incomes = (
        Income.query.filter_by(user_id=current_user.id)
        .order_by(Income.date.desc(), Income.created_at.desc())
        .paginate(page=page, per_page=15, error_out=False)
    )
    return render_template("income/index.html", incomes=incomes, sources=INCOME_SOURCES)


@income_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        try:
            amount = float(request.form.get("amount", 0))
        except ValueError:
            flash("Invalid amount.", "danger")
            return render_template("income/add.html", sources=INCOME_SOURCES)

        if amount <= 0:
            flash("Amount must be greater than zero.", "danger")
            return render_template("income/add.html", sources=INCOME_SOURCES)

        income = Income(
            user_id=current_user.id,
            amount=amount,
            source=request.form.get("source", "Other"),
            description=request.form.get("description", "").strip(),
            date=_parse_date(request.form.get("date")),
        )
        db.session.add(income)
        db.session.commit()
        flash("Income added successfully!", "success")
        return redirect(url_for("income.index"))

    return render_template("income/add.html", sources=INCOME_SOURCES,
                           today=datetime.utcnow().date().strftime("%Y-%m-%d"))


@income_bp.route("/edit/<int:income_id>", methods=["GET", "POST"])
@login_required
def edit(income_id):
    income = Income.query.filter_by(id=income_id, user_id=current_user.id).first_or_404()

    if request.method == "POST":
        try:
            income.amount = float(request.form.get("amount", income.amount))
        except ValueError:
            flash("Invalid amount.", "danger")
            return render_template("income/edit.html", income=income, sources=INCOME_SOURCES)

        income.source = request.form.get("source", income.source)
        income.description = request.form.get("description", income.description or "").strip()
        income.date = _parse_date(request.form.get("date"))
        db.session.commit()
        flash("Income updated successfully!", "success")
        return redirect(url_for("income.index"))

    return render_template("income/edit.html", income=income, sources=INCOME_SOURCES)


@income_bp.route("/delete/<int:income_id>", methods=["POST"])
@login_required
def delete(income_id):
    income = Income.query.filter_by(id=income_id, user_id=current_user.id).first_or_404()
    db.session.delete(income)
    db.session.commit()
    flash("Income record deleted.", "info")
    return redirect(url_for("income.index"))
