"""Command line interface for threethings"""
import os.path
import argh
import json
from argh import (
    safe_input,
)
from .model import (
    Session,
    Base,
    User,
    now,
)

from .settings_utils import(
    load_settings_from_environ,
    ENVIRON_SETTINGS_MAP,
)
from pyramid_mailer import (
    mailer_factory_from_settings,
)
from .email_processing import (
    send_notification,
    welcome_user,
)
from dateutil.parser import (
    parse,
)
import pytz
import transaction

DEFAULT_DATABASE_URL = 'postgresql://threethings@127.0.0.1:5432/threethings-dev'  # noqa
DEFAULT_MANDRILL_USERNAME = 'username'
DEFAULT_MANDRILL_TEST_KEY = 'HONFNmswdL6K075sBSk1-g'
DEFAULT_CONFIG_PATH = '~/.config/3things.json'

DEFAULT_CONFIGURATION = {
    'sqlalchemy.url': DEFAULT_DATABASE_URL,
    'mail.host': 'smtp.mandrillapp.com',
    'mail.port': 2525,
    'mail.tls': True,
}

import logging
logging.basicConfig(level=logging.DEBUG)

cli_mailer = None


def _setup_database(db_url):
    from sqlalchemy import create_engine
    engine = create_engine(db_url)
    Session.configure(bind=engine)
    Base.metadata.bind = engine


def _setup_from_config(config_path):
    from sqlalchemy import engine_from_config
    config = _load_config(config_path)
    load_settings_from_environ(config, ENVIRON_SETTINGS_MAP)
    engine = engine_from_config(config, prefix='sqlalchemy.')
    Session.configure(bind=engine)
    Base.metadata.bind = engine

    global cli_mailer
    cli_mailer = mailer_factory_from_settings(config)


def _load_config(config_path):
    path = os.path.expanduser(config_path)
    if os.path.exists(path):
        with open(path) as config_file:
            config = json.load(config_file)
    else:
        config = DEFAULT_CONFIGURATION.copy()
    return config


def _write_config(config, config_path):
    path = os.path.expanduser(config_path)
    with open(path, mode='w') as config_file:
        json.dump(config, config_file, sort_keys=True,
                  indent=4, separators=(',', ': '))


def create_schema(config=DEFAULT_CONFIG_PATH,
                  reset=False):
    _setup_from_config(config)
    if reset:
        Base.metadata.drop_all()
    Base.metadata.create_all()


def _ask_with_default(name, default):
    result = safe_input("{} [{}]: ".format(name, default))
    if result is "":
        result = default
    return result


def config(path=DEFAULT_CONFIG_PATH):
    database_url = _ask_with_default("Database URL", DEFAULT_DATABASE_URL)
    username = _ask_with_default("Mandrill Username",
                                 DEFAULT_MANDRILL_USERNAME)
    api_key = _ask_with_default("Mandrill API Key",
                                DEFAULT_MANDRILL_TEST_KEY)

    config = DEFAULT_CONFIGURATION.copy()
    config.update({
        'database.url': database_url,
        'mail.user': username,
        'mail.password': api_key,
    })
    _write_config(config,
                  config_path=path)


def add_user(email_address,
             timezone='America/Los_Angeles',
             config=DEFAULT_CONFIG_PATH):
    _setup_from_config(config)
    with transaction.manager:
        user = User()
        user.email_address = email_address
        user.timezone = timezone
        Session.add(user)
        welcome_user(cli_mailer, user)
        transaction.commit()
    yield "Added: {}".format(email_address)


def remove_user(email_address,
                config=DEFAULT_CONFIG_PATH):
    _setup_from_config(config)
    with transaction.manager:
        user = Session.query(User).get(email_address)
        if user:
            Session.delete(user)
            transaction.commit()
            yield "Removed: {}".format(email_address)
        else:
            yield "No such user: {}".format(email_address)


def send_reminders(date_override=None,
                   force=False,
                   timezone="UTC",
                   config=DEFAULT_CONFIG_PATH):
    _setup_from_config(config)
    if date_override is not None:
        when = parse(date_override)
        if when.tzinfo is None:
            zone = pytz.timezone(timezone)
            when = zone.localize(when)
    else:
        when = now()
    with transaction.manager:
        who = User.to_notify(when, force=force)
        yield "Sending notifications for {}".format(when)
        for user in who:
            yield "Sending notification for: {}".format(user.email_address)
            send_notification(cli_mailer, user, when)
        transaction.commit()


parser = argh.ArghParser()
parser.add_commands([
    add_user,
    config,
    remove_user,
    create_schema,
    send_reminders,
])


def main():
    parser.dispatch()

if __name__ == '__main__':
    main()
