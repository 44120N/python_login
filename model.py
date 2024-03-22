from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.String(255), primary_key=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    level = db.Column(db.Enum('admin', 'operator', 'player'), nullable=False)

    def __init__(self, id, name, username, password, level):
        self.id = id
        self.name = name
        self.username = username
        self.password = password
        self.level = level