FROM ubuntu:20.04

MAINTAINER Martin Pollard

ENV PACKAGES autoconf build-essential ca-certificates cmake curl g++ gcc git \
        lib32z1 libboost-all-dev libbz2-dev libcurl4 libcurl4-openssl-dev libffi-dev \
        libfmt-dev libghc-iconv-dev libiperf-dev liblzma-dev libmysqlclient-dev libnuma-dev lib.so.6 libssl-dev \
        libtbb-dev libusb-1.0-0-dev libusb-dev libxml2-dev make numactl python3-dev python3-pip \
        python3-yaml python3-yapsy qt5-default qt5-qmake qtbase5-dev qttools5-dev \
        samtools tar time unzip vim wget zlib1g-dev parallel

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ${PACKAGES} && \
    apt-get clean

#create benchmarking directory
RUN mkdir /benchmarking

#copy files required for benchmarking and install requirements.txt
COPY ./setup/ /benchmarking/setup
COPY ./scripts/ /benchmarking/scripts
COPY ./benchmark_suite /benchmarking/benchmark_suite
COPY ./runbenchmarks.sh /benchmarking/
RUN pip3 install --upgrade pip setuptools
RUN pip3 install -r /benchmarking/setup/requirements.txt

#create data directory
RUN mkdir /data

ENTRYPOINT ["./benchmarking/runbenchmarks.sh"]

