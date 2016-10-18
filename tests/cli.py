#!/usr/bin/python
import base64
import click
import json
import requests


@click.command('fibo-experiment')
@click.option('--url', default='http://192.168.99.100:32313/',
              help='API endpoint')
@click.option('-d', '--docker-img', default='diegodelemos/capreuse_fibonacci',
              help='Docker image')
@click.option('-w', '--weight', default='slow', help='Docker image')
@click.option('-e', '--experiment', default='alice',
              type=click.Choice(['alice', 'atlas', 'cms', 'lhcb', 'recast']),
              help='Experiment to address the request to')
@click.option('-f', '--filename', type=click.Path(exists=True),
              help='Docker image input file')
@click.option('-n', default='1',
              type=click.IntRange(min=1, max=40),
              help='Number of requests')
def all_experiments_same_data(url, docker_img, weight, experiment, filename, n):
    with open(click.format_filename(filename)) as f:
        input_file = f.read()

    input_file_b64 = base64.encodestring(input_file.encode())

    data = {
        'docker-img': docker_img,
        'weight': weight,
        'experiment': experiment,
        'input-file': input_file_b64
    }
    json_string = json.dumps(data).encode()
    for i in range(n):
        response = requests.post(url, json=json_string)
        click.echo('Request {} of {}: {}'.format(i+1, n, response.text))

if __name__ == '__main__':
    all_experiments_same_data()
