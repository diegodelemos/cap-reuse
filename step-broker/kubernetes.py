import pykube

api = pykube.HTTPClient(pykube.KubeConfig.from_service_account())
api.session.verify = False

MAX_JOB_RESTART = 1


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
            job_name = '-'.join(pod['metadata']['name'].split('-')[:-1])
            if job_name in [j for j in job_db.keys()
                            if job_db[j]['status'] == 'started']:
                try:
                    n_res \
                        = pod['status']['containerStatuses'][0]['restartCount']
                    job_db[job_name]['restart_count'] = n_res
                except KeyError:
                    continue

                if job_db[job_name]['restart_count'] > MAX_JOB_RESTART:
                    job_db[job_name]['status'] = pod['status']\
                                                 ['containerStatuses'][0]\
                                                 ['lastState']['terminated']\
                                                 ['message']
                    kill_job(job_name)


def kill_job(job_name):
    job = pykube.Job.objects(api).get_by_name(
        job_name
    )
    job.delete()
    # it is not deleting the associated Pod.
    # Once a job is deleted all its resources
    # should be deleted by k8s also.
    # FIX ME
