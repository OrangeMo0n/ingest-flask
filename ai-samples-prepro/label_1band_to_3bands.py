import os
from osgeo import gdal
import numpy as np

def walkDirFile(srcPath, ext=".txt"):
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

palette = {
    0 : [0, 0, 0],
    1 : [255, 0, 0],
    2 : [0, 255, 0],
    3 : [0, 0, 255]
}

if __name__ == "__main__":
    inputDir = "F:\\Data\\PIE-AI样本训练平台数据集\\landcover.ai\\masks"
    outputDir = "F:\\Data\\PIE-AI样本训练平台数据集\\landcover.ai\\masks_rgb"

    if not os.path.exists(outputDir):
        os.makedirs(outputDir)

    inputFileList = walkDirFile(inputDir, ".tif")
    for inputFile in inputFileList:
        fileName = os.path.basename(inputFile)
        outputFile = os.path.join(outputDir, fileName)

        inputDs = gdal.Open(inputFile)
        imageWidth = inputDs.RasterXSize
        imageHeight = inputDs.RasterYSize

        inputBandData = inputDs.GetRasterBand(1).\
            ReadAsArray(0, 0, imageWidth, imageHeight, imageWidth, imageHeight)
        
        format = "GTiff"
        driver = gdal.GetDriverByName(format)
        outputDs = driver.Create(outputFile, imageWidth, imageHeight,
            3, gdal.GDT_Byte, options=["COMPRESS=LZW"])
        
        for iband in range(3):
            outputBandData = np.zeros((inputBandData.shape[0], inputBandData.shape[1]),
                dtype=np.uint8)
            for c, i in palette.items():
                m = inputBandData == c
                outputBandData[m] = i[iband]
            
            outputDs.GetRasterBand(iband+1).WriteArray(outputBandData, 
                0, 0)
            outputDs.GetRasterBand(iband+1).FlushCache()
        
        del inputDs
        inputDs = None
