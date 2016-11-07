FROM python:2.7
ADD requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
ADD . /workdir/worker
WORKDIR /workdir
ARG QUEUE_ENV=default
ENV QUEUE_ENV ${QUEUE_ENV}
RUN adduser --uid 1004 --disabled-password --gecos '' capreuse-recast && \
    chown -R capreuse-recast:capreuse-recast /workdir
USER capreuse-recast
CMD celery -A worker worker -l info -Q ${QUEUE_ENV}
