from __future__ import absolute_import

import os
import time
import worker.job_api as japi
from worker.celery import app


@app.task
def run_jobs(lines, workflow_dir, workflow_id, docker_img, cmd, jobs):
    for step, line in enumerate(lines):
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

        try:
            job_id = japi.create_job(job_spec)
            jobs[job_id] = {'status': 'started'}
            print('Job {} sucessfully created'.format(job_id))
        except Exception, e:
            print('Error while trying to create job')
            print(e)


@app.task
def get_failed_jobs(jobs):
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

            try:
                job = japi.get_job(job_id)
                jobs[job_id] = job
            except Exception, e:
                print('Error while retrieving job {}'.format(job_id))
                print(e)
                break

            retries += 1

        print('Job {id} --> {status}.'.format(id=job_id, status=job['status']))

    return [failed_job for failed_job in jobs.values()
            if failed_job['status'] == 'failed']


@app.task(name='tasks.fibonacci', ignore_result=True)
def fibonacci(docker_img, cmd, task_weight, input_file, experiment):

    # Let Celery task id be the Workflow id
    workflow_id = fibonacci.request.id

    workflow_dir = os.path.join('/data', workflow_id)
    jobs = {}

    run_jobs(input_file.split('\n'), workflow_dir,
             workflow_id, docker_img, cmd, jobs)

    failed_jobs = get_failed_jobs(jobs)

    if not failed_jobs:
        print('Workflow {} successfuly completed'.format(workflow_id))
    else:
        print('Workflow execution failed.')
        print('There was an error while executing the following jobs:')
        for job in failed_jobs:
            print('{id}\nLog\n{log}'.format(id=job['job-id'], log=job['log']))
