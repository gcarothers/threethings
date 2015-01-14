import os

ENVIRON_SETTINGS_MAP = {
    'DATABASE_URL': 'sqlalchemy.url',
    'SMTP_USER': 'mail.username',
    'SMTP_PASSWORD': 'mail.password',
}


def load_settings_from_environ(settings, to_load):
    for env_var, setting_name in to_load.items():
        setting_from_environ(settings, env_var, setting_name)


def setting_from_environ(settings, env_var, setting_name):
    if env_var in os.environ:
        settings[setting_name] = os.environ.get(env_var)
