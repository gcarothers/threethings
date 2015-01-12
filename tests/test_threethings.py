# -*- coding: utf-8 -*-

"""
test_threethings
----------------------------------

Tests for `threethings` module.
"""

from threethings.model import (
    Session,
    Base,
    User,
    StatusUpdate,
)

from zope.sqlalchemy import mark_changed

import iso8601
import datetime

import transaction

from nose.tools import *
import testing.postgresql

import logging

log = logging.getLogger(__name__)

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
            Session.execute("TRUNCATE TABLE {} CASCADE".format(table.name))
            mark_changed(Session.registry())
        transaction.commit()


def fake_last_notification(when):
    with transaction.manager:
        users = Session.query(User)
        for user in users:
            log.debug("Setting notification for %r to %r", user, when)
            user.last_notified = when
        transaction.commit()


@with_setup(create_data, remove_data)
def test_notify_on_friday_afternoon():
    dt = iso8601.parse_date("2015-02-06T22:00:00Z")
    to_be_notified = list(User.to_notify(dt))
    eq_(len(to_be_notified), 2)


@with_setup(create_data, remove_data)
def test_notify_on_friday_afternoon_singapore():
    dt = iso8601.parse_date("2015-02-06T08:00:00Z")
    to_be_notified = list(User.to_notify(dt))
    eq_(len(to_be_notified), 1)


@with_setup(create_data, remove_data)
def test_notify_on_friday_afternoon_after_already_sending_some():
    dt = iso8601.parse_date("2015-02-06T22:00:00Z")
    fake_last_notification(dt - datetime.timedelta(hours=4))
    to_be_notified = list(User.to_notify(dt))
    eq_(len(to_be_notified), 0)


@with_setup(create_data, remove_data)
def test_notify_on_only_those_without_status_for_week():
    dt = iso8601.parse_date("2015-02-06T22:00:00Z")

    with transaction.manager:
        user = Session.query(User).get("singapore@example.com")
        update = StatusUpdate()
        update.raw_text = "Did some work"
        update.when = dt - datetime.timedelta(hours=12)
        update.user = user
        transaction.commit()

    to_be_notified = list(User.to_notify(dt))
    eq_(len(to_be_notified), 1)
