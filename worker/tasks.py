from __future__ import absolute_import

import os
import requests
from worker.celery import app

CA_CERT_PATH = '/var/run/secrets/kubernetes.io/serviceaccount/ca.crt'
TOKEN_PATH = '/var/run/secrets/kubernetes.io/serviceaccount/token'
with open(TOKEN_PATH) as tf:
    TOKEN = tf.read()

CREATE_JOB_ENDPOINT = '/apis/extensions/v1beta1/namespaces/default/jobs'


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
                                    "name": kubernetes_volume,
                                    "readOnly": False,
                                    "mountPath": "/data"
                                }
                            ],
                        }
                    ],
                    "volumes": [
                        {
                            "name": kubernetes_volume,
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

    response = requests.post('{}{}'.format('https://kubernetes',
                                           CREATE_JOB_ENDPOINT),
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


@app.task(name='tasks.fibonacci')
def fibonacci(docker_img, task_weight, input_file, experiment):
    print 'Running docker image {0} with weight {1} and the \
    following input file on {3}: {2}'.format(
        docker_img, task_weight, input_file, experiment
    )

    shared_dir = os.path.join('/data', experiment, os.getenv('HOSTNAME'),
                              fibonacci.request.id)
    if not os.path.exists(shared_dir):
        os.makedirs(shared_dir)

    input_file_name = os.path.join(shared_dir, 'input.dat')
    with open(input_file_name, 'w') as f:
        f.write(input_file)

    # Call Kubernetes API to run docker img and transfer input file to the
    # volume it is going to use.
    create_job(fibonacci.request.id, docker_img,
               'cap-pv', shared_dir)
