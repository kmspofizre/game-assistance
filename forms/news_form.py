from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf.file import FileField


class NewsForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    pictures = FileField('Cartoons', validators=[DataRequired()])
    text = FileField('News text (only .docxs files)', validators=[DataRequired()])
    submit = SubmitField('Done')