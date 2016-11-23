from __future__ import absolute_import

import os
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

    workflow_dir = os.path.join('/data', fibonacci.request.id)
    jobs_list = []

    for step, line in enumerate(input_file.split('\n')):
        step_dir = os.path.join(workflow_dir, str(step))
        if not os.path.exists(step_dir):
            os.makedirs(step_dir)

        input_file_name = os.path.join(step_dir, 'input.dat')

        with open(input_file_name, 'w') as f:
            f.write(line)

        job_name = '{}-{}'.format(fibonacci.request.id, step)
        jobs_list.append(job_name)
        # launch a job per line
        # Call step-broker api to launch job

        job_spec = {
            'experiment': os.getenv('EXPERIMENT'),
            'job-name': job_name,
            'docker-img': docker_img,
            'cmd': cmd,
            'env-vars': {
                'RANDOM_ERROR': '1',
                'WORK_DIR': os.path.join(
                    fibonacci.request.id,
                    str(step)
                )
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
            print 'Job {} sucessfully created'.format(job_name)
        else:
            print 'Error while trying to create job'
            print response.text
