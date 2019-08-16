#!/usr/bin/env bash
# start nginx service
service nginx start
# start celery worker
nohup python3 manage.py celery worker -l info -c 4 > ./logs/worker.log 2>&1 &
# start celery beat
nohup python3 manage.py celery beat -l info > ./logs/beat.log 2>&1 &
# start fastrunner
uwsgi --ini ./uwsgi.ini