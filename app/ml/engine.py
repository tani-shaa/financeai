"""
ML Engine
=========
Provides:
  1. Expense category classification  (TF-IDF + Logistic Regression)
  2. Next-month spending prediction   (Random Forest Regressor)
  3. Budget recommendation analysis
"""

import os
import pickle
import logging
from collections import defaultdict
from datetime import date, datetime

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────
_BASE = os.path.dirname(__file__)
MODELS_DIR = os.path.join(_BASE, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

CLASSIFIER_PATH = os.path.join(MODELS_DIR, "category_classifier.pkl")
REGRESSOR_PATH  = os.path.join(MODELS_DIR, "spending_regressor.pkl")


# ─────────────────────────────────────────────────────────────────────────────
# 1.  Category Classifier
# ─────────────────────────────────────────────────────────────────────────────

def _build_classifier_pipeline():
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=5000, lowercase=True)),
        ("clf",   LogisticRegression(max_iter=1000, C=5.0)),
    ])


def train_classifier(descriptions: list, categories: list) -> dict:
    """Train and persist the category classifier. Returns accuracy metrics."""
    if len(descriptions) < 10:
        return {"status": "skipped", "reason": "not enough training data"}

    pipeline = _build_classifier_pipeline()

    if len(set(categories)) > 1 and len(descriptions) >= 20:
        X_train, X_test, y_train, y_test = train_test_split(
            descriptions, categories, test_size=0.2, random_state=42, stratify=categories
        )
        pipeline.fit(X_train, y_train)
        accuracy = accuracy_score(y_test, pipeline.predict(X_test))
    else:
        pipeline.fit(descriptions, categories)
        accuracy = 1.0

    with open(CLASSIFIER_PATH, "wb") as f:
        pickle.dump(pipeline, f)

    logger.info("Classifier trained – accuracy %.2f", accuracy)
    return {"status": "ok", "accuracy": round(accuracy, 4), "samples": len(descriptions)}


def _load_classifier():
    if not os.path.exists(CLASSIFIER_PATH):
        return None
    with open(CLASSIFIER_PATH, "rb") as f:
        return pickle.load(f)


def predict_category(description: str) -> dict:
    """Predict expense category from a text description."""
    pipeline = _load_classifier()
    if pipeline is None:
        return {"category": "Others", "confidence": 0.0, "trained": False}

    desc = description.strip().lower()
    proba = pipeline.predict_proba([desc])[0]
    predicted = pipeline.predict([desc])[0]
    confidence = float(max(proba))

    return {"category": predicted, "confidence": round(confidence, 4), "trained": True}


# ─────────────────────────────────────────────────────────────────────────────
# 2.  Spending Predictor
# ─────────────────────────────────────────────────────────────────────────────

def _build_features(monthly_totals: list[float]) -> np.ndarray:
    """
    Convert a sorted list of monthly totals into feature rows.
    Each row = [lag1, lag2, lag3, rolling_mean_3, rolling_mean_6, trend]
    Target = next value.
    """
    rows_X, rows_y = [], []
    n = len(monthly_totals)
    for i in range(6, n):
        lag1 = monthly_totals[i - 1]
        lag2 = monthly_totals[i - 2]
        lag3 = monthly_totals[i - 3]
        rm3  = np.mean(monthly_totals[i-3:i])
        rm6  = np.mean(monthly_totals[i-6:i])
        trend = monthly_totals[i-1] - monthly_totals[i-2]
        rows_X.append([lag1, lag2, lag3, rm3, rm6, trend])
        rows_y.append(monthly_totals[i])
    return np.array(rows_X), np.array(rows_y)


def train_regressor(monthly_totals: list[float]) -> dict:
    """Train and persist the spending regressor. Returns status."""
    if len(monthly_totals) < 7:
        return {"status": "skipped", "reason": "need at least 7 months of data"}

    X, y = _build_features(monthly_totals)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)

    with open(REGRESSOR_PATH, "wb") as f:
        pickle.dump(model, f)

    logger.info("Regressor trained on %d samples", len(X))
    return {"status": "ok", "training_samples": len(X)}


def _load_regressor():
    if not os.path.exists(REGRESSOR_PATH):
        return None
    with open(REGRESSOR_PATH, "rb") as f:
        return pickle.load(f)


def predict_next_month(monthly_totals: list[float]) -> dict:
    """Predict next month's spending. Falls back to weighted average if untrained."""
    if len(monthly_totals) == 0:
        return {"predicted": 0.0, "method": "no_data", "confidence": "low"}

    if len(monthly_totals) < 7:
        # Simple weighted average fallback
        weights = np.array(range(1, len(monthly_totals) + 1), dtype=float)
        predicted = float(np.average(monthly_totals, weights=weights))
        return {"predicted": round(predicted, 2), "method": "weighted_avg", "confidence": "medium"}

    model = _load_regressor()
    if model is None:
        result = train_regressor(monthly_totals)
        if result["status"] != "ok":
            weights = np.arange(1, len(monthly_totals) + 1, dtype=float)
            predicted = float(np.average(monthly_totals, weights=weights))
            return {"predicted": round(predicted, 2), "method": "weighted_avg", "confidence": "medium"}
        model = _load_regressor()

    n = monthly_totals
    lag1  = n[-1]
    lag2  = n[-2]
    lag3  = n[-3]
    rm3   = np.mean(n[-3:])
    rm6   = np.mean(n[-6:])
    trend = n[-1] - n[-2]
    features = np.array([[lag1, lag2, lag3, rm3, rm6, trend]])
    predicted = float(model.predict(features)[0])
    predicted = max(0, predicted)

    return {"predicted": round(predicted, 2), "method": "RandomForest", "confidence": "high"}


# ─────────────────────────────────────────────────────────────────────────────
# 3.  Budget Recommendation
# ─────────────────────────────────────────────────────────────────────────────

def generate_budget_recommendation(user_id: int) -> dict:
    """Analyse user data and return actionable budget recommendations."""
    from app.models import Expense, Income
    from app import db
    from sqlalchemy import func, extract

    today = date.today()

    # ── Monthly expense history ────────────────────────────────────────────
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

    if not rows:
        return {"status": "no_data"}

    monthly_totals = [float(r.total) for r in rows]
    avg_monthly = np.mean(monthly_totals)
    max_monthly = np.max(monthly_totals)

    # ── Category breakdown (all time) ─────────────────────────────────────
    cat_rows = (
        db.session.query(Expense.category, func.sum(Expense.amount))
        .filter(Expense.user_id == user_id)
        .group_by(Expense.category)
        .all()
    )
    cat_totals = {r[0]: float(r[1]) for r in cat_rows}
    total_spent = sum(cat_totals.values())
    top_category = max(cat_totals, key=cat_totals.get) if cat_totals else "N/A"
    top_cat_pct  = round(cat_totals.get(top_category, 0) / total_spent * 100, 1) if total_spent else 0

    # ── Income ────────────────────────────────────────────────────────────
    total_income = (
        db.session.query(func.sum(Income.amount))
        .filter(Income.user_id == user_id)
        .scalar() or 0
    )
    avg_monthly_income = total_income / max(len(rows), 1)

    # ── Prediction ────────────────────────────────────────────────────────
    prediction = predict_next_month(monthly_totals)

    # ── Recommended budget = 90 % of predicted or avg, whichever is lower
    safe_budget = round(min(avg_monthly * 0.9, prediction["predicted"] * 0.95), 2)
    expected_savings = round(avg_monthly_income - safe_budget, 2)

    # ── Tips ──────────────────────────────────────────────────────────────
    tips = []
    if top_cat_pct > 30:
        tips.append(f"'{top_category}' takes up {top_cat_pct}% of spending — consider setting a limit.")
    if prediction["predicted"] > avg_monthly * 1.1:
        tips.append("Next month's predicted spend is higher than your average — plan ahead.")
    if expected_savings < 0:
        tips.append("Your expenses may exceed income next month — review non-essential spending.")
    if len(monthly_totals) >= 2 and monthly_totals[-1] > monthly_totals[-2] * 1.2:
        tips.append("Your spending jumped significantly last month — identify what drove the increase.")
    if not tips:
        tips.append("You're on track! Keep monitoring your spending habits.")

    return {
        "status": "ok",
        "avg_monthly_expense": round(avg_monthly, 2),
        "max_monthly_expense": round(max_monthly, 2),
        "safe_budget": safe_budget,
        "expected_savings": expected_savings,
        "top_category": top_category,
        "top_category_pct": top_cat_pct,
        "predicted_next_month": prediction["predicted"],
        "prediction_method": prediction["method"],
        "tips": tips,
        "category_breakdown": cat_totals,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4.  Auto-train on app startup / rebuild call
# ─────────────────────────────────────────────────────────────────────────────

def retrain_classifier_from_db():
    """Pull all MLTrainingData + user-labelled expenses and retrain."""
    from app.models import MLTrainingData, Expense
    from app import db

    seed_rows = MLTrainingData.query.all()
    descs  = [r.description for r in seed_rows]
    cats   = [r.category    for r in seed_rows]

    # Enrich with user-confirmed expense descriptions
    user_rows = Expense.query.filter(Expense.description != "").all()
    for e in user_rows:
        descs.append(e.description.lower())
        cats.append(e.category)

    return train_classifier(descs, cats)
