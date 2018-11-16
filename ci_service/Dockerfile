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
