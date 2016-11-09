import pykube
from six.moves.urllib.parse import urlencode

api = pykube.HTTPClient(pykube.KubeConfig.from_service_account())
api.session.verify = False

MAX_JOB_RESTART = 1


def get_jobs():
    return [job.obj for job in pykube.Job.objects(api).
            filter(namespace=pykube.all)]


def create_job(job_name, docker_img, work_dir, permissions):
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
                                    "name": "pv",
                                    "mountPath": "/data"
                                }
                            ]
                        },
                    ],
                    "securityContext": {
                        "fsGroup": permissions
                    },
                    "volumes": [
                        {
                            "name": "pv",
                            "cephfs": {
                                "monitors": [
                                    "128.142.36.227:6790",
                                    "128.142.39.77:6790",
                                    "128.142.39.144:6790"
                                ],
                                "path": work_dir,
                                "user": "k8s",
                                "secretRef": {
                                    "name": "ceph-secret"
                                },
                                "readOnly": False
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
                    if job_db[job_name]['restart_count'] > MAX_JOB_RESTART:
                        pod = pykube.Pod.objects(api).get_by_name(
                            pod['metadata']['name']
                        )
                        # Remove this line and `logs()` function when
                        # Pykube 0.14.0 is released
                        pod.logs = logs
                        job_db[job_name]['status'] = pod.logs(pod)
                        kill_job(job_name, [pod])

                except KeyError:
                    continue


def kill_job(job_name, associated_pods):
    job = pykube.Job.objects(api).get_by_name(job_name)
    job.delete()
    for pod in associated_pods:
        pod.delete()


def logs(self, container=None, pretty=None, previous=False,
         since_seconds=None, since_time=None, timestamps=False,
         tail_lines=None, limit_bytes=None):
    """
    Produces the same result as calling kubectl logs pod/<pod-name>.
    Check parameters meaning at
    http://kubernetes.io/docs/api-reference/v1/operations/,
    part 'read log of the specified Pod'. The result is plain text.
    """
    log_call = "log"
    params = {}
    if container is not None:
        params["container"] = container
    if pretty is not None:
        params["pretty"] = pretty
    if previous:
        params["previous"] = "true"
    if since_seconds is not None and since_time is None:
        params["sinceSeconds"] = int(since_seconds)
    elif since_time is not None and since_seconds is None:
        params["sinceTime"] = since_time
    if timestamps:
        params["timestamps"] = "true"
    if tail_lines is not None:
        params["tailLines"] = int(tail_lines)
    if limit_bytes is not None:
        params["limitBytes"] = int(limit_bytes)

    query_string = urlencode(params)
    log_call += "?{}".format(query_string) if query_string else ""
    kwargs = {
        "version": self.version,
        "namespace": self.namespace,
        "operation": log_call,
    }
    r = self.api.get(**self.api_kwargs(**kwargs))
    r.raise_for_status()
    return r.text
