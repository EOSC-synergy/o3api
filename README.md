Copyright (c) 2017 - 2019 Karlsruhe Institute of Technology - Steinbuch Centre for Computing.

This code is distributed under the GNU LGPLv3 License. Please, see the LICENSE file

@authors: Valentin Kozlov, Borja Esteban, Tobias Kerzenmacher (KIT)

# REST API for the O3as service
[![Build Status](https://jenkins.eosc-synergy.eu/buildStatus/icon?job=eosc-synergy-org%2Fo3api%2Fmaster)](https://jenkins.eosc-synergy.eu/job/eosc-synergy-org/job/o3api/job/master/) [![Documentation Status](https://readthedocs.org/projects/o3as/badge/?version=latest)](https://o3as.readthedocs.io/en/latest/?badge=latest)

O3as is a service for Ozone (O3) Assessment, http://o3as.data.kit.edu/

Description: *to come...*

# Runing with docker
The most common way to run a container application would be using [docker](https://docs.docker.com/).

**N.B.**: Dockerfile and docker-compose.yml example are located in the `~/docker` subdirectory.

## Using docker commands
To start a container which would provide REST API to process a data set, use the following:
```sh
docker run \
    -v /path/to/data:/srv/o3api/data:ro \
    o3as/o3api:{tag} \
```
where `tag = latest`


## Using docker compose
This section would be a good example of a working docker compose file:
```yml
version: '3.7'
services:
  o3api:
    image: o3as/o3api:{tag}
    build:
      context: .
      args:
        branch: {tag}
    volumes:
        - /path/to/data:/srv/o3api/data:ro
    ports:
        - 5005:5005
    entrypoint:
        - /srv/o3api/start.sh 
```

* To start run: `$ docker-compose -f "file_name.yml" up -d --build`
* To stop run: `$ docker-compose -f "file_name.yml" down`


## Issues getting the data into a local folder?
To mount a remote file system using ssh the usage of [sshfs](https://github.com/libfuse/sshfs) is recommended:
* To mount:  `$ sshfs -o allow_other [user@]hostname:[directory] mountpoint`
* To unmount: `$ umount mountpoint`

> The option -o allow_other is mandatory to allow docker to access the mount point.

# Running with udocker
In cases where your user cannot get administration rights, the alternative is to use [udocker](https://indigo-dc.gitbook.io/udocker/). 


## Installation
If udocker is not installed, do:
```sh
curl https://raw.githubusercontent.com/indigo-dc/udocker/master/udocker.py > udocker
chmod u+rx ./udocker
mv udocker $HOME/.local/bin # (or something in your PATH)
udocker install
```
> More INFO: https://github.com/indigo-dc/udocker/blob/master/doc/installation_manual.md


## Using udocker
The standard way to work with udocker is:

### PULL the provided Docker image and CREATE Container
In the computer where to run with udocker, download the image and create a container:

* `udocker pull o3as/o3api:{tag}` <br /> 
To download the image from the Docker Hub registry.

*  `udocker create --name={container-name} o3as/o3api:{tag}` <br /> 
To create the corresponding container on your system.

> NB: creating container may take 5-10 minutes...

> `udocker setup --execmode=F3 {container-name}` <br />
To change execmode, if needed

### RUN the container
In a similar way it would be done with docker, you can run:
```sh
udocker run \
    -v /path/to/data:/srv/o3api/data:ro \
    {container-name}
```
Do not forget to indicate the correct path for your data and where to store the outputs.

If you like to re-build Docker image:
### BUILD new image and PUSH to regisry
In a computer where docker is installed, build and upload to a registry the image to download it later in the computer where to use udocker.

* `docker build --pull --rm -t {your-registry}/o3api:{tag} "."` <br /> 
To build the image on the directory where the file [Dockerfile](./Dockerfile) is located. Replace {tag} by a version identification.

*  `docker push {your-registry}/o3api:{tag}` <br /> 
To push the image to {your-registry} (In Docker hub for example).
