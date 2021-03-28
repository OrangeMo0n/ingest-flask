from osgeo import gdal, ogr

def vector_base_info(vectorPath):
    responseJson = {}
    try:
        ogrDriver = ogr.GetDriverByName("GeoJSON")
        ogrDataset = ogr.Open(vectorPath)
        if not ogrDataset:
            responseJson["code"] = 500
            responseJson["msg"] = "Failed to open vector!"
            return responseJson
        
        ogrLayer = ogrDataset.GetLayer()
        if not ogrLayer:
            responseJson["code"] = 500
            responseJson["msg"] = "Failed to get layer!"
            return responseJson
        
        featureDefn = ogrLayer.GetLayerDefn()
        fieldCount = featureDefn.GetFieldCount()
        for attrIndex in range(fieldCount):
            fieldDefn = featureDefn.GetFieldDefn(attrIndex)
            print(fieldDefn.GetNameRef(), ":", fieldDefn.GetFieldTypeName(fieldDefn.GetType()))
        
        featureCount = ogrLayer.GetFeatureCount()
        for featureIndex in range(featureCount):
            feature = ogrLayer.GetFeature(featureIndex)
            if not feature:
                continue
            geom = feature.GetGeometryRef()
            envelope = geom.GetEnvelope()
            print("Envelope:", envelope[0], envelope[1], envelope[2], envelope[3])
        
        vectorInfo = {
            "vector:": vectorPath,
            "featureCount": featureCount
        }
    except Exception as e:
        print("Catch exception, error is {}".format(e))
        responseJson["code"] = 500
        responseJson["msg"] = "Get exception when query image info: {}".format(e)
        return responseJson
    
    return responseJson

if __name__ == "__main__":
    vector_base_info("F:\\48.json")