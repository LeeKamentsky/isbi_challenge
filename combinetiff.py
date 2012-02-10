import subimager.client
import numpy as np
import urllib
import os
subimager.client.start_subimager()

path = "c:/Temp/isbi_challenge/output/test_volume/"
url = "file:" + urllib.pathname2url(os.path.join(path, "test_prediction.tif"))
out_url = "file:" + urllib.pathname2url(os.path.join(path, "leek_test_prediction.tif"))
metadata = subimager.client.get_metadata(url)
for i in range(1,30):
    url = "file:" + urllib.pathname2url(os.path.join(path, "TrainPrediction%02d.tiff" % i))
    image = subimager.client.get_image(url)
    image = image / np.max(image)
    subimager.client.post_image(out_url, image, metadata, index = str(i-1), compresion="LZW")
    
subimager.client.stop_subimager()
