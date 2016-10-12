import os
import random

# https://www.python.org/dev/peps/pep-0255/
def fib():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b


def fibonacci(number):
    for index, fibonacci_number in enumerate(fib()):
        if index == number:
            return fibonacci_number


def fibo_file(input_file, output_file):
    if os.getenv('RANDOM_ERROR', False) and \
       random.randint(0, 10) < 2:
        raise ArithmeticError

    number_list = []
    with open(input_file, 'r') as f:
        number_list = [int(i) for i in f.read().split(',')]

    with open(output_file, 'w') as f:
        f.write(str(fibonacci(number_list[0])))
        for i in number_list[1:]:
            f.write(",{}".format(fibonacci(i)))


if __name__ == '__main__':
    fibo_file('/data/input.dat', '/data/output.dat')
