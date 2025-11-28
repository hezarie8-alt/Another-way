"""
Main Routes
مسیرهای اصلی برنامه
"""

from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """صفحه اصلی"""
    return render_template('index.html')


@main_bp.route('/about')
def about():
    """صفحه درباره ما"""
    return render_template('about.html')