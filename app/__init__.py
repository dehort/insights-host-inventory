import os
import connexion
import logging
import logging.config
import yaml

from connexion.resolver import RestyResolver
from flask import jsonify

from api.json_validators import verify_uuid_format
from api.mgmt import monitoring_blueprint
from app.config import Config
from app.models import db
from app.exceptions import InventoryException


def render_exception(exception):
    response = jsonify(exception.to_json())
    response.status_code = exception.status
    return response

from connexion.decorators.validation import RequestBodyValidator
from connexion.problem import problem
from connexion.utils import is_null
from jsonschema import ValidationError
from jsonschema.validators import validator_for


class CustomRequestBodyValidator(RequestBodyValidator):
    def validate_schema(self, data, url):
        if self.is_null_value_valid and is_null(data):
            return None

        #print("self.schema:", self.schema)
        cls = validator_for(self.schema)
        print("type(cls):", type(cls))
        print("cls:", cls)
        #cls.check_schema(self.schema)
        #errors = tuple(cls(self.schema).iter_errors(data))

        #if errors:
        #    error_list = [ e.message for e in errors ]
        #    return problem(400, 'Bad Request', {'errors': error_list}, type='validation')

        #return None

        try:
            print("self.validator:", self.validator)
            print("type(self.validator):", type(self.validator))
            print("data:", data)
            self.validator.validate(data)
        except ValidationError as exception:
            print("exception:", exception)
            print("dir(exception):", dir(exception))
            print("context:", exception.context)
            print("cause:", exception.cause)
            print("validator:", exception.validator)
            print("validator_value:", exception.validator_value)
            print("path:", exception.path)
            print("{url} validation error: {error}".format(url=url,
                          error=exception.message),
                          #extra={'validator': 'body'})
                          )
            #return problem(400, 'Bad Request', str(exception.message))
            return problem(400, 'Bad Request', str(exception))

        return None


def create_app(config_name):
    connexion_options = {"swagger_ui": True}

    # This feels like a hack but it is needed.  The logging configuration
    # needs to be setup before the flask app is initialized.
    configure_logging()

    app_config = Config(config_name)

    connexion_app = connexion.App(
        "inventory", specification_dir="./swagger/", options=connexion_options
    )

    # Read the swagger.yml file to configure the endpoints
    with open("swagger/api.spec.yaml", "rb") as fp:
        spec = yaml.safe_load(fp)

    validator_map = {
            "body": CustomRequestBodyValidator,
            }

    connexion_app.add_api(
        spec,
        validate_responses=True,
        strict_validation=True,
        base_path=app_config.api_url_path_prefix,
        validator_map=validator_map,
    )

    # Add an error handler that will convert our top level exceptions
    # into error responses
    connexion_app.add_error_handler(InventoryException, render_exception)

    flask_app = connexion_app.app

    flask_app.config["SQLALCHEMY_ECHO"] = False
    flask_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = app_config.db_uri
    flask_app.config["SQLALCHEMY_POOL_SIZE"] = app_config.db_pool_size
    flask_app.config["SQLALCHEMY_POOL_TIMEOUT"] = app_config.db_pool_timeout

    db.init_app(flask_app)

    flask_app.register_blueprint(monitoring_blueprint,
                                 url_prefix=app_config.mgmt_url_path_prefix)

    return flask_app


def configure_logging():
    env_var_name = "INVENTORY_LOGGING_CONFIG_FILE"
    log_config_file = os.getenv(env_var_name)
    if log_config_file is not None:
        # The logging module throws an odd error (KeyError) if the
        # config file is not found.  Hopefully, this makes it more clear.
        try:
            fh = open(log_config_file)
            fh.close()
        except FileNotFoundError:
            print("Error reading the logging configuration file.  "
                  "Verify the %s environment variable is set "
                  "correctly. Aborting..." % env_var_name)
            raise

        logging.config.fileConfig(fname=log_config_file)
