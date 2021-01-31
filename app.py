from flask import Flask, jsonify, request
from image_base_info import image_base_info
from vector_base_info import vector_base_info

app = Flask(__name__)

@app.route("/pie-ai/gdal/info", methods=['GET'])
def gdal_info():
    imagePath = request.args.get("image")
    responseJson = image_base_info(imagePath)

    return jsonify(responseJson)

@app.route("/pie-ai/ogr/info", methods=['GET'])
def ogr_info():
    vectorPath = request.args.get("vector")
    responseJson = vector_base_info(vectorPath)

    return jsonify(responseJson)

if __name__ == "__main__":
    app.config['JSON_AS_ASCII'] = False
    app.config['JSONIFY_MIMETYPE'] ="application/json;charset=utf-8"
    app.debug = False
    app.run(host='localhost', port=5000)