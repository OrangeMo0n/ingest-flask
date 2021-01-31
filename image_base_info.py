from osgeo import gdal

IMAGE_STRUCTURE_DOMAIN = "IMAGE_STRUCTURE"
INTERLEAVE_METAITEM = "INTERLEAVE"

def image_base_info(imagePath):
    responseJson = {}
    try:
        imageDataset = gdal.Open(imagePath)
        if not imageDataset:
            responseJson["code"] = 500
            responseJson["msg"] = "Failed to open image!"
            return responseJson
        
        imageWidth = imageDataset.RasterXSize
        imageHeight = imageDataset.RasterYSize
        bandCount = imageDataset.RasterCount
        bandDataType = imageDataset.GetRasterBand(1).DataType
        dataTypeName = gdal.GetDataTypeName(bandDataType)
        interleaveName = ""
        metadataDomainList = imageDataset.GetMetadataDomainList()
        if IMAGE_STRUCTURE_DOMAIN in metadataDomainList:
            metadataDict = imageDataset.GetMetadata_Dict(IMAGE_STRUCTURE_DOMAIN)
            if INTERLEAVE_METAITEM in metadataDict:
                interleaveName = metadataDict[INTERLEAVE_METAITEM]

        if interleaveName == "PIXEL":
            interleaveName = "BIP"
        elif interleaveName == "BAND":
            interleaveName = "BSQ"
        elif interleaveName == "LINE":
            interleaveName = "BIL"

        imageInfo = {
            "image": imagePath,
            "width": imageWidth,
            "height": imageHeight,
            "bandCount": bandCount,
            "bandDataType": dataTypeName,
            "interleave": interleaveName
        }
        print("imageInfo:", imageInfo)

    except Exception as e:
        print("Catch exception, error is {}".format(e))
        responseJson["code"] = 500
        responseJson["msg"] = "Get exception when query image info: {}".format(e)
        return responseJson
    
    responseJson["code"] = 200
    responseJson["msg"] = "操作成功"
    responseJson["data"] = imageInfo
    return responseJson