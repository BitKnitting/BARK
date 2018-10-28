import os

from flask import Flask, render_template, redirect, url_for, request, jsonify, flash
from flask_bcrypt import check_password_hash
from flask_bootstrap import Bootstrap
from flask_cors import CORS
from flask_login import LoginManager, login_user, login_required

from login_user import User, LoginForm
from sliding_door import SlidingDoor

app = Flask(__name__)
Bootstrap(app)
# Now add the class for opening and closing the door.
door = SlidingDoor()
#
# I use the Flask-CORS module so that we can access this over the router's IP.
# see https://flask-cors.readthedocs.io/en/latest/
CORS(app)

# Secret key is needed because we are using sessions...
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
login_manager = LoginManager()
login_manager.init_app(app)
# Now set the html page to be displayed.
login_manager.login_view = 'login'


#
# Function used by LoginManager to grab the user object to use.
# We don't have multiple users, so just create an instance of the
# User class.
@login_manager.user_loader
def load_user(userid):
    # user will always exist.
    user = User()
    return user


#
# Here we show the video feed as well as ability to open/close/stop the actuator that controls door movement.
@app.route('/dashboard')
@app.route('/')
@app.route('/index')
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/login', methods=('GET', 'POST'))
def login():
    form = LoginForm()
    # Person has 'submitted' the form by clicking button to check password.
    # Validators set in the LoginForm are run..if all checks...
    if form.validate_on_submit():
        user = User()
        if check_password_hash(user.hashed_password, form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash("your password is incorrect!", "error")
    return render_template('login.html', form=form)


@app.route('/get_open_close', methods=['POST'])
def get_open_close():
    action = request.get_json()
    door.do_action(action['action'])
    resp = jsonify(success=True)
    return resp


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8519, debug=True)
