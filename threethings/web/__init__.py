"""Web Application"""

from pyramid.config import Configurator


def main(global_config, **settings):
    """This functions returns a Pyramid WSGI application"""
    config = Configurator(settings=settings)
    config.include('pyramid_celery')
    config.scan()
    return config.make_wsgi_app()
