import datetime
import sqlalchemy
from sqlalchemy import orm
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin


from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    day_of_birth = sqlalchemy.Column(sqlalchemy.DateTime, nullable=True)
    profile_picture = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    hashed_email_code = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    confirmed = sqlalchemy.Column(sqlalchemy.Boolean, nullable=True, default=False)
    special_access = sqlalchemy.Column(sqlalchemy.Boolean, nullable=True, default=False)

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def set_email_code(self, code):
        self.hashed_email_code = generate_password_hash(code)

    def check_email_code(self, code):
        return check_password_hash(self.hashed_email_code, code)