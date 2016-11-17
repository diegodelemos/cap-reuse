#!/usr/bin/python
import base64
import click
import requests


@click.group(chain=True)
def cli():
    pass


@cli.command()
@click.option('--url', default='http://137.138.6.43:32331/fibonacci',
              help='API endpoint')
@click.option('-w', '--weight', default='slow', help='Docker image')
@click.option('-e', '--experiment', default='alice',
              type=click.Choice(['alice', 'atlas', 'cms', 'lhcb', 'recast']),
              help='Experiment to address the request to')
@click.option('-f', '--filename', type=click.Path(exists=True),
              help='Docker image input file')
@click.option('-n', default='1',
              type=click.IntRange(min=1, max=40),
              help='Number of requests')
def fibonacci(url, weight, experiment, filename, n):
    with open(click.format_filename(filename)) as f:
        input_file = f.read()

    input_file_b64 = base64.encodestring(input_file.encode())

    data = {
        'weight': weight,
        'experiment': experiment,
        'input-file': input_file_b64
    }

    for i in range(n):
        response = requests.post(url, json=data)
        click.echo('Request {} of {}: {}'.format(i+1, n, response.text))


@cli.command()
@click.option('--url', default='http://137.138.6.43:32331/yadage',
              help='API endpoint')
@click.option('-e', '--experiment', default='alice',
              type=click.Choice(['alice', 'atlas', 'cms', 'lhcb', 'recast']),
              help='Experiment to address the request to')
@click.option('-t', '--toplevel', default='toplevel', help='Toplevel')
@click.option('-w', '--workflow', default='workflow', help='Yadage Workflow')
@click.option('-p', '--parameters',
              default={'param1': 'value1', 'param2': 'value2'},
              help='Yadage Workflow')
@click.option('-n', default='1',
              type=click.IntRange(min=1, max=40),
              help='Number of requests')
def yadage(url, experiment, toplevel, workflow, parameters, n):
    data = {
        'experiment': experiment,
        'toplevel': toplevel,
        'workflow': workflow,
        'parameters': parameters,
    }

    for i in range(n):
        response = requests.post(url, json=data)
        click.echo('Request {} of {}: {}'.format(i+1, n, response.text))

if __name__ == '__main__':
    cli()
