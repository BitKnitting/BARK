########################################################
# flask_login revolves around a User class.  I'm not using
# a database, so there is no class inheritance from a db model.
########################################################


from flask_login import UserMixin
# Using functions from flask_bcrypt to check the hashed password, which is in the .env
# file.  The hashed password is created outside of the flask app and then stored in
# .env as an attribute that is then checked using the check_password_hash function.
# To create the password:
# >>>from flask_bcrypt import generate_password_hash
# >>> generate_password_hash('password')
# copy the output to be the value of the attribute within .env.


from flask_wtf import Form
import os

from wtforms import PasswordField
from wtforms.validators import DataRequired, Length


# "UserMixin is like adding chocolate chips to cookie dough..." it mixes in attributes
# and a method.  See "Your User Class" in the docs for flask-login


class User(UserMixin):
    hashed_password = os.getenv('HASHED_PASSWORD')
    id = 1


class LoginForm(Form):
    password = PasswordField('Password',
                             validators=[
                                 DataRequired(),
                                 Length(min=4)
                             ])
