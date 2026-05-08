import os
from app import create_app, db

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
# OPTIONAL: SAFE ADMIN CHECK (NON-BLOCKING)
# -----------------------------
def ensure_admin():
    try:
        from app.models import User
        from app.utils.admin import create_admin  # adjust if your path differs

        ADMIN_EMAIL = "petsona.helpcare@gmail.com"
        DEFAULT_ADMIN_PHOTO = "images/avatar/dog.png"

        admin_exists = User.query.filter_by(email=ADMIN_EMAIL).first()

        if not admin_exists:
            create_admin(
                email=ADMIN_EMAIL,
                password="Petsona-0717",
                photo_url=DEFAULT_ADMIN_PHOTO
            )
            print("Admin created.")
    except Exception as e:
        print("Admin setup skipped:", e)

# Run admin setup safely AFTER app starts
with app.app_context():
    ensure_admin()

# -----------------------------
# ROUTES (HEALTH CHECK)
# -----------------------------
@app.route("/")
def home():
    return "PetSona is running successfully 🚀"

# -----------------------------
# ENTRY POINT (RAILWAY SAFE)
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    try:
        socketio.run(app, host="0.0.0.0", port=port)
    except Exception:
        app.run(host="0.0.0.0", port=port)