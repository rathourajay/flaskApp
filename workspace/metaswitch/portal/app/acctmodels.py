from flask_sqlalchemy import SQLAlchemy
from models import db
import bcrypt

class DeveloperAccount(db.Model):
    __tablename__ = "developers"
    id = db.Column("id", db.Integer, primary_key=True)
    email = db.Column("email", db.String(128), unique=True, index=True)
    hash = db.Column("hash", db.String(64))
    name = db.Column("name", db.String(128))

    def __init__(self, email, password, name):
        self.email = email
        self.hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        self.name = name

    def check_password(self, password):
        return bcrypt.checkpw(password.encode("utf-8"), self.hash.encode("utf-8"))

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return "<Developer %r>" % (self.email)

