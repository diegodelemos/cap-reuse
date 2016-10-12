from __future__ import absolute_import

import json
import os
from celery import Celery
import requests


celery = Celery('tasks',
                broker='amqp://test:1234@broker-service//')

celery.conf.update(CELERY_ACCEPT_CONTENT=['json'],
                   CELERY_TASK_SERIALIZER='json')


CA_CERT_PATH = '/var/run/secrets/kubernetes.io/serviceaccount/ca.crt'
TOKEN_PATH = '/var/run/secrets/kubernetes.io/serviceaccount/token'
with open(TOKEN_PATH) as tf:
    TOKEN = tf.read()

ENDPOINT = '/apis/extensions/v1beta1/namespaces/{ns}/jobs'.format(
    ns=os.getenv('EXPERIMENT')
)


def get_job_state(job_id):
    response = requests.get('{}{}/{}'.format('https://kubernetes',
                                             ENDPOINT, job_id),
                            headers={'Authorization': 'Bearer {}'.format(
                                TOKEN
                            )},
                            verify=CA_CERT_PATH)

    if response.ok:
        res_dict = json.loads(response.text)
        print res_dict
        if not (res_dict['status'].get('succeeded', False) or
                res_dict['status'].get('failed', False)):
            response = requests.get(
                '{}{}?name={}&watch=true&timeoutSeconds=10'.
                format('https://kubernetes',
                       ENDPOINT, job_id),
                headers={'Authorization': 'Bearer {}'
                         .format(
                             TOKEN
                         )},
                verify=CA_CERT_PATH)
            res_dict = json.loads(response.text)

        if res_dict['status'].get('succeeded', False):
            return True
        else:
            return False

    else:
        print 'Error while calling Kubernetes API'
        print response.text


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
                            "volumeMounts": [
                                {
                                    "name": job_name,
                                    "mountPath": "/data"
                                }
                            ]
                        }
                    ],
                    "volumes": [
                        {
                            "name": job_name,
                            "hostPath": {
                                "path": shared_dir
                            }
                        },
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


@celery.task(name='tasks.fibonacci')
def fibonacci(docker_img, task_weight, input_file, experiment):
    print 'Running docker image {0} with weight {1} and the \
    following input file on {3}: {2}'.format(
        docker_img, task_weight, input_file, os.getenv('EXPERIMENT')
    )
    shared_dir = os.path.join('/data', os.getenv('EXPERIMENT'),
                              os.getenv('HOSTNAME'),
                              fibonacci.request.id)

    jobs_ids = []
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
        jobs_ids.append(job_name)
        # launch a job per line
        create_job(job_name, docker_img, 'cap-claim', step_dir)

    results = {}
    for job in jobs_ids:
        results[job] = get_job_state(job)

    with open(os.path.join(shared_dir, 'workflow_result.dat'), 'w') as f:
        for job, success in results.iteritems():
            f.write('Job {} ---> succeeded: {}'.format(job, success))
