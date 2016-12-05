# -*- coding: utf-8 -*-

from sqlalchemy import (
    and_,
    Column,
    Integer,
    Text,
    ForeignKey,
    DateTime,
    Boolean,
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
from collections import (
    defaultdict,
)
import pytz

from datetime import (
    datetime,
    timedelta,
)

from mako.template import Template

import logging

log = logging.getLogger(__name__)

Session = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

now = partial(datetime.now, tz=pytz.UTC)

FRIDAY = 5


class StatusUpdate(Base):
    __tablename__ = 'status_updates'

    id = Column(Integer, primary_key=True)
    email_address = Column(Text, ForeignKey('users.email_address'))
    raw_text = Column(Text, nullable=False)
    raw_html = Column(Text, nullable=True)
    when = Column(DateTime(timezone=True), nullable=False, default=now)

    @property
    def text(self):
        from email_reply_parser import EmailReplyParser
        message = EmailReplyParser.read(self.raw_text)
        return message.reply

    @classmethod
    def updates_in_week(cls, day_in_week):
        for_year, for_week, week_day = day_in_week.isocalendar()
        # Offset to include monday till 1900 utc (11 am PST)
        # after day_in_week's isoweek
        # This is intended to catch any last minute updates
        # It's assumed users will not send in new updates on a monday
        # And assumes mail will be automatically delivered at 11 am PST
        start_date = day_in_week - timedelta(days=(week_day - 1))
        padded_start_date = start_date + timedelta(days=0, hours=17, seconds=1)
        end_date = start_date + timedelta(days=7, hours=19)

        q = Session.query(cls)
        q = q.filter(and_(
            cls.when >= padded_start_date,
            cls.when <= end_date,
        ))

        q = q.order_by(cls.when)

        return q

    @classmethod
    def from_email(cls, author, when, text, html=None):
        update = StatusUpdate()
        update.raw_text = text
        update.when = when
        update.email_address = author
        Session.add(update)
        Session.flush()
        return update

    def __json__(self, request):
        return {
            'id': self.id,
            'email': self.email_address,
            'when': self.when.isoformat()
        }


class User(Base):
    __tablename__ = 'users'

    email_address = Column(Text, primary_key=True)
    full_name = Column(Text, default="")
    timezone = Column(Text, nullable=False)
    notifications_on = Column(Boolean, nullable=False, default=True)
    last_notified = Column(DateTime(timezone=True))

    status_updates = relation(StatusUpdate, backref='user')

    def __repr__(self):
        cls_name = self.__class__.__name__
        return "<{}('{}')>".format(cls_name, self.email_address)

    @classmethod
    def all_users(cls):
        all_users = Session.query(cls)
        return all_users

    @classmethod
    def woke_users(cls):
        woke_users = Session.query(cls)
        woke_users = woke_users.filter(cls.notifications_on)
        return woke_users

    @classmethod
    def to_notify(cls, when=None, force=False):
        if when is None:
            when = now()

        all_users = Session.query(cls)
        for user in all_users:
            if force or user.should_be_notified(when):
                yield user

    def should_be_notified(self, when):
        if self.notifications_on:
            log.debug("Set for notifications: %r", self)
            if self.is_after_expected_update_time(when):
                log.debug("last_notified: %r", self.last_notified)
                if self.last_notified is None or (when - self.last_notified >
                                                  timedelta(hours=24)):
                    if self.update_for_week(when).count() == 0:
                        return True

    def update_for_week(self, when):
        when = self.in_localtime(when)
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
        assert isinstance(when, datetime)
        tz = pytz.timezone(self.timezone)
        localtime = when.astimezone(tz)
        return localtime


class WeeklySummary(object):

    SUMMARY_TEMPLATE = Template("""Hi folks,

I've collected status updates from Week ${week} of ${year}!

%for user, updates in updates_by_user.items():
${user.full_name} <${user.email_address}>:

  %for update in updates:
${update.text}
  %endfor


%endfor

%if len(users_without_updates) > 0:
Sadly I didn't get updates from ${len(users_without_updates)} people:
%for user in users_without_updates:
${user.full_name} <${user.email_address}>
%endfor
%endif

See you next Friday!
Friendly Robot
""")

    def __init__(self, when=None):
        self.when = when
        self.updates = StatusUpdate.updates_in_week(when)

        woke_users = {user for user in User.woke_users()}

        self.users_with_updates = {update.user for update in self.updates}
        self.users_without_updates = woke_users - self.users_with_updates

    def updates_by_user(self):
        results = defaultdict(list)
        for update in self.updates:
            results[update.user].append(update)
        return results

    def email_contents(self):
        for_year, for_week, week_day = self.when.isocalendar()
        return self.SUMMARY_TEMPLATE.render(**{
            'week': for_week,
            'year': for_year,
            'updates_by_user': self.updates_by_user(),
            'users_without_updates': self.users_without_updates,
        })
