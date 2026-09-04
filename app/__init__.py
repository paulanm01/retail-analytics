"""
Application factory.

The app is built inside a function instead of at module level. This lets us
create a separate app for tests, and avoids circular imports between the
app, the models and the extensions.
"""
from flask import Flask

from .config import Config
from .extensions import db, migrate


def create_app(config_class=Config):
    """Builds and returns a configured Flask application."""
    app = Flask(__name__)

    # Loads every uppercase attribute of Config into app.config
    app.config.from_object(config_class)

    # Bind the extensions to this specific app
    db.init_app(app)
    migrate.init_app(app, db)

    # Imported after db.init_app(). Without this, Flask-Migrate does not
    # see the models and generates empty migrations.
    from app import models  # noqa: F401

    # Register the blueprints (route groups)
    from app.routes.health import health_bp
    app.register_blueprint(health_bp)

    from app.routes.sales import sales_bp
    app.register_blueprint(sales_bp)

    from app.routes.products import products_bp
    app.register_blueprint(products_bp)

    from app.routes.customers import customers_bp
    app.register_blueprint(customers_bp)

    return app