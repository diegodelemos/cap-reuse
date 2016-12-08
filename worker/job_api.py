import requests

API = 'api/v1.0'
HOST = 'step-broker-service.default.svc.cluster.local'


def create_job(json_spec, api_version=API, host=HOST):
    response = requests.post(
        'http://{host}/{api}/{resource}'.format(
            host=host,
            api=api_version,
            resource='jobs'
        ),
        json=json_spec,
        headers={'content-type': 'application/json'}
    )

    if response.status_code == 201:
        job_id = str(response.json()['job-id'])
        print 'Job {} sucessfully created'.format(job_id)
        return job_id
    else:
        raise Exception(response.text)


def get_job(job_id, api_version=API, host=HOST):
    response = requests.get(
        'http://{host}/{api}/{resource}/{id}'.format(
            host=host,
            api=api_version,
            resource='jobs',
            id=job_id
        ),
    )

    if response.status_code == 200:
        return response.json()['job']
    else:
        raise Exception(response.text)
