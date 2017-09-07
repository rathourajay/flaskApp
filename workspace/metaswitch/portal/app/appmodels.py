from flask_sqlalchemy import SQLAlchemy
from models import db
from acctmodels import DeveloperAccount
"""
from msmodels import Microservice, MicroserviceFlavor
"""

class Application(db.Model):
    __tablename__ = "applications"
    id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column("name", db.String(128), index=True)
    developer_id = db.Column("developer_id", db.Integer, db.ForeignKey("developers.id"), index=True)
    description = db.Column("description", db.String(256))
    available = db.Column("available", db.Boolean)
    app_metadata = db.Column("app-metadata", db.String(8192))
    enabled = db.Column("enabled", db.Boolean)
    placement = db.Column("placement", db.String(32))

"""
class Application(db.Model):
    __tablename__ = "applications"
    id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column("name", db.String(128), index=True)
    developer_id = db.Column("developer_id", db.Integer, ForeignKey("developers.id"), index=True)
    description = db.Column("description", db.String(256))
    available = db.Column("available", db.Boolean)
    metadata = db.Column("metadata", db.String(8192))
    developer = db.relationship("DeveloperAccount", back_populates="applications")

class AppMicroservice(db.Model):
    __tablename__ = "appmicroservices"
    id = db.Column("id", db.Integer, primary_key=True)
    app_id = db.Column("app_id", db.Integer, ForeignKey("applications.id"), index=True)
    microservice_flavor = db.Column("microservice_flavor", db.Integer, ForeignKey("microserviceflavor.id"), index=True)
    application = db.relationship("Application", back_populates="microservices")

class AppExposedBinding(db.Model):
    __tablename__ = "appmicroservices"
    id = db.Column("id", db.Integer, primary_key=True)
    app_id = db.Column("app_id", db.Integer, ForeignKey("applications.id"), index=True)
    binding_id = db.Column("binding_id", db.Integer, ForeignKey("microserviceexposedbindings.id"), index=True)
    cidr = db.Column("cidr", db.String(64))
    application = db.relationship("Application", back_populates="exposed_bindings")
"""



