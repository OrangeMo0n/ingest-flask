from osgeo import gdal
import os
import random
from clip_image_sample import clip_image_sample

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

    image1ClipResponseJson = clip_image_sample(imageFile1, imageId, imageFile1TraningDir,\
        sampleWidth, sampleHeight, sampleExtension)
    
    if image2DirName:
        imageFile2TraningDir = os.path.join(outDir, "train")
        imageFile2TraningDir = os.path.join(imageFile2TraningDir, image2DirName)

        imageFile2ValidDir = os.path.join(outDir, "valid")
        imageFile2ValidDir = os.path.join(imageFile2ValidDir, image2DirName)

        image2ClipResponseJson = clip_image_sample(imageFile2, imageId, imageFile2TraningDir,\
            sampleWidth, sampleHeight, sampleExtension)
    
    labelTraningDir = os.path.join(outDir, "train")
    labelTraningDir = os.path.join(imageFile1TraningDir, "labels")

    labelValidDir = os.path.join(outDir, "valid")
    labelValidDir = os.path.join(labelValidDir, "labels")

    labelClipResponseJson = clip_image_sample(labelFile, imageId, labelTraningDir,\
            sampleWidth, sampleHeight, sampleExtension)
    
    sampleCount = image1ClipResponseJson['data']['sampleCount']