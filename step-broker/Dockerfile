FROM python:3.5
ADD requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
ADD . /public
WORKDIR /public
RUN sed -i 's/self.verify_ssl = True/self.verify_ssl = False/' /usr/local/lib/python3.5/site-packages/kubernetes/client/configuration.py
RUN adduser --uid 1000 --disabled-password --gecos '' capuser && \
    chown -R capuser:capuser /public
USER capuser
EXPOSE 5000
CMD ["python", "app.py"]
