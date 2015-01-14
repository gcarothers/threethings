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


WELCOME_MESSAGE_TEMPLATE = """
Hi there!

Welcome to the 3things status update email workflow awesomeness tool with
power features. Every week you'll get an email from me asking you to tell
me what what you've been doing this week, and what your planning on doing
next week. Just reply to that email and I'll make sure to let everyone else
on your team know what you've been up to.

You can also send me an email at any time before I remind you! I'll keep
track of all the emails you send me in a week and summarize them on Monday
morning.

See you next Friday!
Friendly Robot
"""


def welcome_user(mailer, user):
    message = Message(subject="Welcome to 3things!",
                      sender=FROM,
                      recipients=[user.email_address],
                      body=WELCOME_MESSAGE_TEMPLATE,
                      )
    mailer.send(message)
    return user
