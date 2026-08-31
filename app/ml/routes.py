from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import func, extract
from app import db
from app.models import Expense, Prediction
from app.ml.engine import (
    predict_category,
    predict_next_month,
    retrain_classifier_from_db,
    generate_budget_recommendation,
    train_regressor,
)

ml_bp = Blueprint("ml", __name__)


def _get_monthly_totals(user_id):
    rows = (
        db.session.query(
            extract("year", Expense.date).label("yr"),
            extract("month", Expense.date).label("mo"),
            func.sum(Expense.amount).label("total"),
        )
        .filter(Expense.user_id == user_id)
        .group_by("yr", "mo")
        .order_by("yr", "mo")
        .all()
    )
    return [float(r.total) for r in rows], [f"{int(r.yr)}-{int(r.mo):02d}" for r in rows]


@ml_bp.route("/")
@login_required
def index():
    monthly_totals, labels = _get_monthly_totals(current_user.id)

    # Train regressor with latest data
    train_regressor(monthly_totals)
    prediction = predict_next_month(monthly_totals)
    recommendation = generate_budget_recommendation(current_user.id)

    # Persist prediction
    from datetime import date
    next_month = _next_month_label()
    existing = Prediction.query.filter_by(
        user_id=current_user.id, prediction_month=next_month
    ).first()
    if not existing:
        p = Prediction(
            user_id=current_user.id,
            predicted_amount=prediction["predicted"],
            prediction_month=next_month,
            algorithm=prediction["method"],
        )
        db.session.add(p)
        db.session.commit()

    return render_template(
        "ml/index.html",
        prediction=prediction,
        recommendation=recommendation,
        monthly_totals=monthly_totals,
        labels=labels,
        next_month=next_month,
    )


@ml_bp.route("/predict-category", methods=["POST"])
@login_required
def api_predict_category():
    data = request.get_json(silent=True) or {}
    description = data.get("description", "").strip()
    if not description:
        return jsonify({"error": "description required"}), 400
    result = predict_category(description)
    return jsonify(result)


@ml_bp.route("/retrain", methods=["POST"])
@login_required
def retrain():
    result = retrain_classifier_from_db()
    return jsonify(result)


def _next_month_label():
    from datetime import date
    today = date.today()
    month = today.month % 12 + 1
    year  = today.year + (1 if today.month == 12 else 0)
    return f"{year}-{month:02d}"
