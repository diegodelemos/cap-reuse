import pykube

api = pykube.HTTPClient(pykube.KubeConfig.from_service_account())


def get_jobs():
    return [job.obj for job in pykube.Job.objects(api).
            filter(namespace=pykube.all)]


def create_job(job_name, docker_img, work_dir):
    job = {
        "kind": "Job",
        "apiVersion": "batch/v1",
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
                                "path": work_dir
                            }
                        }
                    ],
                    "restartPolicy": "OnFailure"
                }
            }
        }
    }

    # add better handling
    try:
        pykube.Job(api, job).create()
        return True
    except pykube.exceptions.HTTPError:
        return False


def watch_jobs(job_db):
    while True:
        stream = pykube.Job.objects(api).filter(namespace=pykube.all).watch()
        for line in stream:
            job = line[1].obj
            if job['metadata']['name'] in job_db:
                if job['status'].get('succeeded'):
                    job_db[job['metadata']['name']]['status'] = 'succeeded'
                if job['status'].get('failed'):
                    job_db[job['metadata']['name']]['status'] = 'failed'


def watch_pods(job_db):
    while True:
        stream = pykube.Pod.objects(api).filter(namespace=pykube.all).watch()
        for line in stream:
            pod = line[1].obj
            print(pod)
            # get job name with the API
            # pod['metadata']['annotations']['kubernetes.io/created-by']['reference']['name']
            job_name = '-'.join(pod['metadata']['name'].split('-')[:-1])
            if job_name in job_db:
                print(pod)
