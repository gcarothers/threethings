"""Web Application"""

from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from ..model import (
    Session,
    Base,
)


def main(global_config, **settings):
    """This functions returns a Pyramid WSGI application"""

    engine = engine_from_config(settings, 'sqlalchemy.')
    Session.configure(bind=engine)
    Base.metadata.bind = engine

    config = Configurator(settings=settings)
    config.include('.mandrill', route_prefix="/mandrill")
    return config.make_wsgi_app()
