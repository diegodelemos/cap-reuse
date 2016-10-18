from __future__ import absolute_import

import json
import os
import requests
from worker.celery import app

CA_CERT_PATH = '/var/run/secrets/kubernetes.io/serviceaccount/ca.crt'
TOKEN_PATH = '/var/run/secrets/kubernetes.io/serviceaccount/token'
with open(TOKEN_PATH) as tf:
    TOKEN = tf.read()

ENDPOINT = '/apis/extensions/v1beta1/namespaces/{ns}/jobs'.format(
    ns=os.getenv('EXPERIMENT')
)


@app.task
def get_job_state(job_list):
    jobs_status_dict = dict([(job_id, None) for job_id in job_list])
    while True:
        try:
            response = requests.get('{}{}'.format('https://kubernetes',
                                                  ENDPOINT),
                                    params={'watch': 'true'},
                                    headers={'Authorization': 'Bearer {}'.
                                             format(
                                                 TOKEN
                                             )},
                                    verify=CA_CERT_PATH,
                                    stream=True,
                                    timeout=10)

            if response.ok:
                for line in response.iter_lines():
                    object = json.loads(line.decode('UTF-8')).get('object')
                    if (object['metadata']['name'] in job_list
                        and (object['status'].get('succeeded')
                             or object['status'].get('failed'))):
                        job_id = object['metadata']['name']
                        del(job_list[job_list.index(job_id)])
                        if object['status'].get('succeeded'):
                            jobs_status_dict[job_id] = True
                        else:
                            jobs_status_dict[job_id] = False

                        if not job_list:
                            return jobs_status_dict

        except requests.exceptions.ConnectionError, e:
            if 'Read timed out.' in str(e):
                print 'Connection timed out. Retrying...'
                continue
            else:
                return False

        except Exception, e:
            return False


@app.task(ignore_result=True)
def create_job(job_name, docker_img, kubernetes_volume, shared_dir):
    job_description = {
        "kind": "Job",
        "apiVersion": "extensions/v1beta1",
        "metadata": {
            "name": job_name,
        },
        "spec": {
            "autoSelector": True,
            "template": {
                "metadata": {
                    "name": job_name,
                },
                "spec": {
                    "containers": [
                        {
                            "name": job_name,
                            "image": docker_img,
                            "env": [
                                {
                                    "name": "RANDOM_ERROR",
                                    "value": "1"
                                }
                            ],
                            "volumeMounts": [
                                {
                                    "name": job_name,
                                    "mountPath": "/data"
                                }
                            ]
                        },
                    ],
                    "volumes": [
                        {
                            "name": job_name,
                            "hostPath": {
                                "path": shared_dir
                            }
                        }
                    ],
                    "restartPolicy": "Never"
                }
            }
        }
    }

    response = requests.post('{}{}'.format('https://kubernetes', ENDPOINT),
                             json=job_description,
                             headers={'Authorization': 'Bearer {}'.format(
                                 TOKEN
                             ),
                             'content-type': 'application/json'},
                             verify=CA_CERT_PATH)

    if response.status_code == 201:
        print 'Job {} sucessfully created'.format(job_name)
    else:
        print 'Error while trying to create job'
        print response.text


@app.task(name='tasks.fibonacci', ignore_result=True)
def fibonacci(docker_img, task_weight, input_file, experiment):
    print 'Running docker image {0} with weight {1} and the \
    following input file on {3}: {2}'.format(
        docker_img, task_weight, input_file, os.getenv('EXPERIMENT')
    )

    shared_dir = os.path.join('/data', os.getenv('EXPERIMENT'),
                              os.getenv('HOSTNAME'),
                              fibonacci.request.id)

    jobs_list = []
    # Call Kubernetes API to run docker img and transfer input file to the
    # volume it is going to use.
    for step, line in enumerate(input_file.split('\n')):
        step_dir = os.path.join(shared_dir, str(step))
        if not os.path.exists(step_dir):
            os.makedirs(step_dir)
        input_file_name = os.path.join(step_dir, 'input.dat')
        with open(input_file_name, 'w') as f:
            f.write(line)

        job_name = '{}-{}'.format(fibonacci.request.id, step)
        jobs_list .append(job_name)
        # launch a job per line
        create_job(job_name, docker_img, 'cap-claim', step_dir)

    results = get_job_state(jobs_list)

    with open(os.path.join(shared_dir, 'workflow_result.dat'), 'w') as f:
        for job, success in results.iteritems():
            f.write('Job {} ---> succeeded: {}\n'.format(job, success))
