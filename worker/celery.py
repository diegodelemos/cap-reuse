from __future__ import absolute_import
from flask import Flask
from celery import Celery

app = Celery('tasks',
             broker='amqp://test:1234@broker//',
             include=['worker.tasks'])

if __name__ == '__main__':
    app.start()
