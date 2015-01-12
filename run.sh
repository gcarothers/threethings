#!/bin/sh
set -e
python setup.py develop
python heroku-run.py
