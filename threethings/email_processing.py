from pyramid_mailer.message import (
    Message,
)


NOTIFICATION_TEMPLATE = """
Hi,

Please reply with your weekly status update! Three simple things that
you did last week, and three things your planning on doing next week.

Cheers,
Friendly Robot
"""

FROM = '3things Status Updates <status-update@in.lexmachina.com>'


def send_notification(mailer, user, for_week):
    year, week_number, day_number = for_week.isocalendar()
    subject = "Status Reminder for Week {} of {}".format(week_number,
                                                         year)
    message = Message(subject=subject,
                      sender=FROM,
                      recipients=[user.email_address],
                      body=NOTIFICATION_TEMPLATE)
    mailer.send(message)
    user.last_notified = for_week
    return message


CONFIRM_TEMPLATE = """
Thanks! I've got it.

Cheers,
Friendly Robot
"""


def send_confirm(mailer, user, reply_to_id=None, reply_to_subject=None):
    headers = {}

    if reply_to_id is not None:
        headers['In-Reply-To'] = reply_to_id

    if reply_to_subject is not None:
        subject = "Re: " + reply_to_subject
    else:
        subject = "Got your update!"

    message = Message(subject=subject,
                      sender=FROM,
                      recipients=[user.email_address],
                      body=CONFIRM_TEMPLATE,
                      extra_headers=headers,
                      )
    mailer.send(message)
    return message
