import os
import argparse
from osgeo import gdal
from mercator_tool import MercatorTools
from geodetic_tool import GlobalGeodetic

def query_image_tile_index():
    parser = argparse.ArgumentParser(description='查询影像地理范围对应的google瓦片的行列号')
    parser.add_argument("-e", '--envlope', action="store", \
        dest="envlope", default="116.368515 117.076707 36.726312 37.29084", \
        help="坐标范围(xmin xmax ymin ymax),例如3857投影坐标和经纬度坐标 112.0 113.0 37.0 38.0")
    parser.add_argument("-z", "--zoom", action="store", \
        dest="zoom", default="16", help="瓦片层级")
    parser.add_argument("-f", "--format", action="store", \
        dest="format", default="4326", \
        help="坐标范围格式，默认为3857投影坐标，可选3857和4326,其中4326为经纬度坐标")
    parser.add_argument("-o", "--output", action="store", \
        dest="output", default="4326", \
        help="查询的切片投影方式，默认为3857投影坐标，可选3857和4326,其中4326为经纬度坐标")
    args = parser.parse_args()

    geoEnvlope = str(args.envlope)
    tileZoom = int(args.zoom)
    coordFormat = str(args.format)
    outputCoordFormat = str(args.output)

    if not geoEnvlope:
        print("Please input query geo envlope!")
        return None
    
    envlopeCoords = geoEnvlope.split(" ")
    if len(envlopeCoords) != 4:
        print("Please input correct geo envlope format, for example 112.0 113.0 37.0 38.0")
        return None
    
    xmin = float(envlopeCoords[0])
    xmax = float(envlopeCoords[1])
    ymin = float(envlopeCoords[2])
    ymax = float(envlopeCoords[3])

    if outputCoordFormat == "3857":
        mercator = MercatorTools()
        if coordFormat == "4326":
            tileMinx, tileMiny = mercator.LatLonToTile(xmin, ymin, tileZoom)
            tileMaxx, tileMaxy = mercator.LatLonToTile(xmax, ymax, tileZoom)
        else:
            tileMinx, tileMiny = mercator.MetersToTile(xmin, ymin, tileZoom)
            tileMaxx, tileMaxy = mercator.MetersToTile(xmax, ymax, tileZoom)
    elif outputCoordFormat == "4326":
        geodetic = GlobalGeodetic(tmscompatible=None)
        if coordFormat == "4326":
            tileMinx, tileMiny = geodetic.LonLatToTile(xmin, ymin, tileZoom)
            tileMaxx, tileMaxy = geodetic.LonLatToTile(xmax, ymax, tileZoom)

    tileMinx, tileMiny = max(0, tileMinx), max(0, tileMiny)
    tileMaxx, tileMaxy = min(2 ** tileZoom - 1, tileMaxx), min(2 ** tileZoom - 1, tileMaxy)

    tileMaxY = 2**(tileZoom-1) - tileMiny - 1
    tileMinY = 2**(tileZoom-1) - tileMaxy - 1
    return [tileMinx, tileMaxx, tileMinY, tileMaxY]

if __name__ == "__main__":
    result = query_image_tile_index()
    if not result:
        print("Get error when query image tile index!")
        exit(-1)
    
    print(result)
    exit(0)