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
    config.add_route('mailgun_receiving', '/receive')
    config.scan()


@view_config(route_name='mailgun_receiving', request_method='HEAD')
def webhook_allowed(request):
    return Response(status=200)


@view_config(route_name='mailgun_receiving',
             request_method='POST',
             renderer='json')
def receive_email(request):
    mailgun_events = request.params.dict_of_lists()
    email_headers = {}
    email_header_thing = json.loads(
        request.params.getall('message-headers')[0]
    )
    for i in email_header_thing:
        email_headers[i[0]] = i[1]

    mailgun_events["parsed_message_id"] = email_headers.get(
        'Message-Id'
    ).strip('>').strip('<')

    mailer = get_mailer(request)
    updates = process_inbound_email(mailer, mailgun_events)

    return list(updates)


def process_inbound_email(mailer, email_json):
    timestamp = datetime.datetime.fromtimestamp(
        float(email_json['timestamp'][0]), tz=pytz.UTC
    )
    author = email_json['sender'][0]
    text = email_json['body-plain'][0]
    html = email_json['body-html'][0]
    subject = email_json['subject'][0]
    message_id = email_json["parsed_message_id"]
    update = StatusUpdate.from_email(author, timestamp, text, html)
    send_confirm(mailer,
                 update.user,
                 reply_to_id=message_id,
                 reply_to_subject=subject,
                 )
    yield update
