import os, shutil, random, traceback
from concurrent.futures import ThreadPoolExecutor
from osgeo import ogr, gdal
from lxml.etree import Element, SubElement, ElementTree
from image_base_info import image_base_info

def pixel_to_geo(xPixel, yPixel, geoTransform):
    xGeo = geoTransform[0] + xPixel*geoTransform[1] + yPixel*geoTransform[2]
    yGeo = geoTransform[3] + xPixel*geoTransform[4] + yPixel*geoTransform[5]

    return [xGeo, yGeo]

def geo_to_pixel(xGeo, yGeo, geoTransform):
    dTemp = geoTransform[1]*geoTransform[5] - geoTransform[2]*geoTransform[4];
    xPixel= (geoTransform[5]*(xGeo-geoTransform[0]) - \
        geoTransform[2]*(yGeo-geoTransform[3]))/dTemp + 0.5
    xPixel = int(xPixel)
    yPixel = (geoTransform[1]*(yGeo-geoTransform[3]) - \
        geoTransform[4]*(xGeo-geoTransform[0]))/dTemp + 0.5;
    yPixel = int(yPixel)

    return [xPixel, yPixel]

def normalize_pixel(pixel, size):
    pixel = int(pixel)
    if pixel < 0:
        pixel = 0
    if pixel > size-1:
        pixel = size-1
    
    return pixel

def walkDirFile(srcPath, ext=".json"):
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

def clip_task(**kwargs):
    xStart = kwargs.get("xStart", None)
    yStart = kwargs.get("yStart", None)
    xEnd = kwargs.get("xEnd", None)
    yEnd = kwargs.get("yEnd", None)
    geoTrans = kwargs.get("geoTrans", None)
    labelFile = kwargs.get("labelFile", None)
    sampleFile = kwargs.get("sampleFile", None)
    bandOption = kwargs.get("bandOption", None)
    isProj = kwargs.get("isProj", None)
    srcLabelFile = kwargs.get("srcLabelFile", None)
    srcImageFile = kwargs.get("srcImageFile", None)
    srcImageWidth = kwargs.get("srcImageWidth", None)
    srcImageHeight = kwargs.get("srcImageHeight", None)
    
    xSize = xEnd - xStart + 1
    ySize = yEnd - yStart + 1

    xStartCoord = xStart
    xEndCoord = xEnd
    yStartCoord = yStart
    yEndCoord = yEnd
    if isProj:
        coordList = pixel_to_geo(xStart, yEnd, geoTrans)
        xStartCoord = coordList[0]
        yStartCoord = coordList[1]
        coordList = pixel_to_geo(xEnd, yStart, geoTrans)
        xEndCoord = coordList[0]
        yEndCoord = coordList[1]
    
    clipOption = f"-clipdst {xStartCoord} {yStartCoord} {xEndCoord} {yEndCoord}"
    labelClipCmd = f'ogr2ogr -f "ESRI Shapefile" {labelFile} {clipOption} {srcLabelFile}'
    #labelClipCmd = f'ogr2ogr -f GeoJSON {labelFile} {clipOption} {srcLabelFile}'
    clipCmdStatus = os.system(labelClipCmd)
    if clipCmdStatus != 0:
        print("Do clip ogr2ogr cmd failed:", labelClipCmd)
        return
    
    ogrDataset = ogr.Open(labelFile)
    if not ogrDataset:
        print("Failed to open vector file:", labelFile)
        return
    
    ogrLayer = ogrDataset.GetLayer()
    if not ogrLayer:
        print("Failed to get layer", labelFile)
        return
    
    featureCount = ogrLayer.GetFeatureCount()
    print("featureCount:", featureCount, "labelFile:", os.path.basename(labelFile))
    if featureCount <= 0:
        print("Clip label have no features:", labelFile)
        ogrDataset = None
        os.remove(labelFile)
        os.remove(labelFile.replace(".shp", ".shx"))
        os.remove(labelFile.replace(".shp", ".prj"))
        os.remove(labelFile.replace(".shp", ".dbf"))
        return
    
    srcWinOption = f"-srcwin {xStart} {yStart} {xSize} {ySize}" 
    sampleClipCmd = f"gdal_translate {srcImageFile} {sampleFile} {bandOption} {srcWinOption}"
    sampleClipStatus = os.system(sampleClipCmd)
    if sampleClipStatus != 0:
        print("Do clip cmd failed:", sampleClipCmd)
        return
    sampleAuxXmlFile = sampleFile + ".aux.xml"
    if os.path.exists(sampleAuxXmlFile):
        os.remove(sampleAuxXmlFile)
    
    sampleDataset = gdal.Open(sampleFile)
    if not sampleDataset:
        print("Failed to open sample image file:", sampleFile)
        return
    sampleBandCount = sampleDataset.RasterCount

    featureDefn = ogrLayer.GetLayerDefn()
    fieldCount = featureDefn.GetFieldCount()
    labelNameIndex = 0
    for attrIndex in range(fieldCount):
        fieldDefn = featureDefn.GetFieldDefn(attrIndex)
        fieldName = fieldDefn.GetNameRef()
        if fieldName == "labelName":
            labelNameIndex = attrIndex
            break
    
    nodeRoot = Element('annotation')
    nodeFolder = SubElement(nodeRoot, 'folder')
    nodeFolder.text = 'VOC'
    nodeFilename = SubElement(nodeRoot, 'filename')
    nodeFilename.text = os.path.basename(sampleFile)
    nodeObjectNum = SubElement(nodeRoot, 'object_num')
    nodeObjectNum.text = str(featureCount)

    nodeSize = SubElement(nodeRoot, 'size')
    nodeWidth = SubElement(nodeSize, 'width')
    nodeWidth.text = str(xSize)
    nodeHeight = SubElement(nodeSize, 'height')
    nodeHeight.text = str(ySize)
    nodeDepth = SubElement(nodeSize, 'depth')
    nodeDepth.text = str(sampleBandCount)

    for index in range(featureCount):
        feature = ogrLayer.GetFeature(index)
        if not feature:
            continue
        geom = feature.GetGeometryRef()
        envelope = geom.GetEnvelope()

        xMin = envelope[0]
        xMax = envelope[1]
        yMin = envelope[2]
        yMax = envelope[3]

        if isProj:
            pixelList = geo_to_pixel(envelope[0], envelope[3], geoTrans)
            xMin = pixelList[0]
            yMin = pixelList[1]
            pixelList = geo_to_pixel(envelope[1], envelope[2], geoTrans)
            xMax = pixelList[0]
            yMax = pixelList[1]
        
        xMin = normalize_pixel(xMin - xStart, xSize)
        yMin = normalize_pixel(yMin - yStart, ySize)
        xMax = normalize_pixel(xMax - xStart, xSize)
        yMax = normalize_pixel(yMax - yStart, ySize)
        
        featureLabelName = feature.GetFieldAsString(labelNameIndex)

        nodeObject = SubElement(nodeRoot, 'object')
        nodeName = SubElement(nodeObject, 'name')
        nodeName.text = str(featureLabelName)
        nodeDifficult = SubElement(nodeObject, 'difficult')
        nodeDifficult.text = '0'

        nodeBndbox = SubElement(nodeObject, 'bndbox')
        nodeXmin = SubElement(nodeBndbox, 'xmin')
        nodeXmin.text = str(xMin)
        nodeYmin = SubElement(nodeBndbox, 'ymin')
        nodeYmin.text = str(yMin)
        nodeXmax = SubElement(nodeBndbox, 'xmax')
        nodeXmax.text = str(xMax)
        nodeYmax = SubElement(nodeBndbox, 'ymax')
        nodeYmax.text = str(yMax)
    
    xmlFile = labelFile.replace(".shp", ".xml")
    if os.path.exists(xmlFile):
        os.remove(xmlFile)
    
    doc = ElementTree(nodeRoot)
    doc.write(xmlFile, pretty_print=True)

    ogrDataset = None
    sampleDataset = None
    os.remove(labelFile)
    os.remove(labelFile.replace(".shp", ".shx"))
    os.remove(labelFile.replace(".shp", ".prj"))
    os.remove(labelFile.replace(".shp", ".dbf"))

def clip_ai_geojson_samples(geoJsonPath, imagePath, imageId, outDir, isProj,\
    sampleWidth, sampleHeight, imageSampleExtension, trainValidRate):
    responseJson = {}
    try:
        srcVectorFilePath = geoJsonPath
        geoJsonExtension = geoJsonExtension.split(".")[-1]
        if geoJsonExtension != "shp":
            geoJsonPath = geoJsonPath.replace("."+geoJsonExtension, ".shp")
            convertShpCmd = 'ogr2ogr -f "ESRI Shapefile" ' + geoJsonPath + " " + srcVectorFilePath
            if os.system(convertShpCmd) != 0:
                responseJson["code"] = 400
                responseJson["msg"] = "Src vector file cannot convert to esri shapefile do clip!"
                return responseJson
        
        trainDir = os.path.join(outDir, "train")
        imageTrainDir = os.path.join(trainDir, "images")
        labelTrainDir = os.path.join(trainDir, "labels")
        if not os.path.exists(imageTrainDir):
            os.makedirs(imageTrainDir)
        if not os.path.exists(labelTrainDir):
            os.makedirs(labelTrainDir)

        dataset = gdal.Open(imagePath)
        if not dataset:
            responseJson["code"] = 500
            responseJson["msg"] = "Failed to open input image file!"
            return responseJson
        
        imageWidth = dataset.RasterXSize
        imageHeight = dataset.RasterYSize
        imageBandCount = dataset.RasterCount
        imageGeoTrans = dataset.GetGeoTransform()

        bandOption = " "
        if imageSampleExtension == ".jpg" or imageSampleExtension == ".png":
            if imageBandCount >= 3:
                bandOption = " -b 1 -b 2 -b 3 "
            else:
                bandOption = " -b 1 -b 1 -b 1 "
        
        xSampleCount = int((imageWidth-1)/sampleWidth + 1)
        ySampleCount = int((imageHeight-1)/sampleHeight + 1)
        
        kwargs = {
            "xStart": 0,
            "yStart": 0,
            "xEnd": 0,
            "yEnd": 0,
            "geoTrans": imageGeoTrans,
            "labelFile": "",
            "sampleFile": "",
            "bandOption": bandOption,
            "isProj": isProj,
            "srcLabelFile": geoJsonPath,
            "srcImageFile": imagePath,
            "srcImageWidth": imageWidth,
            "srcImageHeight": imageHeight
        }

        max_workers = 1
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for yIndex in range(ySampleCount):
                yStart = yIndex * sampleHeight
                if yIndex == ySampleCount-1:
                    yStart = imageHeight-sampleHeight               
                yEnd = yStart + sampleHeight - 1
                for xIndex in range(xSampleCount):
                    xStart = xIndex * sampleWidth
                    if xIndex == xSampleCount-1:
                        xStart = imageWidth-sampleWidth
                    xEnd = xStart + sampleWidth - 1
                    
                    sampleIndex = yIndex * xSampleCount + xIndex

                    outputLabelFile = os.path.join(labelTrainDir, \
                        str(imageId)+"_"+str(sampleIndex)+".shp")
                    outputSampleFile = os.path.join(imageTrainDir, \
                        str(imageId)+"_"+str(sampleIndex)+imageSampleExtension)
                    
                    kwargs["xStart"] = xStart
                    kwargs["yStart"] = yStart
                    kwargs["xEnd"] = xEnd
                    kwargs["yEnd"] = yEnd
                    kwargs["labelFile"] = outputLabelFile
                    kwargs["sampleFile"] = outputSampleFile

                    #clip_task(**kwargs)
                    executor.submit(clip_task, **kwargs)

        clipJsonTempFileList = walkDirFile(labelTrainDir, ".shp")
        if clipJsonTempFileList:
            for tempFile in clipJsonTempFileList:
                os.remove(tempFile)
                shxFile = tempFile.replace(".shp", ".shx")
                if os.path.exists(shxFile):
                    os.remove(shxFile)
                prjFile = tempFile.replace(".shp", ".prj")
                if os.path.exists(prjFile):
                    os.remove(prjFile)
                dbfFile = tempFile.replace(".shp", ".dbf")
                if os.path.exists(dbfFile):
                    os.remove(dbfFile)
        else:
            responseJson["code"] = 201
            responseJson["msg"] = "No sample image and label can clip from json!"
            return responseJson

        validDir = os.path.join(outDir, "valid")
        imageValidDir = os.path.join(validDir, "images")
        labelValidDir = os.path.join(validDir, "labels")
        if not os.path.exists(imageValidDir):
            os.makedirs(imageValidDir)
        if not os.path.exists(labelValidDir):
            os.makedirs(labelValidDir)

        clipLabelXMLList = walkDirFile(labelTrainDir, ".xml")
        clipSampleList = walkDirFile(imageTrainDir, imageSampleExtension)
        sampleCount = len(clipSampleList)
        validSampleCount = int(sampleCount*(1-trainValidRate))
        if validSampleCount < 1:
            validSampleCount = 1
        
        # 读取第一张裁切影像的信息
        firstClipSampeImage = clipSampleList[0]
        sampleBaseInfo = image_base_info(firstClipSampeImage)
        if sampleBaseInfo["code"] != 200:
            return sampleBaseInfo

        validIndexList = random.sample(range(0, sampleCount+1), validSampleCount)
        for index in validIndexList:
            clipLabelFile = clipLabelXMLList[index]
            clipLabelFileName = os.path.basename(clipLabelFile)
            clipSampleFileName = clipLabelFileName.replace(".xml", imageSampleExtension)
            clipSampleFile = os.path.join(imageTrainDir, clipSampleFileName)

            validLabelFile = os.path.join(labelValidDir, clipLabelFileName)
            validSampelFile = os.path.join(imageValidDir, clipSampleFileName)

            shutil.move(clipSampleFile, validSampelFile)
            shutil.move(clipLabelFile, validLabelFile)
        
        clipSampleInfo = sampleBaseInfo["data"]
        clipSampleInfo.pop("image")
        clipSampleInfo["srcImage"] = imagePath
        clipSampleInfo["srcGeoJson"] = srcVectorFilePath
        clipSampleInfo["sampleCount"] = sampleCount
        clipSampleInfo["trainValidRate"] = trainValidRate
        clipSampleInfo["/train/images"] = imageTrainDir
        clipSampleInfo["/train/labels"] = labelTrainDir
        clipSampleInfo["/valid/images"] = imageValidDir
        clipSampleInfo["/valid/labels"] = labelValidDir

        if srcVectorFilePath != geoJsonPath:
            os.remove(geoJsonPath)
            if os.path.exists(geoJsonPath.replace(".shp", ".prj")):
                os.remove(geoJsonPath.replace(".shp", ".prj"))
            if os.path.exists(geoJsonPath.replace(".shp", ".dbf")):
                os.remove(geoJsonPath.replace(".shp", ".dbf"))
            if os.path.exists(geoJsonPath.replace(".shp", ".shx")):
                os.remove(geoJsonPath.replace(".shp", ".shx"))
    except Exception as e:
        print("Catch exception, error is {}".format(e))
        print('traceback.format_exc():\n%s' % traceback.format_exc())
        responseJson["code"] = 500
        responseJson["msg"] = "Get exception when clip geojson sample: {}".format(e)
        return responseJson

    responseJson["code"] = 200
    responseJson["msg"] = "GeoJson and image clip success!"
    responseJson["data"] = clipSampleInfo

    print(responseJson)

    return responseJson

if __name__ == "__main__":    
    clip_ai_geojson_samples("F:\\Data\\gf2_1.shp",
    "F:\\Data\\PIE-AI样本训练平台数据集\\GF2_PMS1_E113.7_N23.1_20190311_L1A0003877356-MSS1_RPCOrthorectification_PanSharpening.tif",
    4539,
    "F:\\Data\\samples",
    True,
    1024,
    1024,
    ".tif",
    0.8)
    '''
    clip_ai_geojson_samples("/data/pie_data/wuhan_pie_ai/test_clip/000.json", \
        "/data/pie_data/wuhan_pie_ai/test_clip/GF2_PMS1__L1A0001015649-MSS1.tif", \
        4539, \
        "/data/pie_data/wuhan_pie_ai/test_clip/samples", \
        False, \
        1024, \
        1024, \
        ".tif", \
        0.8)
    '''
    
    
