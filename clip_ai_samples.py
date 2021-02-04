import os, shutil, random
from osgeo import gdal
from clip_image_sample import clip_image_sample
from image_base_info import image_base_info

def clip_ai_samples(imageFile1, imageFile2, labelFile, imageId, outDir,\
    sampleWidth, sampleHeight, sampleExtension, trainValidRate):
    responseJson = {}

    if not imageFile2:
        image1DirName = "images"
        image2DirName = None       
    else:
        image1DirName = "A"
        image2DirName = "B"

    imageFile1TraningDir = os.path.join(outDir, "train")
    imageFile1TraningDir = os.path.join(imageFile1TraningDir, image1DirName)

    imageFile1ValidDir = os.path.join(outDir, "valid")
    imageFile1ValidDir = os.path.join(imageFile1ValidDir, image1DirName)
    if not os.path.exists(imageFile1ValidDir):
        os.makedirs(imageFile1ValidDir)

    image1ClipResponseJson = clip_image_sample(imageFile1, imageId, imageFile1TraningDir,\
        sampleWidth, sampleHeight, sampleExtension)
    if image1ClipResponseJson["code"] != 200:
        return image1ClipResponseJson
    
    if image2DirName:
        imageFile2TraningDir = os.path.join(outDir, "train")
        imageFile2TraningDir = os.path.join(imageFile2TraningDir, image2DirName)

        imageFile2ValidDir = os.path.join(outDir, "valid")
        imageFile2ValidDir = os.path.join(imageFile2ValidDir, image2DirName)
        if not os.path.exists(imageFile2ValidDir):
            os.makedirs(imageFile2ValidDir)

        image2ClipResponseJson = clip_image_sample(imageFile2, imageId, imageFile2TraningDir,\
            sampleWidth, sampleHeight, sampleExtension)
        if image2ClipResponseJson["code"] != 200:
            return image2ClipResponseJson
    
    labelTraningDir = os.path.join(outDir, "train")
    labelTraningDir = os.path.join(labelTraningDir, "labels")

    labelValidDir = os.path.join(outDir, "valid")
    labelValidDir = os.path.join(labelValidDir, "labels")
    if not os.path.exists(labelValidDir):
        os.makedirs(labelValidDir)

    labelClipResponseJson = clip_image_sample(labelFile, imageId, labelTraningDir,\
            sampleWidth, sampleHeight, sampleExtension)
    if labelClipResponseJson["code"] != 200:
        return labelClipResponseJson
    
    sampleCount = image1ClipResponseJson['data']['sampleCount']
    validSampleCount = int(sampleCount*(1-trainValidRate))
    if validSampleCount < 1:
        validSampleCount = 1
    
    firstClipSampleImage = str(imageId) + "_0" + sampleExtension
    firstClipSampleImage = os.path.join(imageFile1TraningDir, firstClipSampleImage)
    clipSampleInfo = image_base_info(firstClipSampleImage)
    clipSampleInfo = clipSampleInfo["data"]
    clipSampleInfo.pop("image")
    if not imageFile2:
        clipSampleInfo["srcImage"] = imageFile1      
        clipSampleInfo["/train/images"] = imageFile1TraningDir
        clipSampleInfo["/valid/images"] = imageFile1ValidDir
    else:
        clipSampleInfo["srcImage1"] = imageFile1
        clipSampleInfo["srcImage2"] = imageFile2
        clipSampleInfo["/train/A"] = imageFile1TraningDir
        clipSampleInfo["/train/B"] = imageFile2TraningDir
        clipSampleInfo["/valid/A"] = imageFile1ValidDir
        clipSampleInfo["/valid/B"] = imageFile2ValidDir

    clipSampleInfo["srcLabel"] = labelFile  
    clipSampleInfo["/valid/labels"] = labelValidDir
    clipSampleInfo["/train/labels"] = labelTraningDir
    clipSampleInfo["sampleCount"] = sampleCount
    clipSampleInfo["trainValidRate"] = trainValidRate
    
    validIndexList = random.sample(range(0, sampleCount+1), validSampleCount)
    for validIndexValue in validIndexList:
        imageValidFile = str(imageId)+"_"+str(validIndexValue)+sampleExtension
        thumbValidFile = str(imageId) + "_" + str(validIndexValue) + sampleExtension

        image1SrcFile = os.path.join(imageFile1TraningDir, imageValidFile)
        image1DstFile = os.path.join(imageFile1ValidDir, imageValidFile)
        shutil.move(image1SrcFile, image1DstFile)

        image1SrcThumb = os.path.join(imageFile1TraningDir, thumbValidFile)
        if os.path.exists(image1SrcThumb):
            image1DstThumb = os.path.join(imageFile1ValidDir, thumbValidFile)
            shutil.move(image1SrcThumb, image1DstThumb)

        if image2DirName:
            image2SrcFile = os.path.join(imageFile2TraningDir, imageValidFile)
            image2DstFile = os.path.join(imageFile2ValidDir, imageValidFile)
            shutil.move(image2SrcFile, image2DstFile)

            image2SrcThumb = os.path.join(imageFile2TraningDir, thumbValidFile)
            if os.path.exists(image2SrcThumb):
                image2DstThumb = os.path.join(imageFile2ValidDir, thumbValidFile)
                shutil.move(image2SrcThumb, image2DstThumb)
        
        labelSrcFile = os.path.join(labelTraningDir, imageValidFile)
        labelDstFile = os.path.join(labelValidDir, imageValidFile)
        shutil.move(labelSrcFile, labelDstFile)

        labelSrcThumb = os.path.join(labelTraningDir, thumbValidFile)
        if os.path.exists(labelSrcThumb):
            labelDstThumb = os.path.join(labelValidDir, thumbValidFile)
            shutil.move(labelSrcThumb, labelDstThumb)
    
    responseJson["code"] = 200
    responseJson["msg"] = "Image and label clip success!"
    responseJson["data"] = clipSampleInfo
    print(responseJson)

    return responseJson

if __name__ == "__main__":
    '''
    clip_ai_samples("F:\\Data\\PIE-AI样本训练平台数据集\\武大GID\\large-scale\\rgb\\GF2_PMS1__L1A0000564539-MSS1.tif",
        None,
        "F:\\Data\\PIE-AI样本训练平台数据集\\武大GID\\large-scale\\labels\\GF2_PMS1__L1A0000564539-MSS1_label.tif",
        564539,
        "F:\\Data\\PIE-AI样本训练平台数据集\\武大GID\\large-scale\\samples",
        1024,
        1024,
        ".tif",
        0.8)
    '''
    clip_ai_samples("/data/pie_data/wuhan_pie_ai/test_clip/GF2_PMS1__L1A0001015649-MSS1.tif",
        None,
        "/data/pie_data/wuhan_pie_ai/test_clip/GF2_PMS1__L1A0001015649-MSS1_label.tif",
        1015649,
        "/data/pie_data/wuhan_pie_ai/test_clip/1015649",
        1024,
        1024,
        ".tif",
        0.8)