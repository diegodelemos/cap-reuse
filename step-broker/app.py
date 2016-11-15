import copy
import json
import threading
from flask import Flask, abort, jsonify, request
import kubernetes

app = Flask(__name__)
app.secret_key = "mega secret key"
JOB_DB = {}


def get_config(experiment):
    with open('config_template.json', 'r') as config:
        return json.load(config)[experiment]


def filter_jobs(job_db):
    job_db_copy = copy.deepcopy(job_db)
    for job_name in job_db_copy:
        del(job_db_copy[job_name]['obj'])
        del(job_db_copy[job_name]['pod'])
        del(job_db_copy[job_name]['deleted'])

    return job_db_copy


@app.route('/api/v1.0/jobs', methods=['GET'])
def get_jobs():
    return jsonify({"jobs": filter_jobs(JOB_DB)}), 200


@app.route('/api/v1.0/k8sjobs', methods=['GET'])
def get_k8sjobs():
    return jsonify({"jobs": kubernetes.get_jobs()}), 200


@app.route('/api/v1.0/jobs', methods=['POST'])
def create_job():
    if not request.json \
       or not ('experiment') in request.json\
       or not ('job-name' in request.json)\
       or not ('docker-img' in request.json)\
       or not ('work-dir' in request.json):
        print(request.json)
        abort(400)

    print('creating job')
    experiment_config = get_config(request.json['experiment'])

    job_obj = kubernetes.create_job(request.json['job-name'],
                                    request.json['docker-img'],
                                    experiment_config['k8s_volume'],
                                    request.json['work-dir'])
    print('job_created')
    if job_obj:
        job = copy.deepcopy(request.json)
        job['status'] = 'started'
        job['restart_count'] = 0
        job['max_restart_count'] = 1
        job['obj'] = job_obj
        job['deleted'] = False
        JOB_DB[job.get('job-name')] = job
        return jsonify({'job': request.json}), 201
    else:
        return jsonify({'job': 'Could not be allocated'}), 500


@app.route('/api/v1.0/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    if job_id in JOB_DB:
        job_copy = copy.deepcopy(JOB_DB[job_id])
        del(job_copy['obj'])
        del(job_copy['pod'])
        del(job_copy['deleted'])
        return jsonify({'job': job_copy}), 200
    else:
        abort(404)


if __name__ == '__main__':
    job_event_reader_thread = threading.Thread(target=kubernetes.watch_jobs,
                                               args=(JOB_DB,))
    job_event_reader_thread.start()
    pod_event_reader_thread = threading.Thread(target=kubernetes.watch_pods,
                                               args=(JOB_DB,))
    pod_event_reader_thread.start()
    app.run(debug=True, port=5000,
            host='0.0.0.0')
