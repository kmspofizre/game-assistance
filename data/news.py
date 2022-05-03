from datetime import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class News(SqlAlchemyBase):
    __tablename__ = "news"

    id = sqlalchemy.Column(sqlalchemy.Integer, autoincrement=True, primary_key=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    image = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    date_of_creation = sqlalchemy.Column(sqlalchemy.String, default=str(datetime.now))
    weight = sqlalchemy.Column(sqlalchemy.Float, nullable=True)
    news_markup = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    creator = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'), nullable=True)
    creator_id = orm.relation('User')