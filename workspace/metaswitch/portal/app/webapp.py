import os
import time
import sys, traceback
import logging
import flask, httplib
from optparse import OptionParser
from flask import Flask, request, Response, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import TextField, PasswordField, TextAreaField, BooleanField, SelectField, HiddenField, FileField, validators
from models import db
from sqlalchemy import and_
from acctmodels import DeveloperAccount
from appmodels import Application
from msmodels import Microservice
import iaampolicy

ens = Flask(__name__)
ens.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/test.db"
ens.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
ens.config["UPLOAD_FOLDER"] = "msimages"
db.app = ens
db.init_app(ens)

login_manager = LoginManager()
login_manager.init_app(ens)
login_manager.login_view = "login"

ALLOWED_EXTENSIONS = set(["png", "jpg", "jpeg"])

def upload_image(image):
    if image and image.filename != "":
        if "." in image.filename and image.filename.rsplit(".", 1)[1] in ALLOWED_EXTENSIONS:
            filename = secure_filename(image.filename)
            image.save(os.path.join(ens.config["UPLOAD_FOLDER"], filename))
            return filename

    return ""

@login_manager.user_loader
def load_user(id):
    try:
        return DeveloperAccount.query.get(int(id))
    except:
        return None

class LoginForm(FlaskForm):
    email = TextField("Email address", [validators.input_required("Please enter your email address.")])
    password = PasswordField("Password", [validators.input_required("Please enter your password.")])

class SignupForm(FlaskForm):
    email = TextField("Email address", [validators.input_required("Please enter your email address.")])
    password = PasswordField("Password", [validators.input_required("Please enter a password.")])
    name = TextField("Name", [validators.Required("Please enter your name.")])

class ConsoleApplicationForm(FlaskForm):
    id = HiddenField("id", [validators.input_required()])
    enabled = BooleanField("Enabled");
    placement = SelectField("Placement", choices=[("low-latency", "Low latency"), ("low-cost", "Low cost/higher latency")])

class DevApplicationForm(FlaskForm):
    id = HiddenField("id", [validators.optional()])
    name = TextField("Application name", [validators.input_required("Please enter a name for the application")])
    description = TextAreaField("Description", [validators.optional()])
    metadata = TextAreaField("Meta-data", [validators.input_required("Please enter JSON formatted meta-data for the application")])
    available = BooleanField("Available")

class DevMicroserviceForm(FlaskForm):
    id = HiddenField("id", [validators.optional()])
    name = TextField("Microservice name", [validators.input_required("Please enter a name for the microservice")])
    description = TextAreaField("Description", [validators.optional()])
    metadata = TextAreaField("Meta-data", [validators.input_required("Please enter JSON formatted meta-data for the microservice")])
    categories = TextField("Categories", [validators.optional()])
    available = BooleanField("Available")
    public = BooleanField("Public")
    image = FileField("Marketplace image", [validators.optional()])

@ens.route("/", methods=["GET"])
@ens.route("/index", methods=["GET"])
def root():
    """ Display the welcome page with links to sign up or login."""
    return render_template("index.html")

@ens.route("/devresources", methods=["GET"])
def devresources():
    return render_template("devresources.html");

@ens.route("/locations", methods=["GET"])
def locations():
    return render_template("locations.html");

@ens.route("/pricing", methods=["GET"])
def prices():
    return render_template("pricing.html");

@ens.route("/signup", methods=["GET","POST"])
def signup():
    """For GET requests, display the signup form.  For POST requests create
    a user in the database"""
    form = SignupForm()
    if form.validate_on_submit():
        email = form.email.data

        # Check that account doesn't already exist.
        if DeveloperAccount.query.filter_by(email=email).first():
            flask.flash("Developer account %s exists" % email)
            return flask.redirect(flask.url_for(".signup", _external=True))

        devaccount = DeveloperAccount(email, form.password.data, form.name.data)
        db.session.add(devaccount)
        db.session.commit()
        login_user(devaccount)
        flask.flash("Developer account created for %s" % devaccount.name)
        return flask.redirect(flask.url_for("console"))

    return render_template("signup.html", form=form)

@ens.route("/login", methods=["GET", "POST"])
def login():
    """For GET requests, display the login form. For POSTS, login the current user
    by processing the form."""
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data

        # Find account and check password.
        devaccount = DeveloperAccount.query.filter_by(email=email).first()
        if devaccount and devaccount.check_password(form.password.data):
            login_user(devaccount)
            flask.flash("%s logged in successfully" % devaccount.name)
            return flask.redirect(flask.url_for("console"))

    return render_template("login.html", form=form)

@ens.route("/logout", methods=["GET"])
@login_required
def logout():
    """Logout the current user."""
    logout_user()
    return flask.redirect("/")

@ens.route("/marketplace", methods=["GET", "POST"])
def marketplace():
    filter = request.args.get("filter")

    if not filter:
        microservices = Microservice.query.filter(Microservice.public).all()
    else:
        microservices = Microservice.query.filter(and_(Microservice.public, Microservice.categories.like("%%%s%%" % filter))).all()

    return render_template("marketplace.html", microservices=microservices)

@ens.route("/console", methods=["GET"])
@login_required
def console():
    """ Render the default logged in view for a developer, currently their
    list of live applications (if any)"""
    applications = Application.query.filter_by(developer_id=current_user.id).all()
    return render_template("console.html", applications=applications)

@ens.route("/console/application", methods=["GET", "POST"])
def console_application():
    form = ConsoleApplicationForm()

    if form.validate_on_submit():
        application = Application.query.filter_by(id=form.id.data).first()
        if not application:
            return Response(status=httplib.NOT_FOUND)

        # Update with fields from form
        application.enabled = form.enabled.data
        application.placement = form.placement.data

        # Write the updates to the database
        db.session.add(application)
        db.session.commit()

        # Push updates to the IAAM policy nodes
        pm.update_app(application.name, application.enabled, application.placement)

        # Redirect back to the main developer screen
        return flask.redirect(flask.url_for("console"))
    else:
        app_id = request.args.get("id")
        application = Application.query.filter_by(id=app_id).first()
        if not application:
            return Response(status=httplib.NOT_FOUND)

        form = ConsoleApplicationForm(id=application.id,enabled=application.enabled,placement=application.placement)

        return render_template("console_application.html",name=application.name,form=form)

@ens.route("/developer", methods=["GET"])
@login_required
def developer():
    """ Render the default developer portal page, showing lists of applications
    and microservices owned by the developer """
    # Find all applications owned by the developer
    applications = Application.query.filter_by(developer_id=current_user.id).all()
    microservices = Microservice.query.filter_by(developer_id=current_user.id).all()
    return render_template("developer.html",applications=applications,microservices=microservices)

@ens.route("/developer/application", methods=["GET", "POST"])
@login_required
def developer_application():
    app_id = request.args.get("id")
    if app_id and request.method == "GET":
        # Edit request, so find the application
        application = Application.query.filter_by(id=app_id).first()
        if not application:
            return Response(status=httplib.NOT_FOUND)

        # Create a form initialized from the object and render the template as an edit
        form = DevApplicationForm(id=application.id,name=application.name,description=application.description,metadata=application.app_metadata,available=application.available)
        return render_template("dev_application.html",action="Update",form=form)
    else:
        # Add request or form submission
        form = DevApplicationForm()

        if form.validate_on_submit():
            # Form submission so add/update the application.
            app_id = form.id.data
            application = Application.query.filter_by(id=app_id).first()
            if not application:
                application = Application()
                application.developer_id = current_user.id
                application.enabled = False
                application.placement = "low-cost"

            # Update with fields from form
            application.name = form.name.data
            application.description = form.description.data
            application.app_metadata = form.metadata.data
            application.available = form.available.data

            # Write the updates to the database
            db.session.add(application)
            db.session.commit()

            # Redirect back to the main developer screen
            return flask.redirect(flask.url_for("developer"))

        # Render the form as an add
        return render_template("dev_application.html",action="Add",form=form)

@ens.route("/developer/microservice", methods=["GET", "POST"])
@login_required
def developer_microservice():
    ms_id = request.args.get("id")
    if ms_id and request.method == "GET":
        # Edit request, so find the microservice
        microservice = Microservice.query.filter_by(id=ms_id).first()
        if not microservice:
            return Response(status=httplib.NOT_FOUND)

        # Create a form initialized from the object and render the template as an edit
        form = DevMicroserviceForm(id=microservice.id,
                                   name=microservice.name,
                                   description=microservice.description,
                                   metadata=microservice.ms_metadata,
                                   categories=microservice.categories,
                                   image=microservice.image,
                                   available=microservice.available,
                                   public=microservice.public)
        return render_template("dev_microservice.html",action="Update",form=form)
    else:
        # Add request or form submission
        form = DevMicroserviceForm()

        if form.validate_on_submit():
            # Form submission so add/update the application.
            ms_id = form.id.data
            microservice = Microservice.query.filter_by(id=ms_id).first()
            if not microservice:
                microservice = Microservice()
                microservice.developer_id = current_user.id
                microservice.developer_name = DeveloperAccount.query.filter_by(id=current_user.id).first().name

            # Update with fields from form
            microservice.name = form.name.data
            microservice.description = form.description.data
            microservice.ms_metadata = form.metadata.data
            microservice.available = form.available.data
            microservice.public = form.public.data
            if form.image.data:
                microservice.image = upload_image(request.files["image"])
            microservice.categories = form.categories.data

            # Write the updates to the database
            db.session.add(microservice)
            db.session.commit()

            # Redirect back to the main developer screen
            return flask.redirect(flask.url_for("developer"))

        # Render the form as an add
        return render_template("dev_microservice.html",action="Add",form=form)

@ens.route('/msimages/<filename>')
def send_image(filename):
    return send_from_directory(ens.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    # Setup the command line arguments.
    optp = OptionParser()

    # Output verbosity options.
    optp.add_option("-q", "--quiet", help="set logging to ERROR",
                    action="store_const", dest="loglevel",
                    const=logging.ERROR, default=logging.INFO)
    optp.add_option("-d", "--debug", help="set logging to DEBUG",
                    action="store_const", dest="loglevel",
                    const=logging.DEBUG, default=logging.INFO)
    optp.add_option("-v", "--verbose", help="set logging to COMM",
                    action="store_const", dest="loglevel",
                    const=5, default=logging.INFO)

    opts, args = optp.parse_args()

    # Setup logging.
    logging.basicConfig(level=opts.loglevel,
                        format="%(asctime)-15s %(levelname)-8s %(message)s")

    # Enable Flask debug logs if required
    if opts.loglevel == logging.DEBUG:
        ens.debug = True

    # Set up secret key
    ens.secret_key = "\xe5\x7fz\xc2\xb8\x99\xc3\xa8\xfc\xd8.J\xc6v[\x95m\xdb\x0e|X\x01\x81\xe1"

    # Create tables etc. in database
    db.create_all()

    pm = iaampolicy.Manager("/home/ubuntu/ens/policy/app-policy.db")

    # Start the Flask web server (HTTPS)
    # SERVER_PORT = 443
    #context = ("certs/<>.crt", "certs/<>.key")
    #ens.run(host="0.0.0.0", port=SERVER_PORT, ssl_context=context, threaded=True)

    # Start the Flask web server (HTTP)
    SERVER_PORT=80
    ens.run(host="0.0.0.0", port=SERVER_PORT, threaded=True)

