from functools import wraps
from flask import request, g


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        pass

    return decorated
