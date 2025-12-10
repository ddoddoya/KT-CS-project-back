FROM paddlepaddle/paddle:2.6.0-gpu-cuda11.8-cudnn8

RUN apt-get update && apt-get install -y git wget unzip

# PaddleOCR install
RUN git clone https://github.com/PaddlePaddle/PaddleOCR.git /PaddleOCR

WORKDIR /PaddleOCR

# install requirements
RUN pip install -r requirements.txt

# install your extra python packages
RUN pip install opencv-python-headless==4.8.0.74 albumentations imgaug shapely pyclipper

ENV CUDA_VISIBLE_DEVICES=0
