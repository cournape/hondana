#! /bin/sh

# Build the base image
docker build -t deployment-base -f base.docker .;
# Build the build image
docker build -t deployment-build -f build.docker .;
# Build the wheels using the build image. Built wheels are located into $PWD/wheelhouse
docker run --rm -v "$(pwd)":/application -v "$(pwd)"/wheelhouse:/wheelhouse deployment-build;
# Build the deployment image
docker build -t deployment-run -f run.docker .;
