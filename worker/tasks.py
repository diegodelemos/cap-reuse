from __future__ import absolute_import

from worker.celery import app


def fibo(number):
    return number if number < 2 else \
        fibonacci(number-1) + fibonacci(number-2)


@app.task(name='tasks.fibonacci')
def fibonacci(number):
    return fibo(number)
