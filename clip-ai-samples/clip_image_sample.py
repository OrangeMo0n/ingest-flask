from osgeo import gdal
import os
from concurrent.futures import ThreadPoolExecutor

def clip_thread(**kwargs):
    cmd = kwargs.get("cmd", None)
    if not cmd:
        return
    cmdStatus = os.system(cmd)
    if cmdStatus != 0:
        print(f"Do cmd failed: {cmd}")
        return
    
    thumbCmd = kwargs.get("thumb_cmd", None)
    if thumbCmd:
        if os.system(thumbCmd) != 0:
            print("Do create thumb file failed:", thumbCmd)

    auxXmlFile = kwargs.get("aux.xml", None)
    if auxXmlFile:
        if os.path.exists(auxXmlFile):
            os.remove(auxXmlFile)

def clip_image_sample(imagePath, imageId, outDir,\
     sampleWidth, sampleHeight, sampleExtension):
    responseJson = {}
    if sampleExtension != ".tif" and sampleExtension != ".jpg" and \
        sampleExtension != ".png":
        responseJson["code"] = 400
        responseJson["msg"] = "Unsupported sample extension format, must be .tif/.jpg/.png!"
        return responseJson

    if not os.path.exists(outDir):
        os.makedirs(outDir)

    try:
        dataset = gdal.Open(imagePath)
        if not dataset:
            responseJson["code"] = 500
            responseJson["msg"] = "Failed to open input image file!"
            return responseJson
        
        imageWidth = dataset.RasterXSize
        imageHeight = dataset.RasterYSize
        imageBandCount = dataset.RasterCount
        bandOption = " "
        if sampleExtension == ".jpg" or sampleExtension == ".png":
            if imageBandCount >= 3:
                bandOption = " -b 1 -b 2 -b 3 "
            else:
                bandOption = " -b 1 -b 1 -b 1 "

        xSampleCount = int((imageWidth-1)/sampleWidth + 1)
        ySampleCount = int((imageHeight-1)/sampleHeight + 1)
        max_workers = 10
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for yIndex in range(ySampleCount):
                yStart = yIndex * sampleHeight
                if yIndex == ySampleCount-1:
                    yStart = imageHeight-sampleHeight
                for xIndex in range(xSampleCount):
                    xStart = xIndex * sampleWidth
                    if xIndex == xSampleCount-1:
                        xStart = imageWidth-sampleWidth
                        
                    sampleIndex = str(yIndex*xSampleCount+xIndex)
                    outputSample = os.path.join(outDir, str(imageId)+"_"+sampleIndex+sampleExtension)
                    srcWinOption = f" -srcwin {xStart} {yStart} {sampleWidth} {sampleHeight} "
                    clipCmd = "gdal_translate " + imagePath + " " + outputSample + \
                        bandOption + srcWinOption
                    
                    sampleThumb = os.path.join(outDir, \
                        str(imageId)+"_"+sampleIndex+"_thumb"+sampleExtension)
                    thumbCmd = "gdal_translate " + outputSample + " " + sampleThumb + \
                        " -outsize 256 256"
                    kwargs = {
                        "cmd": clipCmd,
                        "aux.xml": outputSample + ".aux.xml",
                        "thumb_cmd": thumbCmd
                    }
                    executor.submit(clip_thread, **kwargs)


    except Exception as e:
        print("Catch exception, error is {}".format(e))
        responseJson["code"] = 500
        responseJson["msg"] = "Get exception when clip image sample: {}".format(e)
        return responseJson

    responseJson["code"] = 200
    responseJson["msg"] = "操作成功"
    responseJson["data"] = {
        "imagePath": imagePath,
        "imageId": imageId,
        "outDir": outDir,
        "sampleWidth": sampleWidth,
        "sampleHeight": sampleHeight,
        "sampleExtension": sampleExtension,
        "sampleCount": xSampleCount*ySampleCount
    }

    return responseJson

if __name__ == "__main__":
    clip_image_sample(
        "F:\\Data\\PIE-AI样本训练平台数据集\\武大GID\\large-scale\\rgb\\GF2_PMS1__L1A0000564539-MSS1.tif", 
        564539,\
        "F:\\Data\\PIE-AI样本训练平台数据集\\武大GID\\large-scale\\rgb\\samples",
        1024,
        1024,
        ".tif")