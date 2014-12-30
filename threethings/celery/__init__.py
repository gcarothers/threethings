"""Celery Task Managment Application"""

from pyramid_celery import celery_app

def main():
    celery_app.start()

if __name__ == '__main__':
    main()
