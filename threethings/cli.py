"""Command line interface for threethings"""

import argh
from .model import (
    Session,
    Base,
    User,
)
import transaction

DEFAULT_DATABASE_URL='postgresql://threethings@127.0.0.1:5432/threethings-dev'


def _setup_database(db_url):
    from sqlalchemy import create_engine
    engine = create_engine(db_url)
    Session.configure(bind=engine)
    Base.metadata.bind = engine


def add_user(email_address,
             timezone='America/Los_Angeles',
             db_url=DEFAULT_DATABASE_URL):
    _setup_database(db_url)
    with transaction.manager:
        user = User()
        user.email_address = email_address
        user.timezone = timezone
        Session.add(user)
        transaction.commit()
    print("Added: {}".format(email_address))


def remove_user(email_address,
                db_url=DEFAULT_DATABASE_URL):
    _setup_database(db_url)
    with transaction.manager:
        user = Session.query(User).get(email_address)
        if user:
            Session.delete(user)
            transaction.commit()
            print("Removed: {}".format(email_address))
        else:
            print("No such user: {}".format(email_address))


parser = argh.ArghParser()
parser.add_commands([
    add_user,
    remove_user,
])

def main():
    parser.dispatch()

if __name__ == '__main__':
    main()
