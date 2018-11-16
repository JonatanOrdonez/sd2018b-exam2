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
    request_data = request.get_data()
    request_data_string = str(request_data, 'utf-8')
    request_data_json = json.loads(request_data_string)
    is_merged = request_data_json["pull_request"]['merged']
    if is_merged:
        sha_id = request_data_json["pull_request"]["head"]["sha"]
        docker_info_url = "https://raw.githubusercontent.com/JonatanOrdonez/sd2018b-exam2/"+sha_id+"/dockerInfo.json"
        request_docker_info_data = requests.get(docker_info_url)
        request_docker_info_json = json.loads(request_docker_info_data.content)

        docker_file_pattern_url = "https://raw.githubusercontent.com/JonatanOrdonez/sd2018b-exam2/"+sha_id+"/Dockerfile"
        docker_file_pattern_data = requests.get(docker_file_pattern_url)
        docker_file_pattern = docker_file_pattern_data.content
        docker_file_artifact = open("Dockerfile", "w")
        docker_file_artifact.write(str(docker_file_pattern, 'utf-8'))
        docker_file_artifact.close()

        registry_url = "192.168.130.126:8083/"+request_docker_info_json['service_name']+":"+request_docker_info_json['version']
        registry = docker.DockerClient(base_url='unix://var/run/docker.sock')
        registry.images.build(path="./", tag=registry_url)
        registry.images.push(registry_url)
        # registry.images.remove(image=registry_url, force=True)
        return Response("Image built successfully :D", 200)
    else:
        return Response("Pull request is not currently merged :c", 200)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
