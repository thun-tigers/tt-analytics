from flask import Blueprint, current_app, jsonify, request

from ..extensions import db
from ..models import User

bp = Blueprint('api', __name__, url_prefix='/api')


def _authorized():
    expected = current_app.config.get('INTERNAL_API_SECRET')
    provided = request.headers.get('X-TT-Internal-Secret')
    return bool(expected and provided and provided == expected)


@bp.route('/internal/users/<int:auth_user_id>', methods=['DELETE'])
def delete_user(auth_user_id):
    if not _authorized():
        return jsonify({'error': 'unauthorized'}), 401

    user = User.query.filter_by(auth_user_id=auth_user_id).first()
    if not user:
        return jsonify({'status': 'not_found'}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({'status': 'deleted', 'auth_user_id': auth_user_id}), 200
