FROM python:3.6-slim

WORKDIR /server

COPY . /server

RUN pip install -r requirements.txt

EXPOSE 80

CMD ["python", "server.py"]
