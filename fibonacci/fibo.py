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
       random.randint(0, 10) < 5:
        raise ArithmeticError

    print('Reading input from {}'.format(input_file))
    number_list = []
    with open(input_file, 'r') as f:
        number_list = [int(i) for i in f.read().split(',')]

    print('Calculating fibonacci for:\n{}'.format(number_list))
    result = [str(fibonacci(i)) for i in number_list]
    print('Writing result to {}'.format(output_file))
    with open(output_file, 'w') as f:
        f.write(','.join(result))
    print('End of execution.')

if __name__ == '__main__':
    working_directory = os.path.join('/data', os.getenv('WORK_DIR'))
    fibo_file(
        os.path.join(working_directory, 'input.dat'),
        os.path.join(working_directory, 'output.dat')
    )
