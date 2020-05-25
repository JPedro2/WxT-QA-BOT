#!/bin/sh
gunicorn --worker-tmp-dir=/dev/shm --workers=2 --threads=4 --worker-class=gthread --log-level=info --log-file=- --bind=0.0.0.0:3002 wsgi:API_app