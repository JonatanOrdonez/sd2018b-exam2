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

        registry_tag = "localhost:83/"+request_docker_info_json['service_name']+":"+request_docker_info_json['version'] # create the tag for upload the container to the registry
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
