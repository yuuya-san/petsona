import os
from app import create_app, db
from flask import redirect, url_for, request

# Create Flask app + SocketIO
app, socketio = create_app()


# -----------------------------
# SAFE DB INITIALIZATION ONLY
# -----------------------------
with app.app_context():
    try:
        from app.utils.db_init import create_tables
        create_tables(db)
        print("Tables ensured successfully.")
    except Exception as e:
        print("DB init warning:", e)


# -----------------------------
# ROUTES (HEALTH CHECK)
# -----------------------------
@app.route("/")
def home():
    return redirect("/auth/home")

# -----------------------------
# ENTRY POINT (RAILWAY SAFE)
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    try:
        socketio.run(app, host="0.0.0.0", port=port)
    except Exception:
        app.run(host="0.0.0.0", port=port)