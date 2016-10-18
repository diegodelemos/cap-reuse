from __future__ import absolute_import
import base64
import json
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
        for line in input_file.split('\n'):
            tmp_nums = []
            for num in line.split(','):
                tmp_nums.append(int(num))
            nums.append(tmp_nums)
    else:
        tmp_nums = []
        for num in input_file.split(','):
            tmp_nums.append(int(num))
        nums.append(tmp_nums)

    return nums


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('bg-form.html')

    # Calculate fibonacci in background
    if request.method == 'POST':
        try:
            if request.json:
                data = json.loads(request.json)
                docker_img = data['docker-img']
                task_weight = data['weight']
                experiment = data['experiment']
                input_file = base64.decodestring(data['input-file'])
                check_input_file(input_file)
                # send right away
                fibonacci.apply_async(
                    args=[docker_img, task_weight, input_file, experiment],
                    queue=experiment_to_queue[experiment]
                )
                return 'Success'
            else:
                docker_img = request.form['docker-img']
                task_weight = request.form['weight']
                queue = experiment_to_queue[request.form['experiment']]
                input_file = request.form['input-file']
                check_input_file(input_file)
                # send right away
                fibonacci.apply_async(
                    args=[docker_img, task_weight, input_file,
                          request.form['experiment']],
                    queue=queue
                )
                flash(
                    'Running docker image {0} with weight {1} and the \
                    following input file on {2}: {3}'.format(
                        docker_img, task_weight, request.form['experiment'],
                        input_file
                    )
                )
                return redirect(url_for('index'))
        except (KeyError, ValueError):
            abort(400)


if __name__ == '__main__':
    app.run(debug=True, port=5000,
            host='0.0.0.0')
