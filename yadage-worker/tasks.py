from __future__ import absolute_import

from __future__ import print_function
from worker.celery import app


API_VERSION = 'api/v1.0'


@app.task(name='tasks.run_yadage_workflow', ignore_result=True)
def run_yadage_workflow(toplevel, workflow, parameters):
    print(toplevel)
    print(workflow)
    print(parameters)
    """
    import yadage.steering_api
    import yadage.backends.kubernetes as kbb
    import uuid
    workflowid = uuid.uuid4()
    workdir = '/data/{}'.format(workflowid)
    yadage.steering_api.run_workflow(
        workdir = workdir,
        worflow = workflow,
        initdata = parameters,
        loadtoplevel = toplevel,
        updateinterval = 30,
        loginterval = 30,
        schemadir = capschemas.schemadir,
        backend = kbb.KubernetesBackend(experiment = os.environ['EXPERIMENT'])
    )
    """
