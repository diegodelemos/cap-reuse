from __future__ import absolute_import
from celery import Celery

app = Celery('tasks',
             broker='amqp://test:1234@broker-service//',
             include=['worker.tasks'])



app.conf.update(CELERY_ACCEPT_CONTENT=['json'],
                CELERY_TASK_SERIALIZER='json')

if __name__ == '__main__':
    app.start()
