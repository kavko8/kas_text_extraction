This repository contains source code and install instructions for extracting text body from slovene academic .pdf texts (BSc MSc and PhD). This code extracts the body to .txt and .json (json is segmented by chapters) format.


#### Prerequisites
- Docker
- Linux OS
- (opt.) python3
- (opt.) python3 virtual environment

Please refere to https://docs.docker.com/get-docker/ for install instructions

#### Usage
WITH DOCKER:
- git clone https://github.com/kavko8/kas_text_extraction.git
- cd kas_text_extraction
- docker build -t text_extract .
- docker run -it -v ABS_PATH_TO_FOLDER_CONTAINING_PDF:/PDF --name text_extract text_extract:latest
- This should make two new directories nammed "json" and "txt" in your ABS_PATH_TO_FOLDER_CONTAINING_PDF containing text bodies in .txt and .json format
  
WITHOUT DOCKER:
- git clone https://github.com/kavko8/kas_text_extraction.git
- cd kas_text_extraction/body
- mkdir PDF
- place your .pdf files in the newly created PDF folder
- python3 -m venv venv
- source venv/bin/activate
- pip install -r requirements.txt
- python3 main.py