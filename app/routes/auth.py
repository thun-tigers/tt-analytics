import logging
import secrets

import jwt
from flask import Blueprint, current_app, flash, redirect, request, session, url_for
from werkzeug.security import generate_password_hash

from tt_common.sso import get_auth_login_url, get_auth_logout_url, is_safe_url

from ..authz import normalize_auth_payload
from ..extensions import db, limiter
from ..models import User
from ..sso_replay import is_replayed_sso_token

bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)


@bp.route("/login")
def login():
    next_page = request.args.get("next")
    if next_page and not is_safe_url(next_page):
        next_page = None
    return redirect(get_auth_login_url('tt-analytics', next_page))


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

    if is_replayed_sso_token(payload):
        flash("SSO-Token wurde bereits verwendet. Bitte erneut anmelden.", "danger")
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
    session["role_permissions"] = auth["role_permissions"]
    session["claims_json"] = user.claims_json or {}
    next_page = request.args.get("next")
    if next_page and is_safe_url(next_page):
        return redirect(next_page)
    return redirect(url_for("main.index"))
