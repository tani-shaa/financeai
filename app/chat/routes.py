"""
chat/routes.py
==============

WHAT IS A FLASK BLUEPRINT?
  A Blueprint is a way to split your Flask app into modules.
  Instead of one giant routes file, each feature has its own file.
  Here: all /chat/* URLs are handled here.

WHAT IS SSE (Server-Sent Events)?
  SSE lets the server PUSH data to the browser without the browser asking.
  This is how we get the "typing" effect — Gemini streams tokens one by one,
  and we send each token to the browser immediately as it arrives.
  
  Normal request:  Browser asks → Server thinks → Server replies (all at once)
  SSE:             Browser opens connection → Server sends chunks as they arrive

  You've seen this on ChatGPT — words appear one by one. That's SSE.
"""

import os
import json
from flask import (
    Blueprint, render_template, request,
    jsonify, stream_with_context, Response
)
from flask_login import login_required, current_user
from app.chat.rag_engine import (
    ask_financial_question,
    SUGGESTED_QUESTIONS,
)

chat_bp = Blueprint("chat", __name__)

# ─────────────────────────────────────────────────────────────────────────────
# Helper — safely get API key
# ─────────────────────────────────────────────────────────────────────────────
def _get_api_key() -> str:
    """
    Read the Gemini API key from environment variables.
    
    WHY ENVIRONMENT VARIABLES?
      - Never hardcode secrets in your code
      - .env file is listed in .gitignore so it never goes to GitHub
      - On deployment platforms (Render/Railway) you set them in the dashboard
    """
    return os.environ.get("GEMINI_API_KEY", "")


# ─────────────────────────────────────────────────────────────────────────────
# Route 1: Chat Page (GET)
# ─────────────────────────────────────────────────────────────────────────────
@chat_bp.route("/")
@login_required   # If not logged in → redirect to login page
def index():
    """
    Renders the chat UI page.
    
    @login_required is a DECORATOR — a function that wraps another function.
    It checks if the user is logged in before running the route.
    If not logged in, Flask-Login redirects them to the login page.
    """
    api_key = _get_api_key()
    has_key = bool(api_key)   # True if key exists, False if empty

    return render_template(
        "chat/index.html",
        suggested=SUGGESTED_QUESTIONS,
        has_key=has_key,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Route 2: Ask endpoint (POST) — this is what JavaScript calls
# ─────────────────────────────────────────────────────────────────────────────
@chat_bp.route("/ask", methods=["POST"])
@login_required
def ask():
    """
    Receives the user's question via JSON POST request.
    Calls the RAG engine and returns the AI answer.
    
    REQUEST FORMAT (from JavaScript fetch):
        POST /chat/ask
        Content-Type: application/json
        Body: {"question": "Where am I overspending?"}
    
    RESPONSE FORMAT:
        {"answer": "Based on your data, you spent $320 on Food..."}
    """
    # Get JSON body from the request
    # request.get_json() parses the JSON body automatically
    data     = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()

    # Validate input
    if not question:
        # Return error with HTTP 400 (Bad Request) status code
        return jsonify({"error": "Please enter a question."}), 400

    api_key = _get_api_key()
    if not api_key:
        return jsonify({
            "error": "Gemini API key not configured. Add GEMINI_API_KEY to your .env file."
        }), 500

    try:
        # ── THE MAIN CALL ─────────────────────────────────────────────────
        # This calls our RAG engine:
        #   1. Fetches user data from SQLite
        #   2. Builds the prompt
        #   3. Calls Gemini
        #   4. Returns the answer text
        answer = ask_financial_question(
            question=question,
            user_id=current_user.id,       # Only THIS user's data
            api_key=api_key,
            currency=current_user.currency,
        )
        return jsonify({"answer": answer})

    except Exception as e:
        # Always handle exceptions in web apps
        # Return a user-friendly message, log the real error
        print(f"[Chat Error] {e}")
        return jsonify({
            "error": f"AI service error: {str(e)}"
        }), 500


# ─────────────────────────────────────────────────────────────────────────────
# Route 3: Quick context endpoint — shows what data the AI sees
# ─────────────────────────────────────────────────────────────────────────────
@chat_bp.route("/context")
@login_required
def view_context():
    """
    Debug/educational route — shows the exact context string
    that gets injected into the Gemini prompt.
    
    Great for interviews: "I built a way to inspect exactly what
    the LLM receives, so I can debug and improve the RAG pipeline."
    """
    from app.chat.rag_engine import _retrieve_financial_context
    context = _retrieve_financial_context(current_user.id, current_user.currency)
    return jsonify({"context": context})
