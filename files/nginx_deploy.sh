#!/bin/sh

yum update -y
yum install -y epel-release
amazon-linux-extras install -y nginx1.12

cat <<EOT >> nginx.conf
#user  nobody;
worker_processes  1;

#error_log  logs/error.log;
#error_log  logs/error.log  notice;
#error_log  logs/error.log  info;

#pid        logs/nginx.pid;


events {
    worker_connections  1024;
}


http {
    include       mime.types;
    default_type  application/octet-stream;

    upstream backend {
    ip_hash;
    server $backend_server1:3000;
    server $backend_server2:3000;

    }

    server {
        listen 80;

        location / {
            proxy_pass http://backend;
            proxy_set_header HOST backend;
        }
    }

}
EOT

mv nginx.conf /etc/nginx/nginx.conf
systemctl start nginx