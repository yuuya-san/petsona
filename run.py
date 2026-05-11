import os
from app import create_app, db

# Create Flask app and SocketIO instance
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
# ENTRY POINT (PRODUCTION SAFE)
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    env = os.environ.get("FLASK_ENV", "development")

    if env == "production":
        # Production: Use eventlet for WebSocket support
        try:
            import eventlet # pyright: ignore[reportMissingImports]
            eventlet.monkey_patch()
        except ImportError:
            print("WARNING: eventlet not installed. Install with: pip install eventlet")

        # For production, use gunicorn instead:
        # gunicorn --worker-class eventlet -w 1 run:app
        print("For production, use: gunicorn --worker-class eventlet -w 1 run:app")
        socketio.run(app, host="0.0.0.0", port=port, debug=False, use_reloader=False)
    else:
        # Development: Use threading
        socketio.run(app, host="0.0.0.0", port=port, debug=True)