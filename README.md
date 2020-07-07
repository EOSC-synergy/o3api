O3AS - service to analyse ozone projections
===========================================

Copyright (c) 2017 - 2019 Karlsruhe Institute of Technology - Steinbuch Centre for Computing.

This code is distributed under the GNU LGPLv3 License. Please, see the LICENSE file

@authors: Valentin Kozlov, Borja Esteban, Tobias Kerzenmacher

# O3AS
Description: TBD

Docker images: synergyimk/o3as at https://hub.docker.com/u/synergyimk

# Runing with docker
The most common way to run a container application would be using [docker](https://docs.docker.com/). 

## Using docker commands
To build the image run the following command:
```sh
$ docker build --pull --build-arg branch={branch} -t o3as:{tag} "." 
```
Note that 'branch' is the git brach of source code to run inside the container. Default is 'master'.


To start a container which would process a data set, use the following:
```sh
$ docker run \
    -v /path/to/data:/srv/o3as/data:ro \
    -v /path/to/output:/srv/o3as/output \
    o3as:{tag} \
    /srv/o3as/o3as/eosc.sh [options]
```

## Using docker compose
The usage of docker compose would allow to call other containers in parallel.
This section would be a good example of a working docker compose file:
```yml
version: '3.7'
services:
  o3as:
    build:
      context: .
      args:
        branch: your-branch
    volumes:
        - /path/to/data:/srv/o3as/data:ro
        - /path/to/output:/srv/o3as/output
    entrypoint:
        - /srv/o3as/o3as/eosc.sh 
        - [options]
```

* To start run: `$ docker-compose -f "file_name.yml" up -d --build`
* To stop run: `$ docker-compose -f "file_name.yml" down`


## Issues getting the data into a local folder?
To mount a remote file system using ssh I recommend the usage of [sshfs](https://github.com/libfuse/sshfs)
* To mount:  `$ sshfs -o allow_other [user@]hostname:[directory] mountpoint`
* To unmount: `$ umount mountpoint`

> The option -o allow_other is mandatory to allow docker to access the mount point.

# Running with udocker
In cases where your user cannot get administration rights, the alternative is to use [udocker](https://indigo-dc.gitbook.io/udocker/). 



## Installation
If udocker is not installed, do:
```sh
$ curl https://raw.githubusercontent.com/indigo-dc/udocker/master/udocker.py > udocker
$ chmod u+rx ./udocker
$ mv udocker $HOME/.local/bin # (or something in your PATH)
$ udocker install
```
> More INFO: https://github.com/indigo-dc/udocker/blob/master/doc/installation_manual.md


## Using udocker
The standard way to work with udocker is:

### BUILD new image and PUSH to regisry
In a **computer with docker installed**, build and upload to a registry the image to download it later in the computer where to use udocker.

* `docker build --pull --rm -f "Dockerfile" -t o3as:{tag} "."` <br /> 
To build the image on the directory where the file [Dockerfile](./Dockerfile) is located. Replace {tag} by a version identification.

* `docker push {your-registry}/o3as:{tag}` <br /> 
To push the image to {your-registry} (In Docker hub for example).


### PULL image and CREATE Container
In a **computer to run using udocker**, download the image and create a container:

* `udocker pull {your-registry}/o3as:{tag}` <br /> 
To download the image from your registry.

*  `udocker create --name={container-name} {your-registry}/o3as:{tag}` <br /> 
To push the image to {your-registry} (In Docker hub for example).

> NB: creating container may take 5-10 minutes...


### RUN the container
In a similar way it would be done with docker, you can run:
```sh
udocker run \
    -v /path/to/data:/srv/o3as/data:ro \
    -v /path/to/output:/srv/o3as/output \
    {container-name} \
    /srv/o3as/o3as/eosc.sh [options]
```
Do not forget to indicate the correct path for your data and where to store the outputs.

