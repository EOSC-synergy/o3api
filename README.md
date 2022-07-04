# REST API for the O3as service
[![Build Status](https://jenkins.eosc-synergy.eu/buildStatus/icon?job=eosc-synergy-org%2Fo3api%2Fmaster)](https://jenkins.eosc-synergy.eu/job/eosc-synergy-org/job/o3api/job/master/)
[![Documentation Status](https://readthedocs.org/projects/o3as/badge/?version=latest)](https://o3as.readthedocs.io/en/latest/?badge=latest)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-1.4-4baaaa.svg)](CODE_OF_CONDUCT.md)

[<img src="https://o3as.data.kit.edu/img/logos/o3as-logo.png" width=50 alt="O3as logo"/>](http://o3as.data.kit.edu/) &nbsp;&nbsp;
O3as is a service for Ozone (O3) Assessment, http://o3as.data.kit.edu/

## Description

O3as REST API (o3api) provides:

* Access to O3as (ozone assessment) skimmed data, produced by the [o3skim](https://git.scc.kit.edu/synergy.o3as/o3skim) component
* Information about used Climate Models
* Ability to produce ozone plots (e.g. tco3_zm, tco3_return) in either PDF or JSON format

The API leverages [Swagger](https://swagger.io/), [Flask](https://flask.palletsprojects.com/), 
and [Connexion](https://connexion.readthedocs.io/), and it is based on OpenAPI v3 standards.

## Documentation

More details about the O3as service and API can be found in our [documentation](https://o3as.readthedocs.io).

## Quick start
O3as API is primarily meant to be run as a container application, e.g. either by using [docker](#docker), [docker-compose](#docker-compose), [udocker](#udocker) or in [Kubernetes](#kubernetes).

### Skimmed Climate model data
In order to run the application, you need to provide corresponding Climate Model data. 
A publicly available published dataset can be downloaded from DOI: [10.35097/675](https://dx.doi.org/10.35097/675).

### Docker images
Pre-built Docker images can be found in our Docker Hub repository: https://hub.docker.com/r/o3as/o3api/tags .

**N.B.**: If you want to rebuild images, the [Dockerfile](docker/Dockerfile) is located in the `docker/` directory.

### Using docker  <a name="docker"></a>
To start a container which would provide REST API to process a dataset, use e.g. the following:
```sh
docker run --rm \
    -v /path/to/data:/srv/o3api/data:ro \
    -p 5005:5005 \
    o3as/o3api:{tag} \
```
where `tag = latest` (or `xx.yy.zz` for the particular version).
You may need to adjust `O3AS_DATA_BASEPATH` environment variable to indicate the path to the Skimmed data.

Or see [o3as-docker-example.sh](docker/o3as-docker-example.sh) example shell script in the `docker/` directory.

### Using docker-compose <a name="docker-compose"></a>
An exampled [docker-compose.yaml](docker/docker-compose.yaml) can be found in the `docker/` directory.

* To start o3api as a daemon: `docker-compose -f docker/docker-compose.yaml up -d`
* If you want to build your own image and immediately run: `docker-compose -f docker/docker-compose.yaml up -d --build`
* To stop run: `docker-compose -f docker/docker-compose.yaml down`


### Using udocker <a name="udocker"></a>
In cases where your user cannot get administration rights, the alternative is to use [udocker](https://indigo-dc.gitbook.io/udocker/). 

#### How to install udocker
If udocker is not installed, do:
```sh
curl https://raw.githubusercontent.com/indigo-dc/udocker/master/udocker.py > udocker
chmod u+rx ./udocker
mv udocker $HOME/.local/bin # (or something in your PATH)
udocker install
```
> More INFO: https://github.com/indigo-dc/udocker/blob/master/doc/installation_manual.md


#### Running with udocker
The standard way to work with udocker is:

1. PULL the provided Docker image and CREATE Container
In the computer where to run with udocker, download the image and create a container:

* `udocker pull o3as/o3api:{tag}` <br /> 
To download the image from the Docker Hub registry.

*  `udocker create --name={container-name} o3as/o3api:{tag}` <br /> 
To create the corresponding container on your system.

> NB: creating container may take a few minutes...

> `udocker setup --execmode=F3 {container-name}` <br />
To change execmode, if needed

2. RUN the container
In a similar way it would be done with docker, you can run:
```sh
udocker run \
    -v /path/to/data:/srv/o3api/data:ro \
    {container-name}
```
Do not forget to indicate the correct path for your data, e.g. you may need to adjust `O3AS_DATA_BASEPATH` environment variable to indicate the path to Skimmed data.

### Deploying in Kubernetes <a name="kubernetes"></a>
A set of configuration files to deploy in Kubernetes can be found in another repository: [o3k8s](https://git.scc.kit.edu/synergy.o3as/o3k8s)

## Contributing
Please, see our [CONTRIBUTING](CONTRIBUTING.md) description and the [CODE OF CONDUCT](CODE_OF_CONDUCT.md).

## License
This code is distributed under the GNU GPLv3 License. Please, see the [LICENSE](LICENSE) file

## Authors and acknowledgment
@Authors: Valentin Kozlov, Borja Esteban, Tobias Kerzenmacher (KIT)

Copyright (c) 2020 - 2022 Karlsruhe Institute of Technology - Steinbuch Centre for Computing.
