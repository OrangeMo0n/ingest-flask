import json
from clip_ai_samples import clip_ai_samples

if __name__ == "__main__":
    '''
    config_path = "F:\\Data\\PIE-AI样本训练平台数据集\\武大GID\\large-scale\\clip_sample.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        params = json.load(f)
    '''

    config = input()
    params = json.load(config)

    srcImage1List = params["srcImage1"]
    srcImage2List = params["srcImage2"]
    srcLabelList = params["srcLabel"]

    if len(srcImage1List) != len(srcLabelList):
        print("srcImage list length must equal srcLabel list length!")
        exit(1)

    sampleType = params["type"]
    if sampleType == "change_detection":
        if len(srcImage1List) != len(srcImage2List):
            print("srcImage1 list length must equal srcImage2 list length!")
            exit(2)
    
    sampleWidth = params["sampleWidth"]
    sampleHeight = params["sampleHeight"]
    sampleExtension = params["sampleExtension"]
    sampleOutDir = params["outDir"]
    trainValidRate = params["trainValidRate"]

    for index in range(len(srcImage1List)):
        print("============================================================")
        print(f"Progress {index+1} / {len(srcImage1List)}: ...")
        srcImage1 = srcImage1List[index]
        srcImage2 = None
        if srcImage2List:
            srcImage2 = srcImage2List[index]
        
        srcLabel = srcLabelList[index]
        if sampleType == "segmentation" or sampleType == "change_detection":
            clip_ai_samples(srcImage1, srcImage2, srcLabel, \
                index, sampleOutDir, sampleWidth, sampleHeight, \
                sampleExtension, trainValidRate)
    
    print("Finished!")