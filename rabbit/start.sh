#!/bin/bash
cat > /etc/rabbitmq/rabbitmq.config <<EOF
[
	{rabbit, [{default_user, <<"$1">>},{default_pass, <<"$2">>},{tcp_listeners, [{"0.0.0.0", 5672}]}]}
].
EOF
rabbitmq-server
#rabbitmqctl add_user test 1234
#rabbitmqctl add_vhost vhost
#rabbitmqctl set_user_tags test administrator
#rabbitmqctl set_permissions -p vhost test ".*" ".*" ".*"
