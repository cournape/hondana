To run hondana in docker, we have prepared a set of 3 docker images:

1. the base image (base.docker Dockerfile), to be used for the 2 other images
2. the build image to build the wheels (build.docker Dockerfile)
3. the actual hondana image where hondana is deployed w/ nginx

The basic workflow to build the docker images is in scripts/build_docker_images.sh:

  ``` bash
  bash scripts/build_docker_images.sh
  ```

You then need to create an hondana configuration:

  ``` bash
  mkdir -p config && python scripts/generate_conf.py config.yaml.j2 config/config.yaml
  ```

Then to run hondana:

  ``` bash
  docker run -p 80:80 -v $(pwd)/store:/srv/store -v $(pwd)/config:/srv/config deployment-run
  ```
