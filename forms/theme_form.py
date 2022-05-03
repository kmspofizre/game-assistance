from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, FileField, SubmitField
from wtforms.validators import DataRequired


class ThemeForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = StringField('Short description', validators=[DataRequired()])
    content = TextAreaField('Large description', validators=[DataRequired()])
    image = FileField('Theme image')
    genre = SelectField('Theme genre', choices=['RPG', 'Shooters', 'Souls-Like', 'Fighting'])
    submit = SubmitField('Done')