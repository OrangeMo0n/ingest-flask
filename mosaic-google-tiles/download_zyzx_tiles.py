import requests
from osgeo import gdal, osr
import os
from geodetic_tool import GlobalGeodetic
import argparse
from concurrent.futures import ThreadPoolExecutor
import shutil

DOWNLOAD_URL = "http://119.3.169.225:3999/geowebcache/service/wmts?"
TILE_SIZE = 256

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

def downloadTileBandTif(**kwargs):
    layerId = kwargs.get("layerId")
    requestBandIndex = kwargs.get("bandId")
    levelId = kwargs.get("levelId")
    tileColIndex = kwargs.get("colId")
    tileRowIndex = kwargs.get("rowId")
    outputTileBandFile = kwargs.get("tileBandFile")

    for requestTimes in range(5):
        response = requests.get(DOWNLOAD_URL, \
            params={"band":f"SBAND:{requestBandIndex}", \
                "layer":f"{layerId}", \
                "tilematrixset":"EPSG:4326", \
                "Service":"WMTS", \
                "Request":"GetTile", \
                "Version":"1.0.0", \
                "Format":"image/tiff", \
                "TileMatrix":f"EPSG:4326:{levelId}", \
                "TileCol":f"{tileColIndex}", \
                "TileRow":f"{tileRowIndex}"})
        if response.status_code == 200:
            break

    if response.status_code != 200:
        print(f"Cannot get tile image: col={tileColIndex} row={tileRowIndex}")
        return False

    with open(outputTileBandFile, 'wb') as file:
        file.write(response.content)
    
    return True

def download_zyzx_tiles(layerId, bandCount, levelId, \
    tileStartCol, tileEndCol, \
    tileStartRow, tileEndRow, \
    outputFile):
    geodetic = GlobalGeodetic(tmscompatible=None)
    boundLU = geodetic.TileLatLonBounds(tileStartCol, 2**(levelId-1)-1-tileEndRow, levelId)
    boundRD = geodetic.TileLatLonBounds(tileEndCol, 2**(levelId-1)-1-tileStartRow, levelId)
    
    tileColCount = tileEndCol-tileStartCol+1
    tileRowCount = tileEndRow-tileStartRow+1

    outputImageWidth = tileColCount*TILE_SIZE
    outputImageHeight = tileRowCount*TILE_SIZE

    resultResX = (boundRD[3] - boundLU[1]) / outputImageWidth
    resultResY = (boundRD[2] - boundLU[0]) / outputImageHeight
    geoTransform = (boundLU[1], resultResX, 0.0, boundRD[2], 0.0, -resultResX)

    format = "GTiff"
    driver = gdal.GetDriverByName(format)
    outputDs = driver.Create(outputFile, outputImageWidth, outputImageHeight,
        4, gdal.GDT_UInt16)
    
    epsgCode = 4326
    outputDs.SetGeoTransform(geoTransform)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsgCode)
    outputDs.SetProjection(srs.ExportToWkt())

    tileCount = tileColCount * tileRowCount
    progIndex = 0

    tempOutputDir = os.path.dirname(outputFile)
    outputFileName = os.path.basename(outputFile).replace(".tif", "")
    tempOutputDir = os.path.join(tempOutputDir, outputFileName)

    if not os.path.exists(tempOutputDir):
        os.makedirs(tempOutputDir)

    with ThreadPoolExecutor(max_workers=10) as executor:
        for colIndex in range(tileColCount):
            tileColIndex = colIndex + tileStartCol
            for rowIndex in range(tileRowCount):
                tileRowIndex = rowIndex + tileStartRow

                progIndex += 1
                print(f"{progIndex}/{tileCount}: col={tileColIndex}, row={tileRowIndex}")

                for bandIndex in range(bandCount):
                    requestBandIndex = bandIndex+1

                    tempFile = f"{tileColIndex}_{tileRowIndex}_{requestBandIndex}.tif"
                    tempFile = os.path.join(tempOutputDir, tempFile)

                    kwargs = {
                        "layerId": layerID,
                        "bandId": requestBandIndex,
                        "levelId": levelID,
                        "colId": tileColIndex,
                        "rowId": tileRowIndex,
                        "tileBandFile": tempFile
                    }

                    executor.submit(downloadTileBandTif, **kwargs)
    
    tileBandFiles = walkDirFile(tempOutputDir)
    for bandFile in tileBandFiles:
        bandFileName = os.path.basename(bandFile).replace(".tif", "")
        tileCol = int(bandFileName.split("_")[0]) - tileStartCol
        tileRow = int(bandFileName.split("_")[1]) - tileStartRow
        bandIndex = int(bandFileName.split("_")[2])

        inputDs = gdal.Open(bandFile)
        inputBandData = inputDs.GetRasterBand(1).\
            ReadAsArray(0, 0, TILE_SIZE, TILE_SIZE, TILE_SIZE, TILE_SIZE)
        outputDs.GetRasterBand(bandIndex).WriteArray(inputBandData, 
            tileCol*TILE_SIZE, tileRow*TILE_SIZE)
        
        del inputDs
        inputDs = None
    
    if os.path.exists(tempOutputDir):
        shutil.rmtree(tempOutputDir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='zywxzx4326投影瓦片下载拼接')
    parser.add_argument("-id", '--layerID', action="store", \
        dest="id", default="283", help="layer ID号")
    parser.add_argument("-b", '--bandCount', action="store", \
        dest="bc", default="4", help="波段数据")
    parser.add_argument("-level", '--levelID', action="store", \
        dest="lv", default="13", help="Level ID号")
    parser.add_argument("-sc", '--startCol', action="store", \
        dest="sc", default="6755", help="起始Col")
    parser.add_argument("-ec", '--endCol', action="store", \
        dest="ec", default="6766", help="终止Col") 
    parser.add_argument("-sr", '--startRow', action="store", \
        dest="sr", default="1211", help="起始Row")
    parser.add_argument("-er", '--endRow', action="store", \
        dest="er", default="1220", help="终止Row")
    parser.add_argument("-o", '--output', action="store", \
        dest="output", default="D:\\283_13.tif", help="输出影像路径")  
    args = parser.parse_args()

    layerID = int(args.id)
    bandCount = int(args.bc)
    levelID = int(args.lv)
    startCol = int(args.sc)
    endCol = int(args.ec)
    startRow = int(args.sr)
    endRow = int(args.er)
    outputFile = str(args.output)

    download_zyzx_tiles(layerID, bandCount, levelID, \
        startCol, endCol, startRow, endRow, outputFile)