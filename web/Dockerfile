FROM python:2.7
ADD requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
ADD . /web
WORKDIR /web
RUN adduser --uid 1000 --disabled-password --gecos '' rodrigdi && \
    chown -R rodrigdi:rodrigdi /web
USER rodrigdi