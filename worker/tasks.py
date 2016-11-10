from __future__ import absolute_import

import os
import requests
from worker.celery import app


API_VERSION = 'api/v1.0'


@app.task(name='tasks.fibonacci', ignore_result=True)
def fibonacci(docker_img, task_weight, input_file, experiment):
    print '\nRunning the following workflow:\n'\
          'Docker image: {0}\n'\
          'Weight: {1}\n'\
          'Infraestructure: {3}\n'\
          'Workflow steps:\n{2}'.format(
              docker_img, task_weight, input_file, os.getenv('EXPERIMENT')
          )

    workflow_dir = os.path.join('/data', fibonacci.request.id)

    jobs_list = []
    # Call Kubernetes API to run docker img and transfer input file to the
    # volume it is going to use.
    for step, line in enumerate(input_file.split('\n')):
        step_dir = os.path.join(workflow_dir, str(step))
        if not os.path.exists(step_dir):
            os.makedirs(step_dir)
        input_file_name = os.path.join(step_dir, 'input.dat')
        print 'writing: {} \n as user with uuid: {}'.format(
            input_file_name, os.getuid()
        )
        while True:
            try:
                with open(input_file_name, 'w') as f:
                    f.write(line)
                    break
            except IOError:
                print('Retrying to write {}'.format(input_file_name))
                continue

        job_name = '{}-{}'.format(fibonacci.request.id, step)
        jobs_list.append(job_name)
        # launch a job per line
        print 'Call step broker api to launch job'

        job_spec = {
            "job-name": job_name,
            "docker-img": "diegodelemos/capreuse_fibonacci:0.1.0",
            "shared-volume": os.path.join(
                os.getenv('SHARED_VOLUME'),
                fibonacci.request.id,
                str(step)
            ),
            "permissions": os.getuid()
        }

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

    # get workflow result
    # results = get_job_state(jobs_list)

    # with open(os.path.join(workflow_dir, 'workflow_result.dat'), 'w') as f:
    #    for job, success in results.iteritems():
    #        f.write('Job {} ---> succeeded: {}\n'.format(job, success))
