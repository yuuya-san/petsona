import pymysql # pyright: ignore[reportMissingModuleSource]
from flask import current_app # pyright: ignore[reportMissingImports]
from sqlalchemy import create_engine # pyright: ignore[reportMissingImports]
from urllib.parse import urlparse


def ensure_database_exists():
    """
    Ensures the MySQL database exists before the app starts.
    Creates the database if missing.
    """

    db_user = current_app.config.get("DB_USERNAME")
    db_pass = current_app.config.get("DB_PASSWORD")
    db_host = current_app.config.get("DB_HOST")
    db_port = current_app.config.get("DB_PORT")
    db_name = current_app.config.get("DB_NAME")

    database_uri = current_app.config.get("SQLALCHEMY_DATABASE_URI") or current_app.config.get("MYSQL_URL")

    if database_uri and (not db_user or not db_host or not db_name):
        parsed = urlparse(database_uri)
        if parsed.scheme and parsed.scheme.startswith("mysql"):
            db_user = db_user or parsed.username
            db_pass = db_pass or parsed.password
            db_host = db_host or parsed.hostname or "localhost"
            db_port = db_port or parsed.port
            if not db_name and parsed.path:
                db_name = parsed.path.lstrip("/")

    if not db_host:
        db_host = "localhost"

    if db_port is None or db_port == "":
        db_port = current_app.config.get("DB_PORT", 3306)

    try:
        db_port = int(db_port)
    except (TypeError, ValueError):
        db_port = 3306

    if not db_user or not db_name:
        current_app.logger.warning(
            "Skipping database creation: DB_USERNAME or DB_NAME is not configured."
        )
        return

    connection = None
    try:
        connection = pymysql.connect(
            host=db_host,
            user=db_user,
            password=db_pass or "",
            port=db_port,
            autocommit=True,
            connect_timeout=10,
        )
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`;")
        cursor.close()
    except Exception as e:
        current_app.logger.error(f"Database creation failed: {e}", exc_info=True)
    finally:
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass


def create_tables(db):
    """
    Ensures all SQLAlchemy models create their tables automatically.
    """

    engine = create_engine(current_app.config["SQLALCHEMY_DATABASE_URI"])

    # Connect and create tables if not exist
    db.metadata.create_all(engine)
    
    # Add any missing columns to existing tables
    add_missing_columns(engine)


def add_missing_columns(engine):
    """
    Adds missing columns to existing tables
    """
    from sqlalchemy import text # pyright: ignore[reportMissingImports]
    
    with engine.begin() as connection:
        # Add is_open column to merchants table if it doesn't exist
        try:
            connection.execute(text("""
                ALTER TABLE merchants 
                ADD COLUMN is_open BOOLEAN DEFAULT 1 
                AFTER is_verified
            """))
        except Exception as e:
            if "Duplicate column" not in str(e) and "already exists" not in str(e):
                pass
            # else: column already exists, continue
        
        # Add is_24h column to merchants table if it doesn't exist
        try:
            connection.execute(text("""
                ALTER TABLE merchants 
                ADD COLUMN is_24h BOOLEAN DEFAULT 0 
                AFTER closing_time
            """))
        except Exception as e:
            if "Duplicate column" not in str(e) and "already exists" not in str(e):
                pass
            # else: column already exists, continue
