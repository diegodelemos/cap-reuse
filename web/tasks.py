from __future__ import absolute_import

from celery import Celery

celery = Celery('tasks',
                broker='amqp://test:1234@rabbit//')


def fibo(number):
    return number if number < 2 else \
        fibonacci(number-1) + fibonacci(number-2)


@celery.task(name='tasks.fibonacci')
def fibonacci(number):
    return fibo(number)
