FROM ubuntu:22.04

LABEL org.opencontainers.image.authors="Martin Pollard <mp15@sanger.ac.uk>"

ENV PACKAGES autoconf build-essential ca-certificates cmake curl g++ gcc git \
        lib32z1 libboost-all-dev libbz2-dev libcurl4 libcurl4-openssl-dev libffi-dev \
        libfmt-dev libghc-iconv-dev libiperf-dev liblzma-dev libmysqlclient-dev libnuma-dev lib.so.6 libssl-dev \
        libtbb-dev libusb-1.0-0-dev libusb-dev libxml2-dev make numactl python3-dev python3-pip \
        python3-yaml python3-yapsy \
        samtools tar time unzip vim wget zlib1g-dev parallel libarchive-tools

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ${PACKAGES} && \
    apt-get clean

#create benchmarking directory
RUN mkdir /benchmarking

#copy files required for benchmarking and install requirements.txt
COPY ./defaults.yml /benchmarking/
COPY ./setup/ /benchmarking/setup
COPY ./benchmark_suite /benchmarking/benchmark_suite
COPY ./runbenchmarks.py /benchmarking/
RUN pip3 install --upgrade pip setuptools
RUN pip3 install -r /benchmarking/setup/requirements.txt

#create data directory
RUN mkdir /data

ENV PYTHONPATH /benchmarking

WORKDIR /benchmarking

ENTRYPOINT ["python3","/benchmarking/runbenchmarks.py"]
