from osgeo import ogr, gdal
import os
from concurrent.futures import ThreadPoolExecutor
from lxml.etree import Element, SubElement, tostring
from xml.dom.minidom import parseString

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
    if pixel < 0:
        pixel = 0
    if pixel > size-1:
        pixel = size-1
    
    return pixel

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
        coordList = pixel_to_geo(xStart, yStart, geoTrans)
        xStartCoord = coordList[0]
        yStartCoord = coordList[1]
        coordList = pixel_to_geo(xEnd, yEnd, geoTrans)
        xEndCoord = coordList[0]
        yEndCoord = coordList[1]
    
    clipOption = f"-clipdst {xStartCoord} {yStartCoord} {xEndCoord} {yEndCoord}"
    labelClipCmd = f"ogr2ogr -f GeoJSON {labelFile} {clipOption} {srcLabelFile}"
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
    if featureCount <= 0:
        print("Clip label have no features:", labelFile)
        return
    
    srcWinOption = f"-srcwin {xStart} {yStart} {xSize} {ySize}" 
    sampleClipCmd = f"gdal_translate {srcImageFile} {sampleFile} {bandOption} {srcWinOption}"
    sampleClipStatus = os.system(sampleClipCmd)
    if sampleClipStatus != 0:
        print("Do clip cmd failed:", sampleClipCmd)
        return

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
    
    node_root = Element('annotation')
    node_folder = SubElement(node_root, 'folder')
    node_folder.text = 'VOC'
    node_filename = SubElement(node_root, 'filename')
    node_filename.text = os.path.basename(sampleFile)
    node_object_num = SubElement(node_root, 'object_num')
    node_object_num.text = str(featureCount)

    node_size = SubElement(node_root, 'size')
    node_width = SubElement(node_size, 'width')
    node_width.text = str(xSize)
    node_height = SubElement(node_size, 'height')
    node_height.text = str(ySize)
    node_depth = SubElement(node_size, 'depth')
    node_depth.text = str(sampleBandCount)

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
            pixelList = geo_to_pixel(xMin, yMin, geoTrans)
            xMin = pixelList[0]
            yMin = pixelList[1]
            pixelList = geo_to_pixel(xMax, yMax, geoTrans)
            xMax = pixelList[0]
            yMax = pixelList[1]
        
        xMin = normalize_pixel(xMin - xStart, xSize)
        yMin = normalize_pixel(yMin - yStart, ySize)
        xMax = normalize_pixel(xMax - xStart, xSize)
        yMax = normalize_pixel(yMax - yStart, ySize)
        
        featureLabelName = feature.GetFieldAsString(labelNameIndex)

        node_object = SubElement(node_root, 'object')
        node_name = SubElement(node_object, 'name')
        node_name.text = str(featureLabelName)
        node_difficult = SubElement(node_object, 'difficult')
        node_difficult.text = '0'

        node_bndbox = SubElement(node_object, 'bndbox')
        node_xmin = SubElement(node_bndbox, 'xmin')
        node_xmin.text = str(xMin)
        node_ymin = SubElement(node_bndbox, 'ymin')
        node_ymin.text = str(yMin)
        node_xmax = SubElement(node_bndbox, 'xmax')
        node_xmax.text = str(xMax)
        node_ymax = SubElement(node_bndbox, 'ymax')
        node_ymax.text = str(yMax)
    
    xml = tostring(node_root, pretty_print = True)
    dom = parseString(xml)

    xmlFile = labelFile.replace(".json", ".xml")
    if os.path.exists(xmlFile):
        os.remove(xmlFile)
    with open(xmlFile, 'w') as f:
        f.write(dom.toprettyxml(indent='\t', encoding='utf-8'))

def clip_ai_geojson_samples(geoJsonPath, imagePath, imageId, outDir, isProj,\
    sampleWidth, sampleHeight, imageSampleExtension):
    responseJson = {}
    try:
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
        dTemp = imageGeoTrans[1]*imageGeoTrans[5]-imageGeoTrans[2]*imageGeoTrans[4]

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
        #with ThreadPoolExecutor(max_workers=max_workers) as executor:
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
                    str(imageId)+"_"+str(sampleIndex)+".json")
                outputSampleFile = os.path.join(imageTrainDir, \
                    str(imageId)+"_"+str(sampleIndex)+imageSampleExtension)
                
                kwargs["xStart"] = xStart
                kwargs["yStart"] = yStart
                kwargs["xEnd"] = xEnd
                kwargs["yEnd"] = yEnd
                kwargs["labelFile"] = outputLabelFile
                kwargs["sampleFile"] = outputSampleFile

                clip_task(**kwargs)

        validDir = os.path.join(outDir, "valid")
        imageValidDir = os.path.join(validDir, "images")
        labelValidDir = os.path.join(validDir, "labels")
        if not os.path.exists(imageValidDir):
            os.makedirs(imageValidDir)
        if not os.path.exists(labelValidDir):
            os.makedirs(labelValidDir)
    except Exception as e:
        print("Catch exception, error is {}".format(e))
        responseJson["code"] = 500
        responseJson["msg"] = "Get exception when clip geojson sample: {}".format(e)
        return responseJson
    
    return responseJson

if __name__ == "__main__":
    clip_ai_geojson_samples("F:\\Data\\PIE-AI样本训练平台数据集\\武大GID\\large-scale\\rgb\\000.json",
    "F:\\Data\\PIE-AI样本训练平台数据集\\武大GID\\large-scale\\rgb\\GF2_PMS1__L1A0000564539-MSS1.tif",
    4539,
    "F:\\Data\\PIE-AI样本训练平台数据集\\武大GID\\large-scale\\samples",
    False,
    1024,
    1024,
    ".tif")
    