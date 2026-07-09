import logging
import secrets
import requests

from dotenv import load_dotenv
from flask import Flask, abort, request, session
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import Config
from .extensions import db, limiter, migrate
from .models import Season, Team
from .routes import auth, main, api


def create_app(config_class=Config):
    load_dotenv()

    log_level = getattr(logging, config_class.LOG_LEVEL.upper(), logging.INFO)
    formatter = logging.Formatter(
        "[%(asctime)s +0000] [%(process)d] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    app = Flask(__name__)
    app.config.from_object(config_class)

    # Flask session config
    app.config.setdefault("SESSION_COOKIE_SECURE", True)
    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
    app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")

    if not app.config.get("SECRET_KEY"):
        if app.debug or app.testing:
            app.logger.warning("SECRET_KEY is not set; running in insecure development mode.")
        else:
            raise RuntimeError("SECRET_KEY must be set in production.")

    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(api.bp)

    # Zentrales UI-Layout aus tt-common
    from tt_common import register_shared_ui
    register_shared_ui(
        app,
        brand_label="Analytics",
        brand_icon="bi-graph-up-arrow",
        home_endpoint="main.index",
        logout_endpoint="auth.logout",
    )

    @app.context_processor
    def inject_current_user():
        # Das geteilte Layout gated auf current_user; analytics arbeitet
        # sessionbasiert, daher hier aus der Session ableiten.
        if session.get("user_id"):
            return {"current_user": {
                "username": session.get("username"),
                "role": session.get("user_role", "user"),
            }}
        return {"current_user": None}

    def generate_csrf_token():
        token = session.get("_csrf_token")
        if not token:
            token = secrets.token_urlsafe(32)
            session["_csrf_token"] = token
        return token

    @app.context_processor
    def inject_csrf_token():
        return {"csrf_token": generate_csrf_token()}

    @app.context_processor
    def inject_platform_links():
        auth_base_url = app.config.get("AUTH_BASE_URL", "http://localhost:8085").rstrip("/")
        return {
            "auth_base_url": auth_base_url,
            "auth_dashboard_url": f"{auth_base_url}/",
        }

    @app.context_processor
    def inject_pending_messages_count():
        auth_user_id = session.get("auth_user_id")
        if not auth_user_id:
            user_id = session.get("user_id")
            if user_id:
                user = db.session.get(User, user_id)
                auth_user_id = user.auth_user_id if user else None
        return {"pending_messages_count": _fetch_pending_messages_count(app, auth_user_id)}

    @app.before_request
    def csrf_protect():
        if request.path.startswith("/api/internal/"):
            return  # Interne Service-zu-Service APIs sind via Secret geschützt
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            token = session.get("_csrf_token")
            if request.is_json:
                payload = request.get_json(silent=True) or {}
                request_token = request.headers.get("X-CSRFToken") or payload.get("csrf_token")
            else:
                request_token = request.form.get("csrf_token")
            if not token or not request_token or token != request_token:
                abort(400)

    def seed_defaults():
        changed = False

        season = Season.query.filter_by(label="2026").first()
        if not season:
            db.session.add(Season(label="2026", year=2026, active=True))
            changed = True

        if changed:
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                app.logger.info("Default analytics seed raced with another worker; continuing.")

    def apply_schema_shims():
        inspector = inspect(db.engine)
        tables = set(inspector.get_table_names())

        if "user" in tables:
            columns = {col["name"] for col in inspector.get_columns("user")}
            if "auth_user_id" not in columns:
                dialect = db.engine.dialect.name
                if dialect == "postgresql":
                    db.session.execute(text('ALTER TABLE "user" ADD COLUMN auth_user_id INTEGER'))
                else:
                    db.session.execute(text("ALTER TABLE user ADD COLUMN auth_user_id INTEGER"))
            if "service_role" not in columns:
                if db.engine.dialect.name == "postgresql":
                    db.session.execute(text('ALTER TABLE "user" ADD COLUMN service_role VARCHAR(20) NOT NULL DEFAULT \'user\''))
                else:
                    db.session.execute(text("ALTER TABLE user ADD COLUMN service_role VARCHAR(20) NOT NULL DEFAULT 'user'"))
            if "platform_role" not in columns:
                if db.engine.dialect.name == "postgresql":
                    db.session.execute(text('ALTER TABLE "user" ADD COLUMN platform_role VARCHAR(20) NOT NULL DEFAULT \'user\''))
                else:
                    db.session.execute(text("ALTER TABLE user ADD COLUMN platform_role VARCHAR(20) NOT NULL DEFAULT 'user'"))
            if "claims_json" not in columns:
                json_default = "'{}'"
                if db.engine.dialect.name == "postgresql":
                    db.session.execute(text(f'ALTER TABLE "user" ADD COLUMN claims_json JSON NOT NULL DEFAULT {json_default}'))
                else:
                    db.session.execute(text(f"ALTER TABLE user ADD COLUMN claims_json TEXT NOT NULL DEFAULT {json_default}"))
            db.session.commit()

        if "game" in tables:
            columns = {column["name"] for column in inspector.get_columns("game")}
            if "analysis_mode" in columns:
                # Keep legacy column in place but stop depending on it in the app.
                pass

    with app.app_context():
        if app.config.get("AUTO_CREATE_DB"):
            db.create_all()
            apply_schema_shims()
            seed_defaults()

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    return app


def _fetch_pending_messages_count(app, auth_user_id):
    if not auth_user_id:
        return 0

    members_base = (app.config.get("TT_MEMBERS_INTERNAL_URL") or "http://tt-members:5000").rstrip("/")
    secret = app.config.get("INTERNAL_API_SECRET") or app.config.get("SSO_SHARED_SECRET") or app.config.get("SECRET_KEY")
    if not secret:
        return 0

    try:
        response = requests.get(
            f"{members_base}/api/internal/messages/count",
            params={"auth_user_id": auth_user_id},
            headers={"X-TT-Internal-Secret": secret},
            timeout=2,
        )
        if response.status_code != 200:
            return 0
        payload = response.json() or {}
        return max(0, int(payload.get("pending_messages_count") or 0))
    except Exception:
        return 0
