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
        
        imageWkt = None
        imageSpatialRef = imageDataset.GetSpatialRef()
        if imageSpatialRef:
            imageWkt = imageSpatialRef.ExportToWkt()
        
        imageGeotransform = imageDataset.GetGeoTransform()
        xImageRes = imageGeotransform[1]
        yImageRes = abs(imageGeotransform[5])
        nodataValue = imageDataset.GetRasterBand(1).GetNoDataValue()

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
            "interleave": interleaveName,
            "wkt": imageWkt,
            "xRes": xImageRes,
            "yRes": yImageRes,
            "nodata": nodataValue
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

if __name__ == "__main__":
    image_base_info("F:\\Data\\PIE-AI样本训练平台数据集\\SECOND_train_set\\train\\A\\00003.png")