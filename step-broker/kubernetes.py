import pykube
from six.moves.urllib.parse import urlencode

api = pykube.HTTPClient(pykube.KubeConfig.from_service_account())
api.session.verify = False


def get_jobs():
    return [job.obj for job in pykube.Job.objects(api).
            filter(namespace=pykube.all)]


def create_job(job_name, docker_img, volume, working_directory):
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
                                },
                                {
                                    "name": "WORK_DIR",
                                    "value": working_directory
                                }
                            ],
                            "volumeMounts": [
                                {
                                    "name": volume['name'],
                                    "mountPath": "/data"
                                }
                            ]
                        },
                    ],
                    "volumes": [volume],
                    "restartPolicy": "OnFailure"
                }
            }
        }
    }

    # add better handling
    try:
        job_obj = pykube.Job(api, job)
        job_obj.create()
        return job_obj
    except pykube.exceptions.HTTPError:
        return None


def watch_jobs(job_db):
    while True:
        stream = pykube.Job.objects(api).filter(namespace=pykube.all).watch()
        for event in stream:
            job = event.object
            if event.type == 'DELETED':
                job_db[job.name]['pod'].delete()

            unended_jobs = [j for j in job_db.keys()
                            if not job_db[j]['deleted']]

            if job.name in unended_jobs:
                if job.obj['status'].get('succeeded'):
                    job_db[job.name]['status'] = 'succeeded'
                    job.delete()
                    job_db[job.name]['deleted'] = True

                # with the current k8s implementation this is never
                # going to happen...
                if job.obj['status'].get('failed'):
                    job_db[job['metadata']['name']]['status'] = 'failed'


def watch_pods(job_db):
    while True:
        stream = pykube.Pod.objects(api).filter(namespace=pykube.all).watch()
        for event in stream:
            pod = event.object
            # FIX ME: watch out here, if the change the naming convention at
            # some the following line won't work. Get job name from API.
            job_name = '-'.join(pod.name.split('-')[:-1])
            # Take note of the related Pod
            if job_db.get(job_name):
                job_db[job_name]['pod'] = pod
                unended_jobs = [j for j in job_db.keys()
                                if not job_db[j]['deleted']]

                if job_name in unended_jobs:
                    try:
                        res = pod.obj['status']['containerStatuses'][0]\
                              ['restartCount']
                        job_db[job_name]['restart_count'] = res
                        if res >= job_db[job_name]['max_restart_count']:
                            job_db[job_name]['status'] = 'failed'
                            # Remove this line when Pykube 0.14.0 is released
                            pod.logs = logs
                            # log failing right now
                            job_db[job_name]['log'] = pod.logs(pod)
                            job_db[job_name]['obj'].delete()
                            job_db[job_name]['deleted'] = True

                    except KeyError:
                        continue


# Remove this function when Pykube 0.14.0 is released
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
