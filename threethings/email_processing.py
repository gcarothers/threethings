import mandrill

Client = None  # mandrill.Mandrill()


def from_config(config):
    global Client
    Client = mandrill.Mandrill(config['apiKey'])


def send_notification(user, for_week):
    year, week_number, day_number = for_week.isocalendar()
    message = {
        'from_email': 'status-update@in.lexmachina.com',
        'from_name': '3things Status Updates',
        'tags': ['3things', 'status-update'],
        'to': [
            {
                'email': user.email_address,
            },
        ],
        'subject': 'Status Reminder for Week {} of {}'.format(week_number,
                                                              year),
        'text': """
Hi,

Please reply with your weekly status update! Three simple things that
you did last week, and three things your planning on doing next week.

Cheers,
Friendly Robot
""",
    }
    results = Client.messages.send(message)
    result = results[0]
    if result['status'] != 'sent':
        raise Exception("%r".format(result))
    user.last_notified = for_week
    return result
