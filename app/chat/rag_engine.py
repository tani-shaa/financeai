"""
rag_engine.py — The RAG Brain
==============================

WHAT IS RAG?
  RAG = Retrieval Augmented Generation
  
  Problem:  Gemini doesn't know YOUR expenses. It was trained on the internet.
  Solution: We RETRIEVE your data from SQLite, then AUGMENT the LLM prompt with
            it, so Gemini can GENERATE answers about YOUR finances.

  Think of it like this:
    - Gemini is a brilliant financial expert
    - RAG hands them YOUR bank statement before they answer
    - Without RAG: generic advice
    - With RAG:    "You spent $340 on food last month, 32% above your average"

WHAT IS LANGCHAIN?
  It's a Python library that makes it easy to:
    1. Connect to different LLMs (Gemini, GPT, Llama) with the same code
    2. Build "chains" — sequences of steps (retrieve → format → ask LLM)
    3. Format prompts cleanly using PromptTemplate

  The "|" pipe operator chains steps together, just like Unix pipes:
    prompt | llm | output_parser
"""

import os
from datetime import date, datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: Create the LLM object
# ─────────────────────────────────────────────────────────────────────────────
# WHAT IS THIS?
#   ChatGoogleGenerativeAI is LangChain's wrapper around Google Gemini API.
#   "model" tells it which Gemini version to use.
#   "gemini-1.5-flash" = fast, free tier, great for text tasks.
#
# WHY NOT PUT THE KEY HERE DIRECTLY?
#   Security. Never hardcode API keys in source files.
#   We read it from an environment variable instead.
#   os.environ.get("GEMINI_API_KEY") reads from your .env file or system env.

def _get_llm(api_key: str):
    """
    Factory function — creates and returns the Gemini LLM object.
    
    Why a function instead of a global?
    Because we need the api_key at call time, not at import time.
    This also makes it easy to swap Gemini for GPT later — change one line.
    """
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",   # Fast, free-tier Gemini model
        google_api_key=api_key,
        temperature=0.7,            # 0=robotic/factual, 1=creative. 0.7 = balanced
        max_tokens=1024,            # Max words in response
    )


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: Retrieve financial data from SQLite
# ─────────────────────────────────────────────────────────────────────────────
# WHY DO WE DO THIS?
#   This is the "R" in RAG — Retrieval.
#   We pull the user's actual data from the database and format it as text
#   so the LLM can read it like a document.
#
# KEY INSIGHT:
#   LLMs work on TEXT. So we convert database rows → readable text summary.
#   This text becomes the "context" we inject into the prompt.

def _retrieve_financial_context(user_id: int, currency: str = "₹") -> str:
    """
    Queries SQLite for the user's financial data and returns it as
    a formatted text string that the LLM can understand.
    
    This is the RAG "retrieval" step.
    """
    # We import here (not at top) to avoid circular imports with Flask app
    from app.models import Expense, Income
    from app import db
    from sqlalchemy import func, extract

    today = date.today()
    year, month = today.year, today.month

    # ── Get current month expenses ────────────────────────────────────────
    # SQLAlchemy ORM query: SELECT * FROM expenses WHERE user_id=? 
    #   AND YEAR(date)=? AND MONTH(date)=?
    cur_expenses = (
        Expense.query
        .filter_by(user_id=user_id)
        .filter(
            extract("year",  Expense.date) == year,
            extract("month", Expense.date) == month,
        )
        .order_by(Expense.date.desc())
        .limit(30)   # Only last 30 to keep prompt size reasonable
        .all()
    )

    # ── Get last 3 months of totals ───────────────────────────────────────
    monthly_totals = (
        db.session.query(
            extract("year",  Expense.date).label("yr"),
            extract("month", Expense.date).label("mo"),
            func.sum(Expense.amount).label("total"),
        )
        .filter(Expense.user_id == user_id)
        .group_by("yr", "mo")
        .order_by("yr", "mo")
        .limit(6)
        .all()
    )

    # ── Category breakdown ────────────────────────────────────────────────
    category_totals = (
        db.session.query(Expense.category, func.sum(Expense.amount))
        .filter_by(user_id=user_id)
        .group_by(Expense.category)
        .all()
    )

    # ── Total income ──────────────────────────────────────────────────────
    total_income = (
        db.session.query(func.sum(Income.amount))
        .filter_by(user_id=user_id)
        .scalar() or 0
    )
    month_income = (
        db.session.query(func.sum(Income.amount))
        .filter(
            Income.user_id == user_id,
            extract("year",  Income.date) == year,
            extract("month", Income.date) == month,
        )
        .scalar() or 0
    )

    # ─────────────────────────────────────────────────────────────────────
    # NOW WE BUILD THE CONTEXT STRING
    # This is what gets injected into the LLM prompt.
    # Think of it as the "bank statement" we hand to the financial expert.
    # ─────────────────────────────────────────────────────────────────────
    lines = []
    lines.append(f"=== FINANCIAL DATA (as of {today.strftime('%B %Y')}) ===\n")

    # Monthly history
    lines.append("--- Monthly Expense History ---")
    for r in monthly_totals:
        label = datetime(int(r.yr), int(r.mo), 1).strftime("%B %Y")
        lines.append(f"  {label}: {currency}{float(r.total):.2f}")

    # Category breakdown
    lines.append("\n--- Spending by Category (All Time) ---")
    for cat, total in sorted(category_totals, key=lambda x: x[1], reverse=True):
        lines.append(f"  {cat}: {currency}{float(total):.2f}")

    # Current month detail
    lines.append(f"\n--- This Month's Transactions ({today.strftime('%B %Y')}) ---")
    if cur_expenses:
        for e in cur_expenses:
            lines.append(f"  {e.date} | {e.category:<15} | {currency}{e.amount:>8.2f} | {e.description}")
    else:
        lines.append("  No transactions this month yet.")

    # Income summary
    lines.append(f"\n--- Income ---")
    lines.append(f"  This month: {currency}{float(month_income):.2f}")
    lines.append(f"  Total ever: {currency}{float(total_income):.2f}")
    lines.append(f"  Net savings (all time): {currency}{float(total_income - sum(r[1] for r in category_totals)):.2f}")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3: Build the Prompt Template
# ─────────────────────────────────────────────────────────────────────────────
# WHAT IS A PROMPT TEMPLATE?
#   It's a string with placeholders — like Python's f-string but for LangChain.
#   {context}  = the financial data we retrieved
#   {question} = what the user typed
#   {currency} = user's currency symbol
#
# WHY DOES PROMPT DESIGN MATTER?
#   The LLM does EXACTLY what the prompt says. If you say "be concise", it's
#   concise. If you say "be a financial advisor", it acts like one.
#   This is called "Prompt Engineering" — a real job skill.

FINANCIAL_PROMPT = PromptTemplate(
    input_variables=["context", "question", "currency"],
    template="""You are FinanceAI, an expert personal financial advisor.
You have access to the user's real financial data below.
Answer ONLY based on this data. Be specific with numbers. Be friendly but professional.
Format your response with clear sections using emojis where helpful.
If you cannot answer from the data provided, say so honestly.

{context}

User's currency: {currency}

User's Question: {question}

Your Answer:"""
)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4: The main ask() function — ties everything together
# ─────────────────────────────────────────────────────────────────────────────
# THIS IS THE LANGCHAIN CHAIN:
#
#   prompt_template  →  fills in {context}, {question}, {currency}
#        |
#        ↓
#      llm           →  sends filled prompt to Gemini API
#        |
#        ↓
#   StrOutputParser  →  extracts just the text from Gemini's response object
#
# The "|" operator is LangChain's pipe — it connects steps into a chain.
# This is called LCEL (LangChain Expression Language).

def ask_financial_question(
    question: str,
    user_id: int,
    api_key: str,
    currency: str = "₹"
) -> str:
    """
    Main RAG function called by the Flask route.
    
    Steps:
      1. Retrieve user's financial data from DB (RAG = Retrieval)
      2. Inject it into the prompt template  (RAG = Augmentation)
      3. Send to Gemini and get answer        (RAG = Generation)
    
    Args:
        question: What the user typed in the chat
        user_id:  Which user's data to retrieve (security — only their data)
        api_key:  Gemini API key
        currency: User's currency symbol (e.g. "$", "€", "₹")
    
    Returns:
        String answer from Gemini
    """
    # Retrieve — get the user's data from SQLite
    context = _retrieve_financial_context(user_id, currency)

    # Build the LangChain chain using the | pipe operator
    # Think of it as: prompt → llm → parser, each step feeds the next
    llm   = _get_llm(api_key)
    chain = FINANCIAL_PROMPT | llm | StrOutputParser()

    # Invoke the chain with our variables
    # LangChain fills in the template, calls Gemini, returns the text
    response = chain.invoke({
        "context":  context,
        "question": question,
        "currency": currency,
    })

    return response


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5: Suggested questions (for the UI)
# ─────────────────────────────────────────────────────────────────────────────
SUGGESTED_QUESTIONS = [
    "Where am I overspending this month?",
    "How much did I spend on food last month?",
    "Am I saving enough money?",
    "Which category takes most of my budget?",
    "Give me a plan to save more next month.",
    "How does my spending compare to last month?",
    "What is my biggest unnecessary expense?",
    "Am I on track to meet my savings goal?",
]
