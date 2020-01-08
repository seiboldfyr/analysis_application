
import functools

from flask import render_template, session, redirect, url_for, current_app, request, flash, Blueprint
from werkzeug.security import generate_password_hash, check_password_hash

auth_blueprint = Blueprint('auth', __name__, template_folder='templates', url_prefix='/auth')

@auth_blueprint.route('', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        if not check(username, generate_password_hash(password)):
            error = "Invalid credentials provided"
        if error is None:
            session.clear()
            session['user_logged_in'] = True
            return redirect(url_for('base.home'))

        flash(error, 'error')

    return render_template('login.html')

@auth_blueprint.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login.html'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_logged_in' not in session:
            return redirect(url_for('auth.login'))

        if not session['user_logged_in']:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view


def check(user: str, password: str) -> bool:
    """For now, this method check"""
    if user != current_app.config['APP_USERNAME']:
        return False

    if check_password_hash(password, current_app.config['APP_PASSWORD']):
        return True

    return False

#TODO: create list of passwords and usernames