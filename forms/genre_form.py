from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class GenreForm(FlaskForm):
    title = StringField('Genre name', validators=[DataRequired()])
    submit = SubmitField('Add')