from osgeo import gdal
import os

def clip_image_sample(imagePath, sampleWidth, sampleHeight, sampleFormat):
    responseJson = {}
    try:
        dataset = gdal.Open(imagePath)
    except Exception as e:
        responseJson["code"] = 500
        responseJson["msg"] = ""

        return responseJson

    return ""