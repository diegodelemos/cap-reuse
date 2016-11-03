import threading
from flask import Flask, abort, jsonify, request
import kubernetes

app = Flask(__name__)
app.secret_key = "mega secret key"
JOB_DB = {}


@app.route('/api/v1.0/jobs', methods=['GET'])
def get_jobs():
    return jsonify({"jobs": kubernetes.get_jobs()}), 200


@app.route('/api/v1.0/jobs', methods=['POST'])
def create_job():
    if not request.json \
       or not ('job-name' in request.json)\
       or not ('work-dir' in request.json)\
       or not ('docker-img' in request.json):
        abort(400)

    job = kubernetes.create_job(request.json['job-name'],
                                request.json['docker-img'],
                                request.json['work-dir'])

    JOB_DB[request.json['job-name']] = 'started'
    return jsonify({'job': job}), 201


@app.route('/api/v1.0/jobs/watch/<job_id>', methods=['GET'])
def get_job(job_id):
    if job_id in JOB_DB:
        return jsonify({'job': JOB_DB[job_id]}), 200
    else:
        abort(404)


if __name__ == '__main__':
    event_reader_thread = threading.Thread(target=kubernetes.watch_jobs)
    event_reader_thread.start()
    app.run(debug=True, port=5000,
            host='0.0.0.0')
