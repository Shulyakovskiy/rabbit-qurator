#!/bin/sh

: ${RABBITPY_PORT:=8889}
: ${IWMN_ENV:="devel"}
: ${CONTAINERNAME:=rabbitpy-$IWMN_ENV}

HOSTNAME="rabbitpy"
docker stop ${CONTAINERNAME} && docker rm ${CONTAINERNAME}
docker run --name ${CONTAINERNAME} \
    -i -t  \
    -h  $CONTAINERNAME \
    -v /usr/local/d8o/rabbitpy:/usr/local/d8o/rabbitpy:rw  \
    -v /usr/local/d8o/domainsage:/usr/local/d8o/domainsage:r \
    --link rabbitmq:amq \
    --link rsyslogd:syslog \
    -p 0.0.0.0:$RABBITPY_PORT:$RABBITPY_PORT \
    -e RABBITPY_ENVIRONMENT=$IWMN_ENV \
    -e RAYGUN_API_KEY=$RAYGUN_API_KEY \
    docker.domarino.com/rabbitpy
