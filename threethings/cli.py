"""Command line interface for threethings"""
import os.path
import argh
import json
from argh import (
    arg,
    confirm,
    safe_input,
)
from .model import (
    Session,
    Base,
    User,
    now,
)
from .email import (
    send_notification,
)
from dateutil.parser import (
    parse,
)
import pytz
import transaction

DEFAULT_DATABASE_URL='postgresql://threethings@127.0.0.1:5432/threethings-dev'
DEFAULT_CONFIG_PATH='~/.config/3things.json'


def _setup_database(db_url):
    from sqlalchemy import create_engine
    engine = create_engine(db_url)
    Session.configure(bind=engine)
    Base.metadata.bind = engine


def _setup_from_config(config_path):
    from sqlalchemy import engine_from_config
    config = _load_config(config_path)
    engine = engine_from_config(config['database'], prefix='')
    Session.configure(bind=engine)
    Base.metadata.bind = engine


def _load_config(config_path):
    path = os.path.expanduser(config_path)
    with open(path) as config_file:
        config = json.load(config_file)
    return config

def _write_config(config, config_path):
    path = os.path.expanduser(config_path)
    with open(path, mode='w') as config_file:
        json.dump(config, config_file)


def create_schema(config=DEFAULT_CONFIG_PATH):
    _setup_from_config(config)
    Base.metadata.create_all()


def config(path=DEFAULT_CONFIG_PATH):
    database_url = safe_input("Database URL [{}]: ".format(DEFAULT_DATABASE_URL))
    if database_url is "":
        database_url = DEFAULT_DATABASE_URL

    config = {
        'database': {
            'url': database_url,
        },
    }
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
        transaction.commit()
    print("Added: {}".format(email_address))


def remove_user(email_address,
                config=DEFAULT_CONFIG_PATH):
    _setup_from_config(config)
    with transaction.manager:
        user = Session.query(User).get(email_address)
        if user:
            Session.delete(user)
            transaction.commit()
            print("Removed: {}".format(email_address))
        else:
            print("No such user: {}".format(email_address))


def send_reminders(date_override=None,
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
    who = User.to_notify(when)
    print("Sending notifications for {}".format(when))
    for user in who:
        print("Sending notification for: {}".format(user.email_address))
        send_notification(user, when)


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
