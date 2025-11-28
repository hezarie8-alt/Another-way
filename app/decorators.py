"""
Custom Decorators
دکوراتورهای سفارشی
"""

from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(f):
    """دکوراتور برای محافظت از صفحات که نیاز به ورود دارند"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'current_user_id' not in session:
            flash('برای دسترسی به این صفحه باید وارد شوید.', 'info')
            return redirect(url_for('auth.show_auth_page'))
        return f(*args, **kwargs)
    return decorated_function