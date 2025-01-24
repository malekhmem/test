import os

class Config:
    MODEL_NAME = "Malekhmem/ActiaMistral"
    HUGGINGFACE_TOKEN = os.environ.get('HUGGING_FACE_API_TOKEN')
