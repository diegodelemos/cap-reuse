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


def get_job_state(job_id):
    while True:
        response = requests.get('{}{}'.format('https://kubernetes',
                                              ENDPOINT),
                                params={'watch': 'true'},
                                headers={'Authorization': 'Bearer {}'.
                                         format(
                                             TOKEN
                                         )},
                                verify=CA_CERT_PATH,
                                stream=True)

        if response.ok:
            for line in response.iter_lines():
                object = json.loads(line.decode('UTF-8')).get('object')
                if (object['metadata']['name'] == job_id
                    and (object['status'].get('succeeded')
                         or object['status'].get('failed'))):
                    res_dict = object
                    if res_dict['status'].get('succeeded'):
                        return True
                    elif res_dict['status'].get('failed'):
                        return False

        else:
            print 'Error while calling the stream API'
            print response.text
            return False


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


@app.task(name='tasks.fibonacci')
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
            f.write('Job {} ---> succeeded: {}\n'.format(job, success))
