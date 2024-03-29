#!/bin/bash
set -euxo pipefail
ACCESS_KEY=$1
SECRET_ACCESS_KEY=$2
DSN=$3
RABBIT_USER='user'
RABBIT_PASSWORD=`openssl rand -base64 32`
docker create --hostname s3-rabbit --name s3-rabbit -e RABBITMQ_DEFAULT_USER="$RABBIT_USER" -e RABBITMQ_DEFAULT_PASS="$RABBIT_PASSWORD" rabbitmq:3-management
docker cp rabbitmq.conf s3-rabbit:/etc/rabbitmq/rabbitmq.conf
docker cp definitions.json s3-rabbit:/etc/rabbitmq/definitions.json
docker start s3-rabbit

RABBIT_HOST=`docker inspect s3-rabbit | jq --raw-output '.[].NetworkSettings.Networks.bridge.IPAddress'`
docker run -d --hostname s3-consume --name s3-consume -e AWS_ACCESS_KEY_ID=$ACCESS_KEY -e AWS_SECRET_ACCESS_KEY=$SECRET_ACCESS_KEY wsisci/benchmarking_s3processing $RABBIT_HOST / $RABBIT_USER $RABBIT_PASSWORD "$DSN"