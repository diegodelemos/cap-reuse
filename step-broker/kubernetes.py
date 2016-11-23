import pykube
import time
from six.moves.urllib.parse import urlencode

api = pykube.HTTPClient(pykube.KubeConfig.from_service_account())
api.session.verify = False


def get_jobs():
    return [job.obj for job in pykube.Job.objects(api).
            filter(namespace=pykube.all)]


def create_job(job_name, docker_img, cmd, volume, working_directory):
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
                            "command": cmd,
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
        print('Starting a new stream request to watch Jobs', flush=True)
        stream = pykube.Job.objects(api).filter(namespace=pykube.all).watch()
        for event in stream:
            print('New Job event received', flush=True)
            job = event.object
            unended_jobs = [j for j in job_db.keys()
                            if not job_db[j]['deleted']]

            if job.name in unended_jobs and event.type == 'DELETED':
                while not job_db[job.name].get('pod'):
                    time.sleep(5)
                    print('Job {} Pod still not known at {}'.format(job.name, time.clock()), flush=True)
                while job.exists():
                    print('Waiting for Job {} to be cleaned at {}'.format(job.name, time.clock()), flush=True)
                    time.sleep(5)
                print('Deleting {}\'s pod -> {} at {}'.format(job.name, job_db[job.name]['pod'].name, time.clock()), flush=True)
                job_db[job.name]['pod'].delete()
                job_db[job.name]['deleted'] = True

            elif (job.name in unended_jobs and
                  job.obj['status'].get('succeeded')):
                print('Job {} successfuly ended. Cleaning at {}'.format(job.name, time.clock()), flush=True)
                job_db[job.name]['status'] = 'succeeded'
                job.delete()

            # with the current k8s implementation this is never
            # going to happen...
            elif job.name in unended_jobs and job.obj['status'].get('failed'):
                print('Job {} failed. Cleaning...'.format(job.name), flush=True)
                job_db[job['metadata']['name']]['status'] = 'failed'
                job.delete()


def watch_pods(job_db):
    while True:
        print('Starting a new stream request to watch Pods', flush=True)
        stream = pykube.Pod.objects(api).filter(namespace=pykube.all).watch()
        for event in stream:
            print('New Pod event received', flush=True)
            pod = event.object
            unended_jobs = [j for j in job_db.keys()
                            if not job_db[j]['deleted']
                            and job_db[j]['status'] != 'failed']
            # FIX ME: watch out here, if they change the naming convention at
            # some point the following line won't work. Get job name from API.
            job_name = '-'.join(pod.name.split('-')[:-1])
            # Store existing job pod if not done yet
            if job_name in job_db and not job_db[job_name].get('pod'):
                # Store job's pod
                print('Storing {} as Job {} Pod'.format(pod.name, job_name), flush=True)
                job_db[job_name]['pod'] = pod
            # Take note of the related Pod
            if job_name in unended_jobs:
                try:
                    restarts = pod.obj['status']['containerStatuses'][0]\
                               ['restartCount']
                    exit_code = pod.obj['status']\
                                ['containerStatuses'][0]\
                                ['state'].get('terminated', {}).get('exitCode')
                    print(pod.obj['status']['containerStatuses'][0]['state'].get('terminated', {}))
                    print('Updating Pod {} restarts to {}'.format(pod.name, restarts), flush=True)
                    job_db[job_name]['restart_count'] = restarts
                    print('exit_code value {} and type {}'.format(exit_code, type(exit_code)), flush=True)
                    if restarts >= job_db[job_name]['max_restart_count'] and \
                       exit_code == 1:
                        print('Job {} reached max restarts...'.format(job_name), flush=True)
                        print('Getting {} logs at {}'.format(pod.name, time.clock()), flush=True)
                        # Remove when Pykube 0.14.0 is released
                        pod.logs = logs
                        job_db[job_name]['log'] = pod.logs(pod)
                        print('Cleaning Job {} at {}'.format(job_name, time.clock()), flush=True)
                        job_db[job_name]['status'] = 'failed'
                        job_db[job_name]['obj'].delete()

                except KeyError as e:
                    print('Skipping event because: {}'.format(e), flush=True)
                    print('Event: {}\nObject:\n{}'.format(event.type, pod.obj), flush=True)


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
