from osgeo import gdal
import shapely
from shapely.geometry import Polygon,MultiPoint
import os
import numpy as np
from lxml.etree import Element, SubElement, ElementTree

def clip_image_label(imageFile, labelFile, outputDir, outputLabelFile, width=1024, height=1024):
    responseJson = {}
    try:
        # (1) 读取待处理的影像图片文件
        imageDataset = gdal.Open(imageFile)
        if not imageDataset:
            responseJson["code"] = 501
            responseJson["msg"] = "Failed to open image!"
            return responseJson
        
        imageWidth = imageDataset.RasterXSize
        imageHeight = imageDataset.RasterYSize
        bandCount = imageDataset.RasterCount

        baseImageName = os.path.basename(imageFile)
        baseImageName = baseImageName.split(".")[0]

        tileXCount = int((imageWidth-1)/width) + 1
        tileYCount = int((imageHeight-1)/height) + 1

        # （2）读取待处理的标注文件
        labelList = []
        index = 0
        f = open(labelFile, "r", encoding="utf-8")
        lineData = f.readline()
        while lineData:
            lineData = f.readline()
            index += 1
            if index <= 2:
                continue
            
            labelInfoList = lineData.split(" ")
            coordArray = []
            for coordIndex in range(8):
                coordArray.append(float(labelInfoList[coordIndex]))
            npArray = np.array(coordArray).reshape(4, 2)
            poly = Polygon(npArray)

            label["poly"] = poly
            label["labelName"] = labelInfoList[8]
            labelList.append(label)

        format = "GTiff"
        driver = gdal.GetDriverByName(format)

        for xindex in range(tileXCount):
            xoff = xindex*width
            xsize = width
            if xindex == tileXCount-1:
                xoff = imageWidth-xsize
                #xsize = (imageWidth-1)%width + 1
            for yindex in range(tileYCount):
                yoff = yindex*height
                ysize = height
                if yindex == tileYCount-1:
                    yoff = imageHeight-ysize
                    #ysize = (imageHeight-1)%height + 1

                tileBound = [xoff, yoff, xoff, yoff+ysize-1, xoff+xsize-1, yoff+ysize-1, xoff+xsize-1, yoff]
                tileBoundArray = np.array(tileBound).reshape(4, 2)
                tilePoly = Polygon(tileBoundArray)

                intersectLabels = []
                for label in labelList:
                    labelPoly = label["poly"]
                    if not labelPoly.intersects(tilePoly):
                        continue
                    intersectPoly = labelPoly.intersection(tilePoly)
                    if intersectPoly.area < 0.5 * tilePoly.area:
                        continue

                    intersectLabel = {
                        "poly": intersectPoly,
                        "labelName": label["labelName"] }
                    intersectLabels.append(intersectLabel)
                    
                
                if len(intersectLabels) <= 0:
                    continue
                    
                nodeRoot = Element('annotation')
                nodeFolder = SubElement(nodeRoot, 'folder')
                nodeFolder.text = 'VOC'
                nodeFilename = SubElement(nodeRoot, 'filename')
                nodeFilename.text = f"{baseImageName}_{yindex}_{xindex}"
                nodeObjectNum = SubElement(nodeRoot, 'object_num')
                nodeObjectNum.text = str(len(intersectLabels))

                nodeSize = SubElement(nodeRoot, 'size')
                nodeWidth = SubElement(nodeSize, 'width')
                nodeWidth.text = str(width)
                nodeHeight = SubElement(nodeSize, 'height')
                nodeHeight.text = str(height)
                nodeDepth = SubElement(nodeSize, 'depth')
                nodeDepth.text = str(bandCount)

                for index in range(len(intersectLabels)):
                    xCoords, yCoords = intersectLabels[index]["poly"].exterior.coords.xy
                    xmin = min(xCoords)
                    xmax = max(xCoords)
                    ymin = min(yCoords)
                    ymax = max(yCoords)

                    featureLabelName = intersectLabels[index]["labelName"]

                    nodeObject = SubElement(nodeRoot, 'object')
                    nodeName = SubElement(nodeObject, 'name')
                    nodeName.text = featureLabelName
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

                outputFile = f"{baseImageName}_{yindex}_{xindex}.tif"
                outputFile = os.path.join(outputDir, outputFile)
                outputDs = driver.Create(outputFile, width, height,
                    bandCount, gdal.GDT_Byte)
                
                for iband in range(bandCount):
                    inputBandData = imageDataset.GetRasterBand(iband+1).\
                        ReadAsArray(xoff, yoff, xsize, ysize, xsize, ysize)
                    outputDs.GetRasterBand(iband+1).WriteArray(inputBandData, 
                        0, 0)
                
                del outputDs
                outputDs = None
    except Exception as e:
        responseJson["code"] = 500
        responseJson["msg"] = "catch exception when do clip image and label!"
        return responseJson

    responseJson["code"] = 200
    responseJson["msg"] = "do clip success!"
    return responseJson

if __name__ == "__main__":
    clip_image_label("E:\\1DOTA\\train\\images\\P0000.png", \
        "E:\\1DOTA\\train\\labelTxt-v1.5\\DOTA-v1.5_train_hbb\\P0000.txt", \
        "E:\\1DOTA\\train\\labelTxt-v1.5", \
        "")