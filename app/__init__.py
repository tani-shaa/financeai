from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from config import config

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()

login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"


def create_app(config_name="default"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialise extensions
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    # Register blueprints
    from app.auth.routes import auth_bp
    from app.dashboard.routes import dashboard_bp
    from app.expenses.routes import expenses_bp
    from app.income.routes import income_bp
    from app.ml.routes import ml_bp
    from app.insights.routes import insights_bp
    from app.chat.routes import chat_bp

    app.register_blueprint(auth_bp,      url_prefix="/auth")
    app.register_blueprint(dashboard_bp, url_prefix="/")
    app.register_blueprint(expenses_bp,  url_prefix="/expenses")
    app.register_blueprint(income_bp,    url_prefix="/income")
    app.register_blueprint(ml_bp,        url_prefix="/ml")
    app.register_blueprint(insights_bp,  url_prefix="/insights")
    app.register_blueprint(chat_bp,      url_prefix="/chat")

    # Create tables & seed ML training data
    with app.app_context():
        db.create_all()
        _seed_ml_training_data()

    return app


def _seed_ml_training_data():
    """Ensure the ML training table has seed rows on first run."""
    from app.models import MLTrainingData

    if MLTrainingData.query.first():
        return

    samples = [
        # Food
        ("pizza", "Food"), ("burger", "Food"), ("sushi", "Food"),
        ("grocery shopping", "Food"), ("coffee", "Food"), ("lunch", "Food"),
        ("dinner", "Food"), ("breakfast", "Food"), ("restaurant", "Food"),
        ("sandwich", "Food"), ("salad", "Food"), ("smoothie", "Food"),
        ("bread milk eggs", "Food"), ("supermarket", "Food"), ("bakery", "Food"),
        # Transport
        ("uber ride", "Transport"), ("taxi", "Transport"), ("bus ticket", "Transport"),
        ("train fare", "Transport"), ("metro card", "Transport"), ("fuel petrol", "Transport"),
        ("car parking", "Transport"), ("lyft", "Transport"), ("flight ticket", "Transport"),
        ("toll fee", "Transport"), ("bike rental", "Transport"),
        # Shopping
        ("amazon purchase", "Shopping"), ("clothes shoes", "Shopping"),
        ("online shopping", "Shopping"), ("electronics gadget", "Shopping"),
        ("furniture", "Shopping"), ("gift", "Shopping"), ("zara h&m", "Shopping"),
        ("department store", "Shopping"), ("mall", "Shopping"),
        # Bills
        ("electricity bill", "Bills"), ("water bill", "Bills"), ("internet plan", "Bills"),
        ("phone bill", "Bills"), ("rent payment", "Bills"), ("insurance premium", "Bills"),
        ("gas bill", "Bills"), ("cable tv", "Bills"), ("mortgage", "Bills"),
        # Entertainment
        ("netflix subscription", "Entertainment"), ("spotify music", "Entertainment"),
        ("movie tickets", "Entertainment"), ("concert", "Entertainment"),
        ("gaming", "Entertainment"), ("youtube premium", "Entertainment"),
        ("disney plus", "Entertainment"), ("bowling", "Entertainment"),
        ("amusement park", "Entertainment"),
        # Healthcare
        ("doctor visit", "Healthcare"), ("pharmacy medicine", "Healthcare"),
        ("hospital", "Healthcare"), ("dental", "Healthcare"),
        ("gym membership", "Healthcare"), ("vitamins supplements", "Healthcare"),
        ("physiotherapy", "Healthcare"), ("eye care", "Healthcare"),
        # Education
        ("tuition fee", "Education"), ("books textbooks", "Education"),
        ("online course", "Education"), ("udemy coursera", "Education"),
        ("school supplies", "Education"), ("workshop seminar", "Education"),
        ("library fee", "Education"),
        # Travel
        ("hotel booking", "Travel"), ("airbnb", "Travel"), ("vacation trip", "Travel"),
        ("travel insurance", "Travel"), ("passport visa", "Travel"),
        ("sightseeing tour", "Travel"),
        # Others
        ("miscellaneous", "Others"), ("donation charity", "Others"),
        ("subscription", "Others"), ("tax payment", "Others"),
        ("loan repayment", "Others"),
    ]
    for desc, cat in samples:
        db.session.add(MLTrainingData(description=desc, category=cat))
    db.session.commit()
