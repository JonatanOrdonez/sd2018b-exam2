# sd2018b-exam2

**Universidad ICESI**  
**Course:** Sistemas Distribuidos  
**Teacher:** Daniel Barragán C.  
**Topic:** Automatización de infraestructura  
**Teacher's email:** daniel.barragan at correo.icesi.edu.co  
**Student:** Jonatan Ordoñz Burbano  
**Banner code:** A00054000  
**Repository:** https://github.com/JonatanOrdonez/sd2018b-exam2/tree/jordonez/exam2

## Description
The following document describes the implementation of a ci server responsible for creating a docker image each time a pull request is made to a repository and uploading it to a registry server from which it can be downloaded.

The created containers will work in the following way: every time a pull request is done from the ``develop-merge`` branch, a github webhook will send a payload to the ``ci_service`` that will validate if the pull request made has been merged. When the pull request has been merged, the ``ci_service`` will create a docker image from the uploaded ``Dockerfile`` and the information from the ``dockerInfo.json``, which will be uploaded to a registry server.

### Docker compose
In the repository there is a file called ``docker-compose.yml``, which is responsible for building three docker services. The first service is a ci_service that is responsible for creating
and uploading a docker image from a configuration file called ``'dockerInfo.json'`` to a docker registry image server. The second service is ``ngrok_service``, which is responsible for creating an internet tunnel to our ``ci_service``; this allows to a github webhook to send a payload with information of all the pull requests made to our repository. The last service is the ``registry_service``, which allows us to create a storage space for docker images, which we can later use to create our containers.

The docker-compose.yml file is located in the root of this repository. The content of the file is shown below.

```
version: "3"
services:
  ci_service:
    build: ./ci_service
    ports:
      - "81:80"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
  ngrok_service:
    image: wernight/ngrok
    ports:
      - "82:4040"
    links:
      - ci_service
    environment:
      NGROK_PORT: ci_service:80
  registry_service:
    restart: always
    image: registry:2
    ports:
      - "83:5000"
```
To create the containers we execute the following commands in the same order:
```
docker-compose build
```
```
docker-compose up
```
In the following image you can see that services are created correctly:

![](images/maquinas_subidas.png)

**The creation of each service in detail is explained below.**

### Ngrok service
This service is built through the docker-compose file, wich takes the base image ``wernight/ngrok`` from docker hub. In the docker-compose the 82 port is mapped to 4040 container port, in which the ngrok service is hosted. A redirection of ports is also made, so the requests made to the ``ngrok_service`` are redirected to 80 port of the ``ci_service``. This process is made explicit in the line ``NGROK PORT: ci_service: 80``. In addition to creating a tunnel to our pc, the ``wernight/ngrok`` image provides a GUI that shows the IP through which we can access our server.

In the following image it can be seen that when accessing ``0.0.0.0:82`` a GUI with the ngrok information appears:

![](images/ngrok_con_ip.png)

**Note:** Unlike the first partial, this base image makes it very easy for us to create a tunnel that communicates our server to internet, since basically ... we don't have to make the manual process.

### Ci service
In the ``docker-compose`` file we can see that the 81 port of the computer is mapped with 80 port of the container; this is done because internally a flask api is deployed and is exposed on 80 port. In addition, the ``docker.sock`` file is copied from the ``/var/run/`` folder to allow the container to communicate with docker through a socket and build an image.

#### Ci service Dockerfile
The image for this service is created from a Dockerfile in the ``/ci_service`` folder. This file contains the following information:
```
# take the 'python:3.6-slim' base image for the container
FROM python:3.6-slim

# generate a server folder
WORKDIR /server

# copy the files of the current folder inside de docker container in '/server' folder
COPY . /server

# install the dependencies in requirements.txt: Flask and Docker
RUN pip install -r requirements.txt

# expose the 80 port for listen requests
EXPOSE 80

# execute the command 'python server.py' for execute the server service
CMD ["python", "server.py"]
```
The base image used to create the ``ci_service`` is ``python: 3.6-slim`` from docker hub, which already comes with python 3.6 that is necessary to deploy our flask service. The dockerfile specifies the creation of a folder inside the container called ``/server``, where the ``server.py`` and the ``requirements.txt`` will be stored. Then the dependencies of the requirements file are installed and finally the server is raised through the command ``python server.py``.

#### Ci service server.py
This file contains the necessary code to receive and read a payload from a github webhook, which contains the pull request information made to the repository.

After processing the pull request information, this is validated whether or not it has been merged to the branch. If it has been merged, a docker image is created from the Dockerfile base file in the ``develop-merge`` branch. Then an image is uploaded to the registry using the name of the service and version as found in the ``dockerInfo.json`` file contained in the branch that we want to mix.

The content of the file can be seen below:
```
from flask import Flask, Response, json, request
import socket
import os
import requests
import docker

app = Flask(__name__)

@app.route("/")
def index():
    return "Ya funciona :D"

@app.route("/makeimage", methods=['POST'])
def image_cooker():
    request_data = request.get_data() # request data from http request
    request_data_string = str(request_data, 'utf-8') # parse the request data to string
    request_data_json = json.loads(request_data_string) # parse string request data to json format
    is_merged = request_data_json["pull_request"]['merged'] # get the boolean value from merged action for pull request
    if is_merged:
        sha_id = request_data_json["pull_request"]["head"]["sha"] # get the sha id of pull request
        docker_info_url = "https://raw.githubusercontent.com/JonatanOrdonez/sd2018b-exam2/"+sha_id+"/dockerInfo.json" # url for get dockerInfo json file with service name, version and value
        request_docker_info_data = requests.get(docker_info_url) # request for get dockerInfo.json data
        request_docker_info_json = json.loads(request_docker_info_data.content) # parse docker info data to json

        docker_file_pattern_url = "https://raw.githubusercontent.com/JonatanOrdonez/sd2018b-exam2/"+sha_id+"/Dockerfile" # url for get Dockerfile DSL
        docker_file_pattern_data = requests.get(docker_file_pattern_url) # request for get Dockerfile data
        docker_file_pattern = docker_file_pattern_data.content # get content of Dockerfile
        docker_file_artifact = open("Dockerfile", "w") # instance of a new Dockerfile in the current folder
        docker_file_artifact.write(str(docker_file_pattern, 'utf-8')) # write the content of the Dockerfile of request ine the new file
        docker_file_artifact.close() # close de buffer writer action

        service_name = request_docker_info_json['service_name']
        version = request_docker_info_json['version']
        registry_tag = "localhost:83/"+service_name+":"+version # create the tag for upload the container to the registry
        registry = docker.DockerClient(base_url='unix://var/run/docker.sock') # create a client for communicating with a Docker server
        registry.images.build(path="./", tag=registry_tag) # build a image in the registry server
        registry.images.push(registry_tag) # push the image to the registry
        print("Image built successfully :D")
        return Response("Image built successfully :D", 200)
    else:
        print("Pull request is not currently merged :c")
        return Response("Pull request is not currently merged :c", 200)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)

```

In the following image we can see the ci_service working by accessing the ``0.0.0.0:81`` ip:

![](images/ci_funciona.png)

In addition, we can also access the ``ci_service`` through ``https://c3d3b0d7.ngrok.io`` that is exposed by the ngrok service through port addressing to the ci service. In the following image you can see this working:

![](images/ci_con_ngrok.png)

### Registry service
This service is created from the docker hub base image ``registry image:2``. In the configuration of the docker-compose it is specified to always restart, allowing the service to be executed every time there is a failure. Finally, a mapping of the 83 port of the host computer to the 5000 container port is done.

## How does it works
The first thing that we do is to create a webhook through github and add the ip provided by the ngrok service. In the following image we can see the webhook with the ip:

![](images/ip_en_webhook.png)

The next thing we do is make changes to some file in the develop-merge branch so that we can enable the pull request option and generate a payload through the webhook. For practical purposes, we change the version of the ``dockerInfo.json`` file. The changes can be seen in the following image:

![](images/cambios_develop_merge.png)

In the following image we see how a pull request is done to the develop branch:

![](images/pull_request_a_develop.png)

This trigger causes a payload to be sent to the service exposed by the ``ci_service``. In the following image you can see the payload that has been sent to the service endpoint:

![](images/webhook_payload_pull_request.png)

On the right side you see how the http request is received by the ``ci_service``, however, since the pull request is not mixed, the ``ci_service`` logic is not performed.

This can be seen in the following image. The ci_service returns a response when the pull request has not yet been merged:

![](images/respuesta_pull_request_no_merged.png)

Now merge the pull request to the ``develop`` branch.

![](images/pull_request_mezclado.png)

In the previous image it is observed that the payload has an error, but this is because the process of creating the docker image and uploading it to the registry takes more time than the minimum response time that the webhook has.

On the right side we see that the registry is processing the image to upload it to the server.

To verify that the image has been loaded, we execute the following command that shows the images stored in the tag that we told to the registry in the ``ci_service``.

```
docker images localhost:83/python_aphine:0.2.0
```

In the following image we observed that the image was successfully uploaded:

![](images/imagen_en_registry.png)

To store the image on our own computer, we execute the following command that is responsible for downloading a copy of the registry.

```
docker pull localhost:83/python_alphine:0.2.0
```

In the following image it is observed that the image is downloaded correctly and is stored in our image database:

![](images/lista_imagenes_cargadas_actualmente.png)

## Problems found
1. The first problem encountered was that the registry blocked the access of the ``ci_service`` to upload the image to the server. When I asked my colleagues about the problem, they told me that I had to create certificates and saved them in the container, so the registry would not block the access. However, what I did was to look for an image in the docker hub that would not block access and use the ``registry:2``.

1. Another problem I had was the creation of the container with ngrok, because I thought that I would have to create a container and explicitly leave the instructions that the container had to do to install and run negrok. This looks like the same procedure as the first partial. However, I found an image in the docker hub that creates a container with ngrok and provides a GUI through which the ip can be obtained. The image is ``wernight/ngrok``.
