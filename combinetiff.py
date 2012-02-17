import subimager.client
import numpy as np
import urllib
import os
import sys
subimager.client.start_subimager()

if len(sys.argv) > 1:
    path = sys.argv[1]
else:
    path = "c:/Temp/isbi_challenge/output/test_volume"
out_url = "file:" + urllib.pathname2url(os.path.join(path, "leek_test_prediction.tif"))

metadata = r"""<?xml version="1.0" encoding="UTF-8"?>
<OME xmlns="http://www.openmicroscopy.org/Schemas/OME/2011-06" 
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
     xsi:schemaLocation="http://www.openmicroscopy.org/Schemas/OME/2011-06 
     http://www.openmicroscopy.org/Schemas/OME/2011-06/ome.xsd">
  <Image ID="Image:0" Name="test_prediction.tif">
    <AcquiredDate>2012-02-08T14:38:24</AcquiredDate>
    <Description/>
    <Pixels DimensionOrder="XYCZT" 
            ID="Pixels:0" 
            SizeC="1" 
            SizeT="1" 
            SizeX="512" 
            SizeY="512" 
            SizeZ="30" 
            Type="float">
      <Channel ID="Channel:0:0" SamplesPerPixel="1"><LightPath/></Channel>
      <BinData xmlns="http://www.openmicroscopy.org/Schemas/BinaryFile/2011-06" 
               BigEndian="true" Length="0"/>
    </Pixels></Image>
    <StructuredAnnotations xmlns="http://www.openmicroscopy.org/Schemas/SA/2011-06">
      <XMLAnnotation ID="Annotation:0">
        <Value>
          <OriginalMetadata xmlns="openmicroscopy.org/OriginalMetadata">
            <Key>PhotometricInterpretation</Key>
            <Value>BlackIsZero</Value>
          </OriginalMetadata>
        </Value>
      </XMLAnnotation><XMLAnnotation ID="Annotation:1">
        <Value>
          <OriginalMetadata xmlns="openmicroscopy.org/OriginalMetadata">
            <Key>MetaDataPhotometricInterpretation</Key>
            <Value>Monochrome</Value>
          </OriginalMetadata>
        </Value>
      </XMLAnnotation>
      <XMLAnnotation ID="Annotation:2">
        <Value>
          <OriginalMetadata xmlns="openmicroscopy.org/OriginalMetadata">
            <Key>Unit</Key><Value>micron</Value>
          </OriginalMetadata>
        </Value>
      </XMLAnnotation>
      <XMLAnnotation ID="Annotation:3">
        <Value>
          <OriginalMetadata xmlns="openmicroscopy.org/OriginalMetadata">
            <Key>ImageLength</Key><Value>512</Value>
          </OriginalMetadata>
        </Value>
      </XMLAnnotation>
      <XMLAnnotation ID="Annotation:4">
        <Value>
          <OriginalMetadata xmlns="openmicroscopy.org/OriginalMetadata">
            <Key>NewSubfileType</Key><Value>0</Value>
          </OriginalMetadata>
        </Value>
      </XMLAnnotation>
      <XMLAnnotation ID="Annotation:5">
        <Value>
          <OriginalMetadata xmlns="openmicroscopy.org/OriginalMetadata">
            <Key>BitsPerSample</Key><Value>32</Value>
          </OriginalMetadata>
        </Value>
      </XMLAnnotation>
      <XMLAnnotation ID="Annotation:6">
        <Value>
          <OriginalMetadata xmlns="openmicroscopy.org/OriginalMetadata">
            <Key>SamplesPerPixel</Key><Value>1</Value>
          </OriginalMetadata>
        </Value>
      </XMLAnnotation>
      <XMLAnnotation ID="Annotation:7">
        <Value>
          <OriginalMetadata xmlns="openmicroscopy.org/OriginalMetadata">
            <Key>Compression</Key><Value>Uncompressed</Value>
          </OriginalMetadata>
        </Value>
      </XMLAnnotation>
      <XMLAnnotation ID="Annotation:8">
        <Value>
          <OriginalMetadata xmlns="openmicroscopy.org/OriginalMetadata">
            <Key>min</Key><Value>0.0</Value>
          </OriginalMetadata>
        </Value>
      </XMLAnnotation>
      <XMLAnnotation ID="Annotation:9">
        <Value>
          <OriginalMetadata xmlns="openmicroscopy.org/OriginalMetadata">
            <Key>NumberOfChannels</Key><Value>1</Value>
          </OriginalMetadata>
        </Value>
      </XMLAnnotation>
      <XMLAnnotation ID="Annotation:10">
        <Value>
          <OriginalMetadata xmlns="openmicroscopy.org/OriginalMetadata">
            <Key>loop</Key><Value>false</Value>
          </OriginalMetadata>
        </Value>
      </XMLAnnotation>
      <XMLAnnotation ID="Annotation:11">
        <Value>
          <OriginalMetadata xmlns="openmicroscopy.org/OriginalMetadata">
            <Key>MetaMorph</Key><Value>no</Value>
          </OriginalMetadata>
        </Value>
      </XMLAnnotation>
      <XMLAnnotation ID="Annotation:12">
        <Value>
          <OriginalMetadata xmlns="openmicroscopy.org/OriginalMetadata">
            <Key>ImageWidth</Key><Value>512</Value>
          </OriginalMetadata>
        </Value>
      </XMLAnnotation>
      <XMLAnnotation ID="Annotation:13">
        <Value>
          <OriginalMetadata xmlns="openmicroscopy.org/OriginalMetadata">
            <Key>SampleFormat</Key><Value>IEEE floating point</Value>
          </OriginalMetadata>
        </Value>
      </XMLAnnotation>
      <XMLAnnotation ID="Annotation:14">
        <Value>
          <OriginalMetadata xmlns="openmicroscopy.org/OriginalMetadata">
            <Key>images</Key><Value>30</Value>
          </OriginalMetadata>
        </Value>
      </XMLAnnotation>
      <XMLAnnotation ID="Annotation:15">
        <Value>
          <OriginalMetadata xmlns="openmicroscopy.org/OriginalMetadata">
            <Key>ImageJ</Key><Value>1.45f</Value>
          </OriginalMetadata>
        </Value>
      </XMLAnnotation>
      <XMLAnnotation ID="Annotation:16">
        <Value>
          <OriginalMetadata xmlns="openmicroscopy.org/OriginalMetadata">
            <Key>max</Key><Value>255.0</Value>
          </OriginalMetadata>
        </Value>
      </XMLAnnotation>
   </StructuredAnnotations>
  </OME>"""

for i in range(1,31):
    url = "file:" + urllib.pathname2url(os.path.join(path, "TrainPrediction%02d.tiff" % i))
    image = subimager.client.get_image(url)
    image = image / np.max(image)
    subimager.client.post_image(out_url, image, metadata, index = str(i-1), compression="LZW")
    
subimager.client.stop_subimager()
