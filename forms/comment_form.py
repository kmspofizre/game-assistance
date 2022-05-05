from flask_wtf import FlaskForm
from wtforms import TextAreaField, FileField, SubmitField
from wtforms.validators import DataRequired


class CommentForm(FlaskForm):
    comment_text = TextAreaField('Оставить комментарий', validators=[DataRequired()])
    comment_image = FileField()
    submit = SubmitField('Send')