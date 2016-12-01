from __future__ import absolute_import

import os
import time
import requests
from worker.celery import app


API_VERSION = 'api/v1.0'


@app.task(name='tasks.fibonacci', ignore_result=True)
def fibonacci(docker_img, cmd, task_weight, input_file, experiment):
    print '\nRunning the following workflow:\n'\
          'Docker image: {0}\n'\
          'Weight: {1}\n'\
          'Infraestructure: {3}\n'\
          'Workflow steps:\n{2}'.format(
              docker_img, task_weight, input_file, os.getenv('EXPERIMENT')
          )

    # Let Celery task id be the Workflow id
    workflow_id = fibonacci.request.id

    workflow_dir = os.path.join('/data', workflow_id)
    jobs_list = []

    for step, line in enumerate(input_file.split('\n')):
        step_dir = os.path.join(workflow_dir, str(step))
        if not os.path.exists(step_dir):
            os.makedirs(step_dir)

        input_file_name = os.path.join(step_dir, 'input.dat')

        # The Workflow controller writes input data for starting workflow.
        with open(input_file_name, 'w') as f:
            f.write(line)

        work_dir = os.path.join(workflow_id, str(step))

        # launch a job per line
        # Call step-broker api to launch job
        job_spec = {
            'experiment': os.getenv('EXPERIMENT'),
            'docker-img': docker_img,
            'cmd': cmd,
            'env-vars': {
                'RANDOM_ERROR': '1',
                'WORK_DIR': work_dir
            }
        }
        print(job_spec)
        response = requests.post(
            'http://{host}/{api}/{resource}'.format(
                host='step-broker-service.default.svc.cluster.local',
                api=API_VERSION,
                resource='jobs'
            ),
            json=job_spec,
            headers={'content-type': 'application/json'}
        )

        if response.status_code == 201:
            jobs_list.append(str(response.json()[u'job-id']))
            print 'Job {} sucessfully created'.format(jobs_list[-1])
        else:
            print 'Error while trying to create job'
            print response.text
