"""Webhooks API for Mailgun based email"""

import json
import datetime
import pytz

from pyramid.view import (
    view_config,
)
from pyramid.response import (
    Response,
)
from pyramid_mailer import get_mailer
from ..model import (
    StatusUpdate,
)
from ..email_processing import (
    send_confirm,
)

import logging

log = logging.getLogger(__name__)


def includeme(config):
    config.add_route('mailgun_landing', '/')
    config.add_route('mailgun_receiving', '/receive')
    config.scan()


@view_config(route_name='mailgun_receiving', request_method='HEAD')
def webhook_allowed(request):
    return Response(status=200)


@view_config(route_name='mailgun_receiving',
             request_method='POST',
             renderer='json')
def receive_email(request):
    mailgun_events = {}
    for i in request.params:
        try:
            mailgun_events[i] = request.params[i]
        except TypeError, e:
            log.error("------ {}".format(e))
            pass
        except:
            pass
    mailgun_events_json = json.dumps(mailgun_events)
    email_json = json.loads(mailgun_events_json)
    mailer = get_mailer(request)
    updates = process_inbound_email(mailer, email_json)
    return list(updates)


def process_inbound_email(mailer, email_json):
    log.info("------ doing a thing for {}".format(email_json['from']))
    timestamp = datetime.datetime.fromtimestamp(
        float(email_json['timestamp']), tz=pytz.UTC
    )
    author = email_json['sender']
    text = email_json['body-plain']
    html = email_json['body-html']
    subject = email_json['subject']
    # this is typed as a unicode and cant index correctly?
    # message_id = email_json['message-headers'].get('Message-Id')
    update = StatusUpdate.from_email(author, timestamp, text, html)
    send_confirm(mailer,
                 update.user,
                 #reply_to_id=reply_to,
                 reply_to_subject=subject,
                 )
    yield update
