from flask_wtf import FlaskForm
from wtforms import StringField, FileField, SubmitField, DateField
from wtforms.validators import DataRequired


class UserForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    birthday = DateField('Day of birth', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()])
    repeat_password = StringField('Repeat password', validators=[DataRequired()])
    submit = SubmitField('Регистрация')