#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

requirements = [
    'argh',
    'mandrill',
    'sqlalchemy',
    'pytz',
    'zope.sqlalchemy',
    'transaction',
    'iso8601',
    'python-dateutil',
    'pyramid',
    'pyramid_tm',
    'pyramid_mailer',
    'repoze.sendmail == 4.1',
]

test_requirements = [
    'testing.postgresql',
    'nose',
    'pyramid_debugtoolbar',
]

setup(
    name='threethings',
    version='0.1.0',
    description='Simple status updates for automated teamwork',
    long_description=readme + '\n\n' + history,
    author='Gavin Carothers',
    author_email='gavin@carothers.name',
    url='https://github.com/gcarothers/threethings',
    packages=[
        'threethings',
    ],
    package_dir={'threethings':
                 'threethings'},
    include_package_data=True,
    install_requires=requirements,
    license="BSD",
    zip_safe=False,
    keywords='threethings',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    entry_points="""
    [console_scripts]
    3things=threethings.cli:main
    [paste.app_factory]
    main = threethings.web:main
    """,
)
