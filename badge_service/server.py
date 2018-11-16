from flask import Flask, Response
from redis import Redis

app = Flask(__name__)
redis = Redis(host='redis', port=6379, db=0)

@app.route('/badgets/services/<service>/versions/<version>')
def save_build_artifact(service, version):
    redis.set('artifact', str(service)) # save service name
    redis.set('build', str(version)) # save service version
    return Response("Saved :D", 200)

@app.route('/artifact')
def get_artifact():
    artifact = str(redis.get('artifact')) # get service name
    build = str(redis.get('build')) # get service version
    html =  "<table><tr><th>artifact</th><th>build</th></tr><tr><td>"+artifact+"</td><td>"+build+"</td></tr></table>" # html table to show service name and version
    return Response(html, 200)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
