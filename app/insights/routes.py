from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, extract
from datetime import date
from app import db
from app.models import Expense, Income

insights_bp = Blueprint("insights", __name__)


def _month_label(year, month):
    return f"{int(year)}-{int(month):02d}"


def _generate_insights(user_id):
    today = date.today()
    cur_year, cur_month = today.year, today.month

    prev_month = cur_month - 1 if cur_month > 1 else 12
    prev_year  = cur_year if cur_month > 1 else cur_year - 1

    def month_expenses(year, month):
        return (
            db.session.query(func.sum(Expense.amount))
            .filter(
                Expense.user_id == user_id,
                extract("year", Expense.date) == year,
                extract("month", Expense.date) == month,
            )
            .scalar() or 0
        )

    def month_income(year, month):
        return (
            db.session.query(func.sum(Income.amount))
            .filter(
                Income.user_id == user_id,
                extract("year", Income.date) == year,
                extract("month", Income.date) == month,
            )
            .scalar() or 0
        )

    def cat_total(year, month):
        rows = (
            db.session.query(Expense.category, func.sum(Expense.amount))
            .filter(
                Expense.user_id == user_id,
                extract("year", Expense.date) == year,
                extract("month", Expense.date) == month,
            )
            .group_by(Expense.category)
            .all()
        )
        return {r[0]: float(r[1]) for r in rows}

    cur_exp   = float(month_expenses(cur_year, cur_month))
    prev_exp  = float(month_expenses(prev_year, prev_month))
    cur_inc   = float(month_income(cur_year, cur_month))
    cur_cats  = cat_total(cur_year, cur_month)
    prev_cats = cat_total(prev_year, prev_month)

    insights = []

    # ── Insight 1: Overall spending change ────────────────────────────────
    if prev_exp > 0:
        pct_change = (cur_exp - prev_exp) / prev_exp * 100
        direction  = "more" if pct_change > 0 else "less"
        if abs(pct_change) > 5:
            insights.append({
                "icon": "trending_up" if pct_change > 0 else "trending_down",
                "type": "warning" if pct_change > 0 else "success",
                "text": f"You spent {abs(pct_change):.1f}% {direction} this month compared to last month.",
            })

    # ── Insight 2: Per-category changes ───────────────────────────────────
    for cat, cur_val in cur_cats.items():
        prev_val = prev_cats.get(cat, 0)
        if prev_val > 0:
            pct = (cur_val - prev_val) / prev_val * 100
            if pct > 15:
                insights.append({
                    "icon": "arrow_upward",
                    "type": "warning",
                    "text": f"{cat} expenses increased by {pct:.1f}% compared to last month.",
                })
            elif pct < -15:
                insights.append({
                    "icon": "arrow_downward",
                    "type": "success",
                    "text": f"{cat} spending decreased by {abs(pct):.1f}% — great discipline!",
                })

    # ── Insight 3: Top spending category ──────────────────────────────────
    if cur_cats:
        top_cat = max(cur_cats, key=cur_cats.get)
        top_pct = cur_cats[top_cat] / cur_exp * 100 if cur_exp else 0
        insights.append({
            "icon": "pie_chart",
            "type": "info",
            "text": f"'{top_cat}' is your biggest spending category this month ({top_pct:.1f}% of expenses).",
        })

    # ── Insight 4: Savings rate ────────────────────────────────────────────
    if cur_inc > 0:
        savings_rate = (cur_inc - cur_exp) / cur_inc * 100
        if savings_rate >= 20:
            insights.append({
                "icon": "savings",
                "type": "success",
                "text": f"Excellent! You're saving {savings_rate:.1f}% of your income this month.",
            })
        elif savings_rate > 0:
            insights.append({
                "icon": "account_balance_wallet",
                "type": "info",
                "text": f"You're saving {savings_rate:.1f}% of income. Aim for 20%+ for financial health.",
            })
        else:
            insights.append({
                "icon": "warning",
                "type": "danger",
                "text": "Your expenses exceed your income this month. Review your spending urgently.",
            })

    # ── Insight 5: Budget check ────────────────────────────────────────────
    from flask_login import current_user
    if current_user.monthly_budget > 0:
        remaining = current_user.monthly_budget - cur_exp
        if remaining < 0:
            insights.append({
                "icon": "error",
                "type": "danger",
                "text": f"You have exceeded your monthly budget by {abs(remaining):.2f} {current_user.currency}.",
            })
        elif remaining / current_user.monthly_budget < 0.1:
            insights.append({
                "icon": "warning",
                "type": "warning",
                "text": f"Only {remaining:.2f} {current_user.currency} left in your monthly budget.",
            })

    # ── Insight 6: All-time savings ────────────────────────────────────────
    all_exp = db.session.query(func.sum(Expense.amount)).filter_by(user_id=user_id).scalar() or 0
    all_inc = db.session.query(func.sum(Income.amount)).filter_by(user_id=user_id).scalar() or 0
    net_savings = all_inc - all_exp
    if net_savings > 0:
        insights.append({
            "icon": "emoji_events",
            "type": "success",
            "text": f"Your total net savings are {net_savings:.2f} {current_user.currency}. Keep it up!",
        })

    if not insights:
        insights.append({
            "icon": "info",
            "type": "info",
            "text": "Add more transactions to unlock personalised insights.",
        })

    return insights


@insights_bp.route("/")
@login_required
def index():
    insights = _generate_insights(current_user.id)
    return render_template("insights/index.html", insights=insights)


@insights_bp.route("/api")
@login_required
def api():
    insights = _generate_insights(current_user.id)
    return jsonify(insights)
