"""
Authentication Routes
مسیرهای احراز هویت
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.forms import RegistrationForm, LoginForm
from app.services import AuthService, StateManager
from app.extensions import limiter

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/auth')
def show_auth_page():
    """صفحه ورود/ثبت‌نام"""
    if session.get('current_user_id'):
        return redirect(url_for('chat.match'))
    return render_template('register.html', form=RegistrationForm(), login_form=LoginForm())


@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    """ثبت‌نام کاربر"""
    form = RegistrationForm()
    if form.validate_on_submit():
        user = AuthService.register_user(form.name.data, form.major.data, form.password.data)
        session['current_user_id'] = user.id
        flash('ثبت‌نام موفقیت‌آمیز بود.', 'success')
        return redirect(url_for('chat.match'))
    return render_template('register.html', form=form, login_form=LoginForm())


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """ورود کاربر"""
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = AuthService.authenticate_user(login_form.username.data, login_form.password.data)
        if user:
            session['current_user_id'] = user.id
            flash('خوش آمدید.', 'success')
            return redirect(url_for('chat.match'))
        else:
            flash('نام کاربری یا رمز عبور اشتباه است.', 'error')
    return render_template('register.html', form=RegistrationForm(), login_form=login_form)


@auth_bp.route('/logout')
def logout():
    """خروج کاربر"""
    user_id = session.get('current_user_id')
    if user_id:
        StateManager.set_offline(user_id)
    session.pop('current_user_id', None)
    flash('خروج موفقیت‌آمیز.', 'info')
    return redirect(url_for('auth.show_auth_page'))