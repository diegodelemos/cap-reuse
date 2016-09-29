FROM ubuntu:16.04
RUN apt-get update
RUN apt-get upgrade
RUN apt-get -y install rabbitmq-server
RUN apt-get -y autoremove && apt-get -y clean
RUN service rabbitmq-server start
ADD start.sh /start.sh
RUN chmod 755 ./start.sh
#RUN rabbitmqctl add_user test 1234
#RUN rabbitmqctl add_vhost vhost
#RUN rabbitmqctl set_user_tags test test-tag
#RUN rabbitmqctl set_permissions -p myvhost myuser ".*" ".*" ".*"
