FROM python:2.7
ADD requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
ADD . /workdir/worker
WORKDIR /workdir
ARG QUEUE_ENV=default
ENV QUEUE_ENV ${QUEUE_ENV}
#RUN adduser --uid 1000 --disabled-password --gecos '' capreuse && \
#    chown -R capreuse:capreuse /workdir
#USER capreuse
CMD celery -A worker worker -l info -Q ${QUEUE_ENV}
