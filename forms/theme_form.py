from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, FileField, SubmitField
from wtforms.validators import DataRequired
from data import db_session
from data.genres import Genres


db_session.global_init("db/content.db")
db_sess = db_session.create_session()


class ThemeForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = StringField('Short description', validators=[DataRequired()])
    content = TextAreaField('Large description', validators=[DataRequired()])
    image = FileField('Theme image')
    genre = SelectField('Theme genre', choices=list(map(lambda x: str(x.title), db_sess.query(Genres).all())))
    submit = SubmitField('Done')