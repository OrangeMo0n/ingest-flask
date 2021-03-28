import os
import shutil
from lxml.etree import Element, SubElement, ElementTree
from osgeo import gdal

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

def find_min_size(inputDir):
    imageFiles = walkDirFile(inputDir, ".png")
    width = 99999999
    height = 99999999
    for imageFile in imageFiles:
        imageDataset = gdal.Open(imageFile)
        imageWidth = imageDataset.RasterXSize
        imageHeight = imageDataset.RasterYSize

        if imageWidth < width:
            width = imageWidth
        if imageHeight < height:
            height = imageHeight
        
        del imageDataset
        imageDataset = None
    
    return width, height

def image_clean(inputDir, width, height, outputDir):
    imageFiles = walkDirFile(inputDir, ".png")
    print("Start do image clean...")

    for imageFile in imageFiles:
        imageDataset = gdal.Open(imageFile)
        imageWidth = imageDataset.RasterXSize
        imageHeight = imageDataset.RasterYSize

        outputFile = os.path.basename(imageFile)
        outputFile = os.path.join(outputDir, outputFile)

        if imageWidth != width or imageHeight != height:
            clipCmd = f"gdal_translate {imageFile} {outputFile} -srcwin \
                0 0 {width} {height}"
            cmdStatus = os.system(clipCmd)
            if cmdStatus != 0:
                print(f"gdal_translate failed!")
        else:
            shutil.copy(imageFile, outputFile)


def label_txt_to_xml(inputFile, outputFile, imageWidth, imageHeight):
    xMinArray = []
    yMinArray = []
    xMaxArray = []
    yMaxArray = []

    with open(inputFile, "r") as f:
        for line in f.readlines():
            line = line.strip("\n\t")
            dataArray = line.split("\t")
            if len(dataArray) != 13:
                continue
            xmin = float(dataArray[-4])
            ymin = float(dataArray[-3])
            xmax = float(dataArray[-2]) + xmin - 1
            ymax = float(dataArray[-1]) + ymin - 1

            if xmin > imageWidth-1 or ymin > imageHeight-1:
                continue
            if xmax > imageWidth-1:
                xmax = imageWidth-1
            if ymax > imageHeight-1:
                ymax = imageHeight-1
            
            if (xmax-xmin) < 1:
                continue
            if (ymax-ymin) < 1:
                continue

            xMinArray.append(xmin)
            yMinArray.append(ymin)
            xMaxArray.append(xmax)
            yMaxArray.append(ymax)
    
    featureCount = len(xMinArray)
    nodeRoot = Element('annotation')
    nodeFolder = SubElement(nodeRoot, 'folder')
    nodeFolder.text = 'VOC'
    nodeFilename = SubElement(nodeRoot, 'filename')
    nodeFilename.text = os.path.basename(inputFile).replace(".txt", "")
    nodeObjectNum = SubElement(nodeRoot, 'object_num')
    nodeObjectNum.text = str(featureCount)

    nodeSize = SubElement(nodeRoot, 'size')
    nodeWidth = SubElement(nodeSize, 'width')
    nodeWidth.text = str(imageWidth)
    nodeHeight = SubElement(nodeSize, 'height')
    nodeHeight.text = str(imageHeight)
    nodeDepth = SubElement(nodeSize, 'depth')
    nodeDepth.text = str(3)

    for index in range(featureCount):
        featureLabelName = str(index+1)

        nodeObject = SubElement(nodeRoot, 'object')
        nodeName = SubElement(nodeObject, 'name')
        nodeName.text = str(featureLabelName)
        nodeDifficult = SubElement(nodeObject, 'difficult')
        nodeDifficult.text = '0'

        nodeBndbox = SubElement(nodeObject, 'bndbox')
        nodeXmin = SubElement(nodeBndbox, 'xmin')
        nodeXmin.text = str(xMinArray[index])
        nodeYmin = SubElement(nodeBndbox, 'ymin')
        nodeYmin.text = str(yMinArray[index])
        nodeXmax = SubElement(nodeBndbox, 'xmax')
        nodeXmax.text = str(xMaxArray[index])
        nodeYmax = SubElement(nodeBndbox, 'ymax')
        nodeYmax.text = str(yMaxArray[index])
    
    if os.path.exists(outputFile):
        os.remove(outputFile)
    
    doc = ElementTree(nodeRoot)
    doc.write(outputFile, pretty_print=True)

    return True

if __name__ == "__main__":
    fileDir = "E:\\2UCAS-AOD\\中科院大学高清航拍目标数据集合\\CAR"
    outputDir = "E:\\2UCAS-AOD\\中科院大学高清航拍目标数据集合\\CAR_LABEL"
    if not os.path.exists(outputDir):
        os.makedirs(outputDir)
    
    imageSize = find_min_size(fileDir)
    image_clean(fileDir, imageSize[0], imageSize[1], outputDir)
    txtFiles = walkDirFile(fileDir)
    index = 0
    for txtFile in txtFiles:
        xmlFileName = os.path.basename(txtFile).replace(".txt", ".xml")
        xmlFile = os.path.join(outputDir, xmlFileName)
        index += 1
        print(f"{index}/{len(txtFiles)}: generate {xmlFileName}")
        label_txt_to_xml(txtFile, xmlFile, imageSize[0], imageSize[1])