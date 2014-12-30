# -*- coding: utf-8 -*-

"""
test_threethings
----------------------------------

Tests for `threethings` module.
"""

from threethings.threethings import (
    Session,
    Base,
    User,
    StatusUpdate,
)

import iso8601

import transaction

from nose.tools import *
import testing.postgresql

postgres_instance = None

def setup_module():
    create_database()

def teardown_module():
    global postgres_instance
    postgres_instance.stop()

def create_database():
    from sqlalchemy import create_engine
    global postgres_instance
    postgres_instance = testing.postgresql.Postgresql()
    engine = create_engine(postgres_instance.url())
    Session.configure(bind=engine)
    Base.metadata.create_all(engine)

def create_data():
    with transaction.manager:
        boston_user = User()
        boston_user.email_address = "boston@example.com"
        boston_user.timezone = "US/Eastern"
        Session.add(boston_user)
        singapore_user = User()
        singapore_user.email_address = "singapore@example.com"
        singapore_user.timezone = "Singapore"
        Session.add(singapore_user)
        transaction.commit()

def remove_data():
    with transaction.manager:
        for table in reversed(Base.metadata.sorted_tables):
            Session.execute(table.delete())

@with_setup(create_data, remove_data)
def test_notify_on_friday_afternoon():
    dt = iso8601.parse_date("2015-02-06T22:00:00Z")
    to_be_notified = list(User.to_notify(dt))
    eq_(len(to_be_notified), 2)

