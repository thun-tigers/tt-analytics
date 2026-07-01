import logging
import secrets
from urllib.parse import urlencode, urljoin, urlparse

import jwt
from flask import Blueprint, current_app, flash, redirect, request, session, url_for
from werkzeug.security import generate_password_hash

from ..authz import normalize_auth_payload
from ..extensions import db, limiter
from ..models import User

bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


def get_auth_login_url(next_page=None):
    auth_base_url = current_app.config.get('AUTH_BASE_URL', 'http://localhost:8085').rstrip('/')
    query = {'next_service': 'tt-analytics'}
    if next_page:
        query['next'] = next_page
    return f"{auth_base_url}/?{urlencode(query)}"


def get_auth_logout_url():
    auth_base_url = current_app.config.get('AUTH_BASE_URL', 'http://localhost:8085').rstrip('/')
    return f"{auth_base_url}/logout"


@bp.route("/login")
def login():
    next_page = request.args.get("next")
    if next_page and not is_safe_url(next_page):
        next_page = None
    return redirect(get_auth_login_url(next_page))


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(get_auth_logout_url())


@bp.route("/auth/sso")
@limiter.limit("60/minute")
def sso_login():
    token = request.args.get("token", "").strip()
    if not token:
        flash("SSO-Token fehlt.", "danger")
        return redirect(url_for("auth.login"))

    try:
        payload = jwt.decode(
            token,
            current_app.config.get("SSO_SHARED_SECRET") or current_app.config.get("SECRET_KEY"),
            algorithms=["HS256"],
            audience=current_app.config.get("SSO_EXPECTED_AUDIENCE", "tt-analytics"),
        )
    except jwt.ExpiredSignatureError:
        flash("SSO-Token ist abgelaufen. Bitte erneut starten.", "warning")
        return redirect(url_for("auth.login"))
    except jwt.InvalidTokenError:
        flash("Ungültiger SSO-Token.", "danger")
        return redirect(url_for("auth.login"))

    auth = normalize_auth_payload(payload)
    claims = auth["claims"]
    username = (claims.get("username") or "").strip()
    role = auth["service_role"]

    if not username:
        flash("SSO-Token enthält keinen Benutzernamen.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(username=username).first()
    if not user:
        if not current_app.config.get("SSO_AUTO_PROVISION_USERS", True):
            flash("SSO-Benutzer ist nicht freigeschaltet.", "danger")
            return redirect(url_for("auth.login"))
        user = User(username=username, role=role, password_hash=generate_password_hash(secrets.token_hex(32)))
        db.session.add(user)
    if current_app.config.get("SSO_SYNC_ROLE", True):
        user.sync_from_sso_claims(claims)
    elif claims.get("sub"):
        user.auth_user_id = int(claims["sub"])
    db.session.commit()

    session["user_id"] = user.id
    session["auth_user_id"] = user.auth_user_id
    session["username"] = user.username
    session["user_role"] = user.service_role
    session["platform_role"] = user.platform_role
    session["memberships"] = auth["memberships"]
    session["permissions"] = auth["permissions"]
    session["claims_json"] = user.claims_json or {}
    next_page = request.args.get("next")
    if next_page and is_safe_url(next_page):
        return redirect(next_page)
    return redirect(url_for("main.index"))
