# S3存储的样本数据访问API
from boto3.session import Session
from botocore.client import Config
import torch.utils.data as data
import numpy as np

ACCESS_KEY = "AKIAT2NCQYSI3X7D52BZ"
SECRET_KEY = "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"
REGION = "cn-northwest-1"
PROFILE = 

class S3PytorchDataset(data.Dataset):
    def __init__(self, path):
        session = Session(aws_access_key_id=accessKey,
            aws_secret_access_key=secretKey,
            region_name=region)
        s3_config = Config(max_pool_connections=200, retries={'max_attempts': 20})
        self.s3 = session.client('s3', config=s3_config)

        self.bucketName = "pie-engine-test"
        keyNamePrefix = path + "images"

        paginator = self.s3.get_paginator('list_objects_v2')
        self.images = []
        responseIterator = paginator.paginate(
            Bucket=self.bucketName,
            Prefix=keyNamePrefix
        )
        for page in responseIterator:
            if "Contents" in page:
                for n in page["Contents"]:
                    key = n["Key"]
                    if ".jpg" in key or ".tif" in key or ".tiff" in key or \
                        ".png" in key or ".TIF" in key:
                        self.images.append(key)
        
        if len(self.images) == 0:
            raise RuntimeError("Found 0 images in subfolders of: " + path + "images" + "\n")
        
        self.loader = s3_dataset_loader