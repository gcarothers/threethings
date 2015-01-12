#!/bin/sh
set -e
pip install -e .
python heroku-run.py
