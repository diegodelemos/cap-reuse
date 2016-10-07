from __future__ import absolute_import
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


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('bg-form.html')

    # Calculate fibonacci in background
    if request.method == 'POST':
        try:
            docker_img = request.form['docker-img']
            task_weight = request.form['weight']
            queue = experiment_to_queue[request.form['experiment']]
            input_file = request.form['input-file']
            # send right away
            fibonacci.apply_async(
                args=[docker_img, task_weight, input_file, request.form['experiment']],
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
