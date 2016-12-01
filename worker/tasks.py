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
    jobs = {}

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
            job_id = str(response.json()['job-id'])
            jobs[job_id] = {'status': 'started'}
            print 'Job {} sucessfully created'.format(job_id)
        else:
            print 'Error while trying to create job'
            print response.text

    # Polling for retrieving workflow's steps status
    for job_id, job in jobs.items():
        retries = 0
        while job['status'] == 'started':
            timeout = 2**retries if retries < 10 else 2**9
            print(
                'Getting job {id} status in {timeout} seconds.'.format(
                    id=job_id, timeout=timeout
                )
            )
            time.sleep(timeout)
            response = requests.get(
                'http://{host}/{api}/{resource}/{id}'.format(
                    host='step-broker-service.default.svc.cluster.local',
                    api=API_VERSION,
                    resource='jobs',
                    id=job_id))

            if response.status_code == 200:
                job = response.json()['job']
                jobs[job_id] = job
            else:
                print 'Error while retrieving job {}'.format(job_id)
                print response.text

            retries += 1

        print('Job {id} --> {status}.'.format(id=job_id, status=job['status']))

    failed_jobs = [failed_job for failed_job in jobs.values()
                   if failed_job['status'] == 'failed']

    if not failed_jobs:
        print('Workflow {} successfuly completed'.format(workflow_id))
    else:
        print('Workflow execution failed.')
        print('There was an error while executing the following jobs:')
        for job in failed_jobs:
            print('{id}\nLog\n{log}'.format(id=job['job-id'], log=job['log']))
