FROM python:3.5
ADD requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
ADD . /public
WORKDIR /public
RUN adduser --uid 1000 --disabled-password --gecos '' capuser && \
    chown -R capuser:capuser /public
USER capuser
EXPOSE 5000
CMD ["python", "app.py"]
