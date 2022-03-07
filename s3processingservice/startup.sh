ACCESS_KEY=$1
SECRET_ACCESS_KEY=$2
DSN=$3
RABBIT_PASSWORD=`openssl rand -base64 32`
docker run -v ./rabbitmq.conf:/etc/rabbitmq/rabbitmq.conf:ro ./definitions.json:/etc/rabbitmq/definitions.json:ro -d --hostname s3-rabbit --name s3-rabbit -e RABBITMQ_DEFAULT_USER=user -e RABBITMQ_DEFAULT_PASS=$RABBIT_PASSWORD rabbitmq:3-management
RABBITMQ_IP=`docker inspect s3-rabbit | jq '.[].NetworkSettings.Networks.bridge.IPAddress'`
docker run -d --hostname s3-consume -name s3-consume -e AWS_ACCESS_KEY_ID=$ACCESS_KEY -e AWS_SECRET_ACCESS_KEY=$SECRET_ACCESS_KEY wsisci/benchmarking_s3processing $RABBITMQ_IP $DSN