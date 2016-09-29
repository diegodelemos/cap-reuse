from __future__ import absolute_import

from worker.celery import app


# https://www.python.org/dev/peps/pep-0255/
def fib():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b


@app.task(name='tasks.fibonacci')
def fibonacci(number):
    for index, fibonacci_number in enumerate(fib()):
        if index == number:
            fibonacci_number
