from datetime import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class Theme(SqlAlchemyBase):
    __tablename__ = 'theme'

    id = sqlalchemy.Column(sqlalchemy.Integer, autoincrement=True, primary_key=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    content = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    image = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    date_of_creation = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.now)
    genre = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('genres.id'), nullable=True)

    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    number_of_messages = sqlalchemy.Column(sqlalchemy.Integer, nullable=True, default=1)
    genre_id = orm.relation('Genres')
    user = orm.relation('User')