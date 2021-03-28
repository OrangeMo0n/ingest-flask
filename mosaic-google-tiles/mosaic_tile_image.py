import os
import platform
import json
import argparse
import numpy as np
from osgeo import gdal, osr
from mercator_tool import MercatorTools

TILE_SIZE = 256
TILE_BAND_COUNT = 3

def walkDirFile(srcPath, ext=".tif"):
    """
    遍历文件夹
    :param srcPath:
    :param ext:
    :return:
    """
    if not os.path.exists(srcPath):
        print("not find path:{0}".format(srcPath))
        return None
    if os.path.isfile(srcPath):
        return None

    if os.path.isdir(srcPath):
        fileList = []
        for root, dirs, files in os.walk(srcPath):
            for name in files:
                filePath = os.path.join(root, name)
                if ext:
                    if ext == os.path.splitext(name)[1]:
                        fileList.append(filePath)
                else:
                    fileList.append(filePath)
        fileList.sort()
        return fileList
    else:
        return None

def mosaic_tile_image(args):
    responseJson = {}
    try:
        # （1）解析传入的参数
        tileDir = str(args["dir"])
        outputFilePath = str(args["output"])
        tileZoom = int(args["zoom"])
        strTileRange = str(args["range"])

        if not tileDir or not outputFilePath or \
            not tileZoom or not strTileRange:
            responseJson["code"] = 500
            responseJson["msg"] = "Input parameter cannot be null!"
            return responseJson

        tileImageList = walkDirFile(tileDir, ".png")
        if len(tileImageList) <= 0:
            responseJson["code"] = 501
            responseJson["msg"] = "No png tile image in input dir!"
            return responseJson

        tileRangeList = strTileRange.split(" ")
        if len(tileRangeList) != 4:
            responseJson["code"] = 502
            responseJson["msg"] = "range parameter must be 4 argument, like 'xmin xmax ymin ymax'!"
            return responseJson
        
        tileMinx = int(tileRangeList[0])
        tileMaxx = int(tileRangeList[1])
        tileMiny = int(tileRangeList[2])
        tileMaxy = int(tileRangeList[3])

        tile3857Miny = 2**tileZoom-1 - tileMaxy
        tile3857Maxy = 2**tileZoom-1 - tileMiny

        mercatorTool = MercatorTools()
        # （2）计算输出结果影像地理范围
        resultRes = mercatorTool.Resolution(tileZoom)
        tileBoundLD = mercatorTool.TileBounds(tileMinx, tile3857Miny, tileZoom)
        resultMinX = tileBoundLD[0]
        resultMinY = tileBoundLD[1]
        tileBoundRU = mercatorTool.TileBounds(tileMaxx, tile3857Maxy, tileZoom)
        resultMaxX = tileBoundRU[2]
        resultMaxY = tileBoundRU[3]

        geoTransform = (resultMinX, resultRes, 0.0, resultMaxY, 0.0, -resultRes)
        epsgCode = 3857

        tileCountX = tileMaxx-tileMinx+1
        tileCountY = tileMaxy-tileMiny+1
        resultWidth = tileCountX*TILE_SIZE
        resultHeight = tileCountY*TILE_SIZE
        
        # (3) 根据地理范围创建结果影像
        format = "GTiff"
        driver = gdal.GetDriverByName(format)
        outputDs = driver.Create(outputFilePath, resultWidth, resultHeight,
            3, gdal.GDT_Byte)
        
        outputDs.SetGeoTransform(geoTransform)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(epsgCode)
        outputDs.SetProjection(srs.ExportToWkt())

        # (4) 循环遍历将瓦片数据写入结果影像
        tileMosaicIndex = 0
        tileMosaicCount = len(tileImageList)
        for tileImage in tileImageList:
            tileMosaicIndex = tileMosaicIndex + 1
            print(f"{tileMosaicIndex}/{tileMosaicCount}: mosaic tile image file {tileImage}")
            if platform.system() == "Windows":
                imagePathWords = tileImage.split("\\")
            elif platform.system() == "Linux":
                imagePathWords = tileImage.split("/")
            
            tileYIndex = int(imagePathWords[-2])
            tileXIndex = int(imagePathWords[-1].replace(".png", ""))
            inputDs = gdal.Open(tileImage)
            if not inputDs:
                print("Cannot open image file:", tileImage)
                continue

            inputWidth = inputDs.RasterXSize
            inputHeight = inputDs.RasterYSize

            writeResultXOff = (tileXIndex-tileMinx)*TILE_SIZE
            writeResultYOff = (tileYIndex-tileMiny)*TILE_SIZE

            for iband in range(TILE_BAND_COUNT):
                inputBandData = inputDs.GetRasterBand(iband+1).\
                    ReadAsArray(0, 0, TILE_SIZE, TILE_SIZE, TILE_SIZE, TILE_SIZE)
                outputDs.GetRasterBand(iband+1).WriteArray(inputBandData, 
                    writeResultXOff, writeResultYOff)
            
            del inputDs
            inputDs = None
    except Exception as e:
        print("Catch exception, error is {}".format(e))
        responseJson["code"] = 503
        responseJson["msg"] = "Get exception when query image info: {}".format(e)
        return responseJson
    
    responseJson["code"] = 200
    responseJson["msg"] = "tile image mosaic success!"
    mosaicImageInfo = {
        "imagePath": outputFilePath,
        "width": resultWidth,
        "height": resultHeight,
        "geoTransform": geoTransform,
        "epsg": 3857
    }
    responseJson["data"] = mosaicImageInfo

    return responseJson

if __name__ == "__main__":
    '''
    parser = argparse.ArgumentParser(description='查询影像地理范围对应的google瓦片的行列号')
    parser.add_argument("-d", '--dir', action="store", \
        dest="dir", default="F:\\Data\\test4\\13", \
        help="瓦片存储文件夹路径, 例如/home/data/test/13")
    parser.add_argument("-o", "--ouput", action="store", \
        dest="output", default="F:\\Data\\test4\\14\\mosaic.tif", help="拼接结果影像文件路径")
    parser.add_argument("-z", "--zoom", action="store", \
        dest="zoom", default="14", help="瓦片层级,例如13")
    parser.add_argument("-r", "--range", action="store", \
        dest="range", default="13353 13428 6695 6707", \
        help="瓦片的行列号最小最大值范围，例如 810 820 620 630")
    args = parser.parse_args()
    '''

    #config_path = "config.json"
    #with open(config_path, 'r', encoding='utf-8') as f:
    #    args = json.load(f)
    conf = input()
    args = json.loads(conf)

    result = mosaic_tile_image()

    if not result:
        print("Catch exception when do tile image mosaic!")
        exit(-1)
    
    exit(0)

