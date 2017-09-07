from flask_sqlalchemy import SQLAlchemy
from models import db

class Microservice(db.Model):
    __tablename__ = "microservices"
    id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column("name", db.String(128), index=True)
    developer_id = db.Column("developer_id", db.Integer, db.ForeignKey("developers.id"), index=True)
    description = db.Column("description", db.String(2048))
    public = db.Column("public", db.Boolean)
    available = db.Column("available", db.Boolean)
    image = db.Column("image", db.String(128))
    categories = db.Column("categories", db.String(128))
    ms_metadata = db.Column("ms-metadata", db.String(2048))
    developer_name = db.Column("developer_name", db.String(128))

"""
class Microservice(db.Model):
    __tablename__ = "microservices"
    id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column("name", db.String(128), index=True)
    developer_id = db.Column("developer_id", db.Integer, ForeignKey("developers.id"), index=True)
    description = db.Column("description", db.String(2048))
    public = db.Column("public", db.Boolean)
    available = db.Column("available", db.Boolean)
    tenancy = db.Column("tenancy", db.Integer)
    developer = db.relationship("DeveloperAccount", back_populates="microservices")

class MicroserviceExposedBinding:
    __tablename__ = "microserviceexposedbindings"
    id = db.Column("id", db.Integer, primary_key=True)
    microservice_id = db.Column("microservice_id", db.Integer, ForeignKey("microservices.id"), index=True)
    binding_id = db.Column("binding_id"), db.Integer, ForeignKey("workloadbindings.id"))
    microservice = db.relationship("Microservice", back_populates="exposed_bindings")
    binding = db.relationship("WorkloadBinding")

class MicroserviceFlavor(db.Model):
    __tablename__ = "microserviceflavors"
    id = db.Column("id", db.Integer, primary_key=True)
    microservice_id = db.Column("microservice_id", db.Integer, ForeignKey("microservices.id"), index=True)
    name = db.Column("name", db.String(32))
    description = db.Column("description", db.String(512))
    max_tenants = db.Column("max_tenants", db.Integer)
    max_load_per_tenant = db.Column("max_load_per_tenant", db.Integer)
    rtu_connect_time = db.Column("rtu_connect_time", db.)
    rtu_request = db.Column("rtu_request",
    microservice = db.relationship("Microservice", back_populates="flavors")

class Workload(db.Model):
    __tablename__ = "workloads"
    id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column("name", db.String(128), unique=True, index=True)
    microservice_id = db.Column("microservice_id", db.Integer, ForeignKey("microservices.id"), index=True)
    image = db.Column("image", db.String(128))
    microservice = db.relationship("Microservice", back_populates="workloads")

class WorkloadBinding(db.Model):
    __tablename__ = "workloadbindings"
    id = db.Column("id", db.Integer, primary_key=True)
    workload_id = db.Column("workload_id", db.Integer, ForeignKey("workloads.id"), index=True)
    name = db.Column("name", db.String(64))
    binding_type = db.Column("binding_type", db.Integer)
    fn = db.Column("fn", db.String(64))
    scheduler = db.Column("scheduler", db.Integer)
    port = db.Column("port", db.Integer)
    workload = db.relationship("Workload", back_populates="bindings")

class WorkloadFlavor(db.Model):
    __tablename__ = "workloadflavors"
    id = db.Column("id", db.Integer, primary_key=True)
    workload_id = db.Column("workload_id", db.Integer, ForeignKey("workloads.id"), index=True)
    flavor_id = db.Column("flavor_id", db.Integer, ForeignKey("microserviceflavors.id") index=True)
    slices = db.Column("slices", db.Integer)
    bandwidth = db.Column("bandwidth", db.Integer)
    block_storage = db.Column("block_storage", db.Integer)
    kv_storage = db.Column("kv_storage", db.Integer)
    workload = db.relationship("Workload", back_populates="flavors")
    flavor = db.relationship("MicroserviceFlavor")
"""







