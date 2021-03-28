import json
from flask import Flask, jsonify, request
from mosaic_tile_image import mosaic_tile_image

app = Flask(__name__)

@app.route("/mosaic", methods=['POST'])
def tile_mosaic():
    data = request.get_data()
    print("POST data:", data)
    json_data = json.loads(data.decode("utf-8"))

    return jsonify(mosaic_tile_image(json_data))

if __name__ == "__main__":
    app.config['JSON_AS_ASCII'] = False
    app.config['JSONIFY_MIMETYPE'] ="application/json;charset=utf-8"
    app.debug = False
    app.run(host='localhost', port=5000)