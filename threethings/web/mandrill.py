"""Webhooks API for Mandrill based email"""

import json
import datetime
import pytz

from pyramid.view import (
    view_config,
)
from pyramid.response import (
    Response,
)
from ..model import (
    StatusUpdate,
)

import logging

log = logging.getLogger(__name__)


def includeme(config):
    config.add_route('mandril_landing', '/')
    config.add_route('mandrill_receiving', '/receive')
    config.scan()


@view_config(route_name='mandrill_receiving', request_method='HEAD')
def webhook_allowed(request):
    return Response(status=200)


@view_config(route_name='mandrill_receiving',
             request_method='POST',
             renderer='json')
def receive_email(request):
    mandrill_events = request.params['mandrill_events']
    email_json = json.loads(mandrill_events)
    updates = process_inbound_email(email_json)
    return list(updates)


def process_inbound_email(email_json):
    """Based on http://help.mandrill.com/entries/22092308-What-is-the-format-of-inbound-email-webhooks-
    process the incoming email."""
    for event in email_json:
        if event['event'] != 'inbound':
            raise ValueError('Unexpected event: {}'.format(event['event']))
        timestamp = datetime.datetime.fromtimestamp(event['ts'], tz=pytz.UTC)
        msg = event['msg']
        author = msg['from_email']
        text = msg['text']
        html = msg['html']
        update = StatusUpdate.from_email(author, timestamp, text, html)
        yield update
