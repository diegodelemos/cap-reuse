from __future__ import absolute_import
import base64
import json
import traceback
from flask import (Flask, abort, flash, redirect, render_template,
                   request, url_for)
from tasks import fibonacci

app = Flask(__name__)
app.secret_key = "super secret key"

experiment_to_queue = {
    'alice': 'alice-queue',
    'atlas': 'atlas-queue',
    'lhcb': 'lhcb-queue',
    'cms': 'cms-queue',
    'recast': 'recast-queue'
}


def check_input_file(input_file):
    nums = []
    if input_file.find('\n') > 0:
        lines = input_file.split('\n')
        if lines[0].strip() != 'Fibonacci pipeline':
            raise ValueError
        # lines[2] which is the docker image should
        # be checked but since this is a proof of
        # concept we suppose that it exists.
        for pos, line in enumerate(lines[2:]):
            lines[pos+2] = lines[pos+2].strip()
            tmp_nums = []
            for num in line.split(','):
                tmp_nums.append(int(num))
            nums.append(tmp_nums)
    else:
        tmp_nums = []
        for num in input_file.split(','):
            tmp_nums.append(int(num))
        nums.append(tmp_nums)

    return lines[1], '\n'.join(lines[2:])


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('bg-form.html')

    # Calculate fibonacci in background
    if request.method == 'POST':
        try:
            if request.json:
                data = json.loads(request.json)
                task_weight = data['weight']
                experiment = data['experiment']
                queue = experiment_to_queue[experiment]
                input_file = base64.decodestring(data['input-file'])
                docker_img, fib_file = check_input_file(input_file)
                # send right away

                fibonacci.apply_async(
                    args=[docker_img, task_weight, fib_file, experiment],
                    queue=queue
                )
                return 'Workflow successfully launched'
            else:
                task_weight = request.form['weight']
                experiment = request.form['experiment']
                queue = experiment_to_queue[request.form['experiment']]
                input_file = request.form['input-file']
                docker_img, fib_file = check_input_file(input_file)

                # send right away
                fibonacci.apply_async(
                    args=[docker_img, task_weight, fib_file, experiment],
                    queue=queue
                )
                flash('Workflow successfully launched')
                return redirect(url_for('index'))
        except (KeyError, ValueError):
            traceback.print_exc()
            abort(400)


if __name__ == '__main__':
    app.run(debug=True, port=5000,
            host='0.0.0.0')
