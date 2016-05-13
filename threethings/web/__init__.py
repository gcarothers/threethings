"""Web Application"""

from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from ..model import (
    Session,
    Base,
)

from ..settings_utils import(
    load_settings_from_environ,
    ENVIRON_SETTINGS_MAP,
)


def main(global_config, **settings):
    """This functions returns a Pyramid WSGI application"""

    load_settings_from_environ(settings, ENVIRON_SETTINGS_MAP)

    engine = engine_from_config(settings, 'database.')
    Session.configure(bind=engine)
    Base.metadata.bind = engine

    config = Configurator(settings=settings)
    config.include('pyramid_tm')
    config.include('pyramid_mailer')
    # config.include('.mandrill', route_prefix="/mandrill")
    config.include('.mailgun', route_prefix="/mailgun")
    return config.make_wsgi_app()
