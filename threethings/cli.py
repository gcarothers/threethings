"""Command line interface for threethings"""
import os.path
import argh
import json
import logging
import pytz
import transaction

from argh import (
    safe_input,
)

from .model import (
    Session,
    Base,
    User,
    WeeklySummary,
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

# TODO how to set usefull values here?
DEFAULT_DATABASE_URL = 'postgresql://threethings:test123@127.0.0.1:5432/local_threethings'  # noqa
DEFAULT_MAILER_USERNAME = 'username'
DEFAULT_MAILER_TEST_KEY = 'HONFNmswdL6K075sBSk1-g'
DEFAULT_CONFIG_PATH = '~/.config/3things.json'

DEFAULT_CONFIGURATION = {
    'database.url': DEFAULT_DATABASE_URL,
    'mail.host': 'smtp.mailgun.org',
    'mail.port': 587,
    'mail.tls': True,
}

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
    engine = engine_from_config(config, prefix='database.')
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
    """Create all required tables in database"""
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
    """Interactive creation of configuration file"""
    database_url = _ask_with_default("Database URL", DEFAULT_DATABASE_URL)
    username = _ask_with_default("Mailer Username",
                                 DEFAULT_MAILER_USERNAME)
    api_key = _ask_with_default("Mailer API Key",
                                DEFAULT_MAILER_TEST_KEY)

    config = DEFAULT_CONFIGURATION.copy()
    # NOTE - mandill used 'user' Mailgun wants 'username'
    # TODO make this configureable?  or set both?
    config.update({
        'database.url': database_url,
        'mail.username': username,
        'mail.password': api_key,
    })
    _write_config(config,
                  config_path=path)


def add_user(email_address,
             full_name,
             timezone='America/Los_Angeles',
             config=DEFAULT_CONFIG_PATH):
    """Add a 3things user to be notified. Timezone sets when they should be
    notified by email."""
    _setup_from_config(config)
    with transaction.manager:
        user = User()
        user.email_address = email_address
        user.full_name = full_name
        user.timezone = timezone
        Session.add(user)
        welcome_user(cli_mailer, user)
        transaction.commit()
    yield "Added: {}".format(email_address)


def remove_user(email_address,
                config=DEFAULT_CONFIG_PATH):
    """Remove a user (and their status updates) from 3things"""
    _setup_from_config(config)
    with transaction.manager:
        user = Session.query(User).get(email_address)
        if user:
            Session.delete(user)
            transaction.commit()
            yield "Removed: {}".format(email_address)
        else:
            yield "No such user: {}".format(email_address)


def mute_user(email_address, config=DEFAULT_CONFIG_PATH):
    """Set user.notifications_on to False"""
    _setup_from_config(config)
    with transaction.manager:
        user = Session.query(User).get(email_address)
        if user:
            if user.notifications_on:
                user.notifications_on = False
                transaction.commit()
                yield "Muted: {}".format(email_address)
            else:
                yield "{} already muted".format(email_address)
        else:
            yield "No such user: {}".format(email_address)


def unmute_user(email_address, config=DEFAULT_CONFIG_PATH):
    """Set user.notifications_on to True"""
    _setup_from_config(config)
    with transaction.manager:
        user = Session.query(User).get(email_address)
        if user:
            if not user.notifications_on:
                user.notifications_on = True
                transaction.commit()
                yield "Unmuted: {}".format(email_address)
            else:
                yield "{} not muted".format(email_address)
        else:
            yield "No such user: {}".format(email_address)


def send_reminders(date_override=None,
                   force=False,
                   timezone="UTC",
                   config=DEFAULT_CONFIG_PATH):
    """Cron-able command for sending reminders to users if it's time to"""
    _setup_from_config(config)
    when = _when(date_override, timezone)
    with transaction.manager:
        who = User.to_notify(when, force=force)
        yield "Sending notifications for {}".format(when)
        for user in who:
            yield "Sending notification for: {}".format(user.email_address)
            send_notification(cli_mailer, user, when)
        transaction.commit()


def display_summary(date_override=None,
                    timezone="UTC",
                    config=DEFAULT_CONFIG_PATH):
    """Display a summary of updates for the current week"""
    _setup_from_config(config)
    when = _when(date_override, timezone)
    summary = WeeklySummary(when)
    yield "Users with updates:"
    for user in summary.users_with_updates:
        yield "* " + user.email_address
    yield "----"
    yield "Users missing updates:"
    for user in summary.users_without_updates:
        yield "* " + user.email_address


def display_updates(date_override=None,
                    timezone="UTC",
                    config=DEFAULT_CONFIG_PATH):
    """Display a copy of the normal summary email for the week"""
    _setup_from_config(config)
    when = _when(date_override, timezone)
    summary = WeeklySummary(when)
    yield summary.email_contents()


def _when(date_override, timezone):
    if date_override is not None:
        when = parse(date_override)
        if when.tzinfo is None:
            zone = pytz.timezone(timezone)
            when = zone.localize(when)
    else:
        when = now()
    return when


parser = argh.ArghParser()
parser.add_commands([
    add_user,
    config,
    remove_user,
    create_schema,
    send_reminders,
    display_summary,
    display_updates,
    mute_user,
    unmute_user,
])


def main():
    parser.dispatch()

if __name__ == '__main__':
    main()
