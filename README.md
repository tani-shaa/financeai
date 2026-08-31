# 💰 AI Financial Assistant

> An intelligent expense tracking and budgeting web app powered by Machine Learning.
> Built with Flask · Scikit-learn · SQLite · Bootstrap 5 · Chart.js

---

## 🚀 Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11, Flask 3.0 |
| **Database** | SQLite via Flask-SQLAlchemy |
| **ML / Data** | Scikit-learn, Pandas, NumPy |
| **Auth** | Flask-Login, Flask-Bcrypt |
| **Frontend** | Bootstrap 5, Chart.js 4, Vanilla JS |
| **Design** | Glassmorphism UI, CSS Variables (dark/light) |
| **Deployment** | Render / Railway (Gunicorn) |

---

## ✨ Features

- **User Auth** — Register, login, logout, password hashing, session management
- **Dashboard** — Glassmorphism stat cards, 4 Chart.js visualisations, budget progress bar
- **Expense CRUD** — Add / edit / delete with category, payment method, date
- **Income CRUD** — Add / edit / delete with source tagging
- **AI Category Prediction** — TF-IDF + Logistic Regression auto-classifies descriptions
- **Spending Prediction** — Random Forest Regressor predicts next month's spend
- **Budget Recommendations** — Safe budget, expected savings, smart tips
- **AI Insights Page** — 6+ personalised insight cards generated from your data
- **Dark / Light Mode** — Persisted via localStorage
- **Fully Responsive** — Works on mobile, tablet, desktop

---

## 📁 Project Structure

```
ai-financial-assistant/
├── app/
│   ├── __init__.py          # App factory, DB init, ML seed
│   ├── models.py            # SQLAlchemy models
│   ├── auth/                # Register, Login, Profile
│   ├── dashboard/           # Summary stats + charts
│   ├── expenses/            # Expense CRUD
│   ├── income/              # Income CRUD
│   ├── ml/                  # ML engine + routes
│   ├── insights/            # AI insights generator
│   ├── static/
│   │   ├── css/style.css    # Glassmorphism design system
│   │   └── js/
│   │       ├── app.js       # Global JS (theme, sidebar, alerts)
│   │       └── charts.js    # Chart.js (pie, bar, line, area)
│   └── templates/           # Jinja2 HTML templates
├── config.py
├── run.py                   # Dev server entry point
├── wsgi.py                  # Production entry point
├── Procfile                 # Render / Railway deploy
└── requirements.txt
```

---

## ⚡ Quick Start

```bash
# 1. Clone
git clone https://github.com/yourname/ai-financial-assistant.git
cd ai-financial-assistant

# 2. Virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Mac/Linux

# 3. Install
pip install -r requirements.txt

# 4. Run
python run.py
# → http://127.0.0.1:5000
```

---

## 🧠 ML Models

### A. Category Classifier
- **Algorithm**: TF-IDF Vectorizer → Logistic Regression
- **Input**: Expense description text
- **Output**: Category label + confidence %
- **Training data**: 80+ seed samples + user's own expenses
- **Retrain**: Click "Retrain Classifier" on the ML Predictions page

### B. Spending Predictor
- **Algorithm**: Random Forest Regressor
- **Input**: Last 6 months of monthly totals (lag features, rolling means, trend)
- **Output**: Predicted next-month spend
- **Fallback**: Weighted average when < 7 months of data

---

## 🗄 Database Schema

```
users          → id, username, email, password_hash, full_name, currency, monthly_budget
expenses       → id, user_id, amount, category, description, date, payment_method
income         → id, user_id, amount, source, description, date
predictions    → id, user_id, predicted_amount, prediction_month, algorithm, confidence
ml_training    → id, description, category
```

---

## ☁️ Deploy to Render

1. Push repo to GitHub
2. New Web Service on render.com → connect repo
3. **Build command**: `pip install -r requirements.txt`
4. **Start command**: `gunicorn wsgi:app`
5. Add environment variable: `SECRET_KEY=your-secret-here`

## ☁️ Deploy to Railway

1. Push repo to GitHub
2. New project on railway.app → Deploy from GitHub
3. Add `SECRET_KEY` env var
4. Railway auto-detects `Procfile`

---

## 📸 Screenshots

| Dashboard | Expenses | AI Insights |
|---|---|---|
| Glassmorphism cards + 4 charts | CRUD table with category badges | Personalised insight cards |
