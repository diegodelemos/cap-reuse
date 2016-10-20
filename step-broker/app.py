from flask import Flask, abort, jsonify, request
import pykube

app = Flask(__name__)
app.secret_key = "mega secret key"

jobs = []

api = pykube.HTTPClient(pykube.KubeConfig.from_service_account())


@app.route('/api/v1.0/jobs', methods=['GET'])
def get_jobs():
    jobs = [job.obj for job in pykube.Job.objects(api).
            filter(namespace=pykube.all)]
    return jsonify({"jobs": jobs}), 200


@app.route('/api/v1.0/jobs', methods=['POST'])
def create_job():
    if not request.json \
       or not ('job-name' in request.json)\
       or not ('work-dir' in request.json)\
       or not ('docker-img' in request.json):
        abort(400)

    job = {
        "kind": "Job",
        "apiVersion": "batch/v1",
        "metadata": {
            "name": request.json['job-name'],
        },
        "spec": {
            "autoSelector": True,
            "template": {
                "metadata": {
                    "name": request.json['job-name'],
                },
                "spec": {
                    "containers": [
                        {
                            "name": request.json['job-name'],
                            "image": request.json['docker-img'],
                            "env": [
                                {
                                    "name": "RANDOM_ERROR",
                                    "value": "1"
                                }
                            ],
                            "volumeMounts": [
                                {
                                    "name": request.json['job-name'],
                                    "mountPath": "/data"
                                }
                            ]
                        },
                    ],
                    "volumes": [
                        {
                            "name": request.json['job-name'],
                            "hostPath": {
                                "path": request.json['work-dir']
                            }
                        }
                    ],
                    "restartPolicy": "OnFailure"
                }
            }
        }
    }

    pykube.Job(api, job).create()

    return jsonify({'job': job}), 201


if __name__ == '__main__':
    app.run(debug=True, port=5000,
            host='0.0.0.0')
