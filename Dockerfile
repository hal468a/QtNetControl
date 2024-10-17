FROM ubuntu:20.04

# Setting time zone
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Taipei

RUN apt-get update && apt-get install -y \
    qttools5-dev-tools \
    qttools5-dev \
    python3-dev \
    python3-pip \
    python3-pyqt5 \
    net-tools \
    network-manager \
    xorg \
    mesa-utils \
    libgl1-mesa-dri \
    iputils-ping \
    && apt-get clean

RUN mkdir -p /usr/src /tmp/runtime-root && chmod 0700 /tmp/runtime-root
WORKDIR /usr/src