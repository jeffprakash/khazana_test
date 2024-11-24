from functools import wraps
from flask_jwt_extended import get_jwt_identity
from flask import jsonify
from .models import User

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if user and user.role == 'admin':
            return fn(*args, **kwargs)
        else:
            return jsonify(message="Admin access required"), 403
    return wrapper
