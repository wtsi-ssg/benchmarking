#!/bin/bash
set -euxo pipefail
ACCESS_KEY=$1
SECRET_ACCESS_KEY=$2
DSN=$3
RABBIT_HOST=$4
RABBIT_VHOST=$5
RABBIT_USER=$6
RABBIT_PASSWORD=$7
docker run -d --hostname s3-consume --name s3-consume -e AWS_ACCESS_KEY_ID=$ACCESS_KEY -e AWS_SECRET_ACCESS_KEY=$SECRET_ACCESS_KEY wsisci/benchmarking_s3processing $RABBIT_HOST $RABBIT_VHOST $RABBIT_USER $RABBIT_PASSWORD "$DSN"