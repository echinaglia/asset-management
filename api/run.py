import os

from flask import Flask, g, jsonify
from flask_cors import CORS
from werkzeug.exceptions import InternalServerError, NotFound
from stock_models.utils.io_utils import set_session, commit_session


from app.views.private.api import private_bp
from app.views.public.api import public_bp


def make_app():
    environment = os.environ.get("APPLICATION_ENV", "development")

    application = Flask(__name__)
    application.config.from_object("config.default")
    application.config.from_object(f"config.{environment}")

    # TODO: CORS on production only from origin on AWS
    CORS(application)

    application.register_blueprint(public_bp)
    application.register_blueprint(private_bp)
    database(application)

    @application.before_request
    def log_requests():
        # TODO: Log
        pass

    @application.errorhandler(NotFound)
    def handle_404(_):
        return jsonify({"message": "The URL requested doesn't exist"}), 404

    @application.errorhandler(InternalServerError)
    def handle_500(_):
        return jsonify({"message": "Internal Server Error"}), 500

    return application


def database(application):
    set_session(application.config['SQLALCHEMY_DATABASE_URI'])

    @application.teardown_appcontext
    def finish_session(exception=None):
        commit_session(exception)
        if hasattr(g, "tasks"):
            for task in g.tasks:
                task.delay()


if __name__ == "__main__":
    app = make_app()
    app.run(debug=True)
