from flask_wtf import FlaskForm
from wtforms import EmailField, SubmitField
from wtforms.validators import DataRequired


class MakeModerForm(FlaskForm):
    email = EmailField('User email', validators=[DataRequired()])
    submit = SubmitField('Done')