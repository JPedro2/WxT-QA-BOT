#!/usr/bin/env bash
source /home/WxT-QA-BOT/venv/bin/activate
cd /home/WxT-QA-BOT/backEnd
gunicorn --worker-class gevent --workers 2 --bind 0.0.0.0:3002 wsgi:API_app