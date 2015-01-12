# -*- coding: utf-8 -*-

from sqlalchemy import (
    Column,
    Integer,
    Text,
    ForeignKey,
    DateTime,
    Boolean,
    func,
)
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relation,
)
from zope.sqlalchemy import ZopeTransactionExtension

from sqlalchemy.ext.declarative import (
    declarative_base,
)
from functools import (
    partial,
)
import pytz
import datetime

import logging

log = logging.getLogger(__name__)

Session = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

now = partial(datetime.datetime.now, tz=pytz.UTC)

FRIDAY = 5


class StatusUpdate(Base):
    __tablename__ = 'status_updates'

    id = Column(Integer, primary_key=True)
    email_address = Column(Text, ForeignKey('users.email_address'))
    status = Column(Text, nullable=False)
    when = Column(DateTime(timezone=True), nullable=False, default=now)

    @classmethod
    def updates_in_week(cls, day_in_week):
        for_year, for_week, week_day = day_in_week.isocalendar()
        q = Session.query(cls)
        q = q.filter(func.date_part('year', cls.when) == for_year)
        q = q.filter(func.date_part('week', cls.when) == for_week)
        return q

    @classmethod
    def from_email(cls, author, text, when):
        update = StatusUpdate()
        update.status = text
        update.when = when
        update.email_address = author
        Session.add(update)

    def __json__(self, request):
        return {
            'id': self.id,
            'email': self.email_address,
            'status': self.status,
            'when': self.when.isoformat()
        }


class User(Base):
    __tablename__ = 'users'

    email_address = Column(Text, primary_key=True)
    timezone = Column(Text, nullable=False)
    notifications_on = Column(Boolean, nullable=False, default=True)
    last_notified = Column(DateTime(timezone=True))

    status_updates = relation(StatusUpdate, backref='user')

    def __repr__(self):
        cls_name = self.__class__.__name__
        return "<{}('{}')>".format(cls_name, self.email_address)

    @classmethod
    def to_notify(cls, when=None, force=False):
        if when is None:
            when = now()

        all_users = Session.query(cls)
        for user in all_users:
            if user.should_be_notified(when) or force:
                yield user

    def should_be_notified(self, when):
        if self.notifications_on:
            log.debug("Set for notifications: %r", self)
            if self.is_after_expected_update_time(when):
                log.debug("last_notified: %r", self.last_notified)
                if self.last_notified is None or (when - self.last_notified >
                                                  datetime.timedelta(hours=24)):
                    if self.update_for_week(when).count() == 0:
                        return True

    def update_for_week(self, when):
        q = StatusUpdate.updates_in_week(when)
        q = q.join(self.__class__)
        q = q.filter(self.__class__.email_address == self.email_address)
        return q

    def is_after_expected_update_time(self, when):
        localtime = self.in_localtime(when)
        day = localtime.isoweekday()
        hour = localtime.hour
        log.debug("Local time for %r is %s", self, localtime)
        if day == FRIDAY and hour >= 15:
            return True
        elif day > FRIDAY:
            return True
        else:
            return False

    def in_localtime(self, when):
        assert isinstance(when, datetime.datetime)
        tz = pytz.timezone(self.timezone)
        localtime = when.astimezone(tz)
        return localtime


class WeeklySummary(object):

    def __init__(self, day_in_week=None):
        pass
