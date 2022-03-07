FROM ubuntu:21.10

LABEL org.opencontainers.image.authors="Martin Pollard <mp15@sanger.ac.uk>"

ENV PACKAGES autoconf build-essential ca-certificates cmake curl g++ gcc git make python3-dev python3-pip \
        libpq-dev librabbitmq4-dev

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ${PACKAGES} && \
    apt-get clean

COPY ./jsonschema.json /
COPY ./requirements.txt /
COPY ./imports3.py /
RUN pip3 install --upgrade pip setuptools
RUN pip3 install -r /requirements.txt

ENTRYPOINT ["python3 ./imports3.py"]