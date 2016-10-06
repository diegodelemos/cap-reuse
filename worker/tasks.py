from __future__ import absolute_import

from worker.celery import app


@app.task(name='tasks.fibonacci')
def fibonacci(docker_img, task_weight, input_file):
    print 'Running docker image {0} with weight {1} and the \
    following input file on {2}'.format(
        docker_img, task_weight, input_file
    )

    # Call Kubernetes API to run docker img and transfer input file to the
    # volume it is going to use.
