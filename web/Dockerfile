FROM python:2.7
ADD requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
ADD . /web
WORKDIR /web
RUN mkdir /data
RUN adduser --uid 1000 --disabled-password --gecos '' rodrigdi && \
    chown -R rodrigdi:rodrigdi /web /data
USER rodrigdi
EXPOSE 5000
CMD ["python", "app.py"]
