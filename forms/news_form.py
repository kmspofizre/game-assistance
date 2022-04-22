from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, FileField
from wtforms.validators import DataRequired


class NewsForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    pictures = FileField('Cartoons', validators=[DataRequired()])
    text = FileField('News text (only .docx files)', validators=[DataRequired()])
    importance = BooleanField('Is important', default=False)
    submit = SubmitField('Done')