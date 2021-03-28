from osgeo import ogr

def clip_geojson_sample(inputGeoJson, outDir, geoTrans, srcWidth, srcHeight,\
    sampleWidth, sampleHeight):
    responseJson = {}
    try:
        ogrDataset = ogr.Open(inputGeoJson)
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

    except Exception as e:
        print("Catch exception, error is {}".format(e))
        responseJson["code"] = 500
        responseJson["msg"] = "Get exception when clip geojson sample: {}".format(e)
        return responseJson

    return responseJson