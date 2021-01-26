FROM ubuntu:18.04

# install OS packages, etc.
RUN \
  apt -y update --fix-missing && \
  apt -y install software-properties-common && \
  apt -y update && \
  apt -y upgrade && \
  apt -y install gdal-bin libgdal-dev python-gdal python3-gdal python3-pip libsm6 libxext6 libxrender-dev libgnutls28-dev libspatialindex-dev && \
  rm -rf /var/lib/apt/lists/*

# install dependencies
WORKDIR /workspace
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# copy files
COPY . /workspace
