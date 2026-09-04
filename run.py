"""
Application entry point.

Run this file to start the development server:
    python run.py
"""
from app import create_app

# The `flask db ...` commands also look for this `app` variable.
app = create_app()


if __name__ == "__main__":
    # Only runs when executing this file directly.
    # debug=True reloads the server automatically on code changes.
    app.run(debug=True, port=5000)