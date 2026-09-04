"""
Flask extensions, created here without being bound to an app.

They live in their own file to avoid circular imports: the models need `db`,
and the app needs the models. With both importing from here, there is no loop.
They are bound to a specific app inside create_app().
"""
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()      # ORM: maps Python classes to SQL tables
migrate = Migrate()    # manages database schema changes