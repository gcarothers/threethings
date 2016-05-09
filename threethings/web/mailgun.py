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
    config.add_route('mailgun_receiving', '/receive2')
    config.scan()


@view_config(route_name='mailgun_receiving', request_method='HEAD')
def webhook_allowed(request):
    return Response(status=200)


@view_config(route_name='mailgun_receiving',
             request_method='POST',
             renderer='json')
def receive_email(request):
    mailgun_events = request.params['mailgun_events']
    email_json = json.loads(mailgun_events)
    mailer = get_mailer(request)
    updates = process_inbound_email(mailer, email_json)
    return list(updates)


def process_inbound_email(mailer, email_json):
    """Based on http://goo.gl/vyeI69 process the incoming email."""
    for event in email_json:
        if event['event'] != 'inbound':
            raise ValueError('Unexpected event: {}'.format(event['event']))
        timestamp = datetime.datetime.fromtimestamp(event['ts'], tz=pytz.UTC)
        msg = event['msg']
        author = msg['from_email']
        text = msg['text']
        html = msg['html']
        subject = msg['subject']
        message_id = msg['headers'].get('Message-Id')
        update = StatusUpdate.from_email(author, timestamp, text, html)
        send_confirm(mailer,
                     update.user,
                     reply_to_id=message_id,
                     reply_to_subject=subject,
                     )
        yield update
