from datetime import datetime
from flask_login import UserMixin
from app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ─────────────────────────────────────────────────────────────────────────────
# User
# ─────────────────────────────────────────────────────────────────────────────
class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(120), nullable=True)
    currency = db.Column(db.String(10), default="$")
    monthly_budget = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    expenses = db.relationship("Expense", backref="user", lazy=True, cascade="all,delete")
    incomes = db.relationship("Income", backref="user", lazy=True, cascade="all,delete")
    predictions = db.relationship("Prediction", backref="user", lazy=True, cascade="all,delete")

    def __repr__(self):
        return f"<User {self.username}>"


# ─────────────────────────────────────────────────────────────────────────────
# Expense
# ─────────────────────────────────────────────────────────────────────────────
CATEGORIES = [
    "Food", "Transport", "Shopping", "Bills",
    "Entertainment", "Healthcare", "Education", "Travel", "Others",
]

PAYMENT_METHODS = ["Cash", "Credit Card", "Debit Card", "UPI", "Bank Transfer", "Other"]


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    payment_method = db.Column(db.String(50), default="Cash")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "amount": self.amount,
            "category": self.category,
            "description": self.description,
            "date": self.date.strftime("%Y-%m-%d"),
            "payment_method": self.payment_method,
        }

    def __repr__(self):
        return f"<Expense {self.description} ${self.amount}>"


# ─────────────────────────────────────────────────────────────────────────────
# Income
# ─────────────────────────────────────────────────────────────────────────────
INCOME_SOURCES = ["Salary", "Freelance", "Business", "Investment", "Rental", "Other"]


class Income(db.Model):
    __tablename__ = "income"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "amount": self.amount,
            "source": self.source,
            "description": self.description,
            "date": self.date.strftime("%Y-%m-%d"),
        }

    def __repr__(self):
        return f"<Income {self.source} ${self.amount}>"


# ─────────────────────────────────────────────────────────────────────────────
# Prediction
# ─────────────────────────────────────────────────────────────────────────────
class Prediction(db.Model):
    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    predicted_amount = db.Column(db.Float, nullable=False)
    prediction_month = db.Column(db.String(20), nullable=False)   # "YYYY-MM"
    algorithm = db.Column(db.String(50), default="RandomForest")
    confidence = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Prediction {self.prediction_month} ${self.predicted_amount}>"


# ─────────────────────────────────────────────────────────────────────────────
# ML Training Data
# ─────────────────────────────────────────────────────────────────────────────
class MLTrainingData(db.Model):
    __tablename__ = "ml_training_data"

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(300), nullable=False)
    category = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"<MLTrainingData {self.description[:30]}>"
