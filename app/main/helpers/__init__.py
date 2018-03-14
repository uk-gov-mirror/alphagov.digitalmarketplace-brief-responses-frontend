import base64
import hashlib
import flask_login

from datetime import datetime
from functools import wraps
from flask import current_app, flash


def hash_email(email):
    m = hashlib.sha256()
    m.update(email.encode('utf-8'))

    return base64.urlsafe_b64encode(m.digest())
