# FinanceAI

A personal finance web application for tracking expenses, managing income, and gaining AI-powered insights into spending habits. Built with Flask and a glassmorphism UI.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, Flask 3.0 |
| Database | SQLite via Flask-SQLAlchemy |
| ML / Data | Scikit-learn, Pandas, NumPy |
| Auth | Flask-Login, Flask-Bcrypt |
| AI | Google Gemini API (RAG-based chat) |
| Frontend | Bootstrap 5, Chart.js 4, Vanilla JS |
| Design | Glassmorphism UI, CSS Variables (dark/light themes) |
| Deployment | Render / Railway via Gunicorn |

---

## Features

- **Authentication** — Register, login, logout with bcrypt password hashing and session management
- **Dashboard** — Key financial stats, budget progress bar, recent transactions, and top spending categories
- **Expense Management** — Full CRUD with category, payment method, and date
- **Income Management** — Full CRUD with source tagging
- **AI Chat Assistant** — RAG-powered chat using Gemini API; asks questions about your actual financial data
- **ML Category Classifier** — TF-IDF + Logistic Regression auto-classifies expense descriptions
- **Spending Predictor** — Random Forest Regressor predicts next month's total spend
- **Smart Insights** — Automatically generated insight cards based on your transaction history
- **Landing Page** — Public-facing home page for unauthenticated visitors
- **Dark / Light Theme** — Toggle persisted via localStorage
- **Responsive Layout** — Mobile, tablet, and desktop support

---

## Project Structure

```
ai-financial-assistant/
├── app/
│   ├── __init__.py              # App factory, DB init, ML seed data
│   ├── models.py                # SQLAlchemy models
│   ├── auth/                    # Register, login, logout, profile
│   ├── dashboard/               # Summary stats, quick-add, landing page
│   ├── expenses/                # Expense CRUD
│   ├── income/                  # Income CRUD
│   ├── chat/                    # AI chat with RAG engine
│   ├── ml/                      # ML classifier and spending predictor
│   ├── insights/                # Auto-generated financial insights
│   ├── static/
│   │   ├── css/style.css        # Glassmorphism design system and theme variables
│   │   └── js/
│   │       ├── app.js           # Theme toggle, sidebar, flash alerts
│   │       └── charts.js        # Chart.js configurations
│   └── templates/               # Jinja2 HTML templates
│       ├── home.html            # Public landing page
│       ├── base.html            # Base layout with sidebar and topbar
│       └── ...
├── config.py
├── run.py                       # Development server entry point
├── wsgi.py                      # Production entry point
├── Procfile                     # Render / Railway deployment config
└── requirements.txt
```

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/tani-shaa/financeai.git
cd financeai

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env and set SECRET_KEY and GEMINI_API_KEY

# 5. Run the development server
python run.py
# Open http://127.0.0.1:5000
```

---

## Environment Variables

| Variable | Description |
|---|---|
| `SECRET_KEY` | Flask session secret key |
| `GEMINI_API_KEY` | Google Gemini API key for the AI chat feature |
| `DATABASE_URL` | Optional — defaults to SQLite at `instance/finance.db` |

---

## Machine Learning

### Category Classifier

- **Algorithm**: TF-IDF Vectorizer with Logistic Regression
- **Input**: Expense description text
- **Output**: Predicted category label with confidence percentage
- **Training data**: 80+ seed samples, augmented by the user's own labelled expenses
- **Retraining**: Available via the ML Predictions page

### Spending Predictor

- **Algorithm**: Random Forest Regressor
- **Input**: Last 6 months of monthly totals with lag features, rolling means, and trend
- **Output**: Predicted spend for the next month
- **Fallback**: Weighted moving average when fewer than 7 months of data are available

---

## Database Schema

```
users           id, username, email, password_hash, full_name, currency, monthly_budget
expenses        id, user_id, amount, category, description, date, payment_method
income          id, user_id, amount, source, description, date
predictions     id, user_id, predicted_amount, prediction_month, algorithm, confidence
ml_training     id, description, category
```

---

## Deployment

### Render

1. Push the repository to GitHub
2. Create a new Web Service on [render.com](https://render.com) and connect the repo
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `gunicorn wsgi:app`
5. Add environment variables: `SECRET_KEY`, `GEMINI_API_KEY`

### Railway

1. Push the repository to GitHub
2. Create a new project on [railway.app](https://railway.app) and deploy from GitHub
3. Add environment variables: `SECRET_KEY`, `GEMINI_API_KEY`
4. Railway auto-detects the `Procfile`

---

## License

MIT
