#!/usr/bin/env bash
source ../WxT-QA-BOT/venv/bin/activate
cd ../WxT-QA-BOT/backEnd
gunicorn --worker-class gevent --workers 2 --bind 0.0.0.0:3002 wsgi:API_app