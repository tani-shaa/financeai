# FinanceAI

### AI-Powered Personal Finance Management and Insights

FinanceAI is a Flask-based personal finance application that enables users to manage income and expenses, analyze spending patterns, predict future spending, and interact with their financial data through an AI-powered assistant.

## Features

* User authentication with secure password hashing
* Income and expense management
* Interactive financial dashboard and spending visualizations
* Automatic expense categorization using Machine Learning
* Monthly spending prediction using Random Forest
* AI-powered financial assistant using Google Gemini
* Retrieval-Augmented Generation (RAG) for context-aware financial insights
* Responsive web interface

## Machine Learning

**Expense Classification**
Uses TF-IDF and Logistic Regression to classify expenses based on their descriptions.

**Spending Prediction**
Uses a Random Forest Regressor with historical spending data, lag features, and rolling averages to estimate upcoming monthly spending.

## Generative AI

The financial assistant integrates the Google Gemini API and retrieves relevant user-specific financial data before generating responses. This allows users to ask natural-language questions about their income and spending.

## Tech Stack

**Backend:** Python, Flask
**Database:** SQLite, SQLAlchemy
**Machine Learning:** Scikit-learn, Pandas, NumPy
**Generative AI:** Google Gemini API, RAG
**Frontend:** HTML, CSS, Bootstrap, JavaScript, Chart.js
**Authentication:** Flask-Login, Flask-Bcrypt
**Deployment:** Gunicorn, Render/Railway

## Project Structure

```text
financeai/
├── app/
│   ├── auth/
│   ├── chat/
│   ├── dashboard/
│   ├── expenses/
│   ├── income/
│   ├── insights/
│   ├── ml/
│   ├── static/
│   └── templates/
├── config.py
├── run.py
├── wsgi.py
├── requirements.txt
├── .env.example
└── README.md
```

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/tani-shaa/financeai.git
cd financeai
```

### 2. Create and activate a virtual environment

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file:

```env
SECRET_KEY=your_secret_key
GEMINI_API_KEY=your_gemini_api_key
```

### 5. Run the application

```bash
python run.py
```

The dashboard is available locally at:

```text
http://127.0.0.1:5000/dashboard
```

## Future Improvements

* Advanced financial forecasting
* Budget recommendations
* Financial goal tracking
* Expense anomaly detection
* Automated financial reports
* Improved conversational memory

## Author

**Tanisha Sharma**
Computer Science Engineering | AI and Machine Learning

[GitHub](https://github.com/tani-shaa)
