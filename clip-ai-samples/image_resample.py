from osgeo import gdal
import os
from image_base_info import image_base_info

def walkDirFile(srcPath, ext=".tif"):
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

def do_resample_cmd(resampleCmd, auxXmlFile):
    if os.system(resampleCmd) != 0:
        print("Do resample cmd failed:", resampleCmd)
        return False

    if os.path.exists(auxXmlFile):
        os.remove(auxXmlFile)
    
    return True

def image_resample(inputDir, inputFileExtesnion, outputDir, \
    resampleWidth, resampleHeight, outputExtension):
    responseJson = {}
    try:
        if not outputExtension:
            outputExtension = inputFileExtesnion
        
        inputFileList = walkDirFile(inputDir, inputFileExtesnion)
        if len(inputFileList) <= 0:
            print("Input file list length is equal 0!")
            responseJson["code"] = 400
            responseJson["msg"] = "No file to process!"
            return responseJson
        
        inputFileCount = len(inputFileList)
        firstInputFile = inputFileList[0]
        firstImageDataset = gdal.Open(firstInputFile)
        if not firstImageDataset:
            print("Failed to open first input image!")
            responseJson["code"] = 400
            responseJson["msg"] = "Cannot open first input image file by gdal!"
            return responseJson
        
        imageBandCount = firstImageDataset.RasterCount
        bandOption = " "
        if outputExtension == ".jpg" or outputExtension == ".png":
            if imageBandCount >= 3:
                bandOption = " -b 1 -b 2 -b 3 "
            else:
                bandOption = " -b 1 -b 1 -b 1 "
        
        outSizeOption = f" -outsize {resampleWidth} {resampleHeight} "

        if not os.path.exists(outputDir):
            os.makedirs(outputDir)
        
        firstOutputFile = ""
        for inputFile in inputFileList:
            inputFileName = os.path.basename(inputFile)
            outputFileName = inputFileName.replace(inputFileExtesnion, "") + outputExtension
            outputFile = os.path.join(outputDir, outputFileName)

            auxXmlFile = outputFile + ".aux.xml"

            if not firstOutputFile:
                firstOutputFile = outputFile

            resampleCmd = "gdal_translate" + bandOption + \
                outSizeOption + inputFile + " " + outputFile
            
            if not do_resample_cmd(resampleCmd, auxXmlFile):
                continue
        
        if firstOutputFile:
            resampleInfo = image_base_info(firstOutputFile)

            if resampleInfo["code"] == 200:
                resampleInfo.pop("image")
                resampleInfo["count"] = inputFileCount
    except Exception as e:
        print("Catch exception, error is {}".format(e))
        responseJson["code"] = 400
        responseJson["msg"] = "Catch exception when do resample image!"
        responseJson["code"] = e
        return responseJson

    responseJson["code"] = 200
    responseJson["msg"] = "Do resample success!"
    responseJson["data"] = resampleInfo

    return responseJson

if __name__ == "__main__":
    image_resample("F:\\Data\\PIE-AI样本训练平台数据集\\光学舰船\\test", \
        ".bmp", "F:\\Data\\PIE-AI样本训练平台数据集\\光学舰船\\testout", 1024, 800, ".jpg")