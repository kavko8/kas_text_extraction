FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN yes | apt-get install python3.8
RUN yes | apt-get install python3-pip
RUN pip install --upgrade pip
RUN apt-get install ffmpeg libsm6 libxext6  -y
RUN apt-get install poppler-utils -y
RUN mkdir PDF

WORKDIR .

COPY ./body /

RUN pip install -r requirements.txt

CMD ["python3", "main.py"]
