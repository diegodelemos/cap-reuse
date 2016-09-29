FROM python:2.7
ADD requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
ADD . /workdir/worker
WORKDIR /workdir
RUN adduser --uid 1000 --disabled-password --gecos '' rodrigdi && \
    chown -R rodrigdi:rodrigdi /workdir
USER rodrigdi