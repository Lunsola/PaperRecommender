# Paper Recommender
Recommends papers to read based on papers you've already read

## Installation
Download all the files in this project and install GROBID's python client https://github.com/kermitt2/grobid_client_python

### Windows
GROBID is not fully supported on Windows PCs. Retrieve the Docker image from https://hub.docker.com/r/lfoppiano/grobid. This may also require using Ubuntu https://ubuntu.com/ or another Linux distribution.

Start up the image on Ubuntu (the final part of 'grobid:0.7.0' may vary if you get a different version of the image)

```
docker run -t --rm --init -p 8070:8070 lfoppiano/grobid:0.7.0
```

Make sure the IDE or terminal you are using is hooked up with the Docker image and then run as directed under usage.

## Usage
Place a starting PDF in a new folder where all subsequent PDFs will also be placed.

Run pick_pdf() and select the folder where PDFs will be passed to the program followed by the folder where structured XMLs should be placed. It will attempt to automatically pop up a folder selection menu if none are given.

```
pick_pdf [in_pdfs = input] [out_xmls = output]

optional arguments:
  -in_pdfs    Where PDFs will be added
  -out_xmls   Where XMLs and parsed PDFs will go
```

While program has not terminated, insert a new PDF in the folder chosen before and hit enter on the program once it is in place
