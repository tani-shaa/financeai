"""
run.py — Application entry point

WHAT IS python-dotenv?
  It reads your .env file and loads every KEY=VALUE pair into
  os.environ so your app can read them with os.environ.get("KEY").
  This keeps secrets OUT of your source code.
"""
import os
from dotenv import load_dotenv

# Load .env file FIRST — before anything else reads env vars
# find_dotenv() searches parent directories if .env isn't in cwd
load_dotenv()

from app import create_app
from app.ml.engine import retrain_classifier_from_db

app = create_app(os.environ.get("FLASK_ENV", "development"))

if __name__ == "__main__":
    with app.app_context():
        try:
            retrain_classifier_from_db()
            print("[ML]  Category classifier ready.")
        except Exception as e:
            print(f"[ML]  Classifier training skipped: {e}")

    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if gemini_key:
        print("[AI]  Gemini API key loaded [OK]")
    else:
        print("[AI]  WARNING: GEMINI_API_KEY not set in .env")

    print("\n  Nexora Trading  ->  http://127.0.0.1:5000\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
