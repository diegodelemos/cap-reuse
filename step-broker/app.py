import copy
import threading
from flask import Flask, abort, jsonify, request
import kubernetes

app = Flask(__name__)
app.secret_key = "mega secret key"
JOB_DB = {}


def filter_jobs(job_db):
    job_db_copy = copy.deepcopy(job_db)
    for job_name in job_db_copy:
        del(job_db_copy[job_name]['json_obj'])
        del(job_db_copy[job_name]['pod'])

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
       or not ('job-name' in request.json)\
       or not ('shared-volume' in request.json)\
       or not ('permissions' in request.json)\
       or not ('docker-img' in request.json):
        print(request.json)
        abort(400)

    job_obj = kubernetes.create_job(request.json['job-name'],
                                    request.json['docker-img'],
                                    request.json['shared-volume'],
                                    int(request.json['permissions']))
    if job_obj:
        job = request.json
        job['status'] = 'started'
        job['restart_count'] = 0
        job['json_obj'] = job_obj
        JOB_DB[job.get('job-name')] = job
        return jsonify({'job': request.json}), 201
    else:
        return jsonify({'job': 'Could not be allocated'}), 500


@app.route('/api/v1.0/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    if job_id in JOB_DB:
        job_copy = copy.deepcopy(JOB_DB[job_id])
        del(job_copy['json_obj'])
        del(job_copy['pod'])
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
