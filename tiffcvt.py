import subimager.client
import subimager.omexml
import h5py
import numpy as np
import os
import urllib

def copy_tif_stack_to_hdf(dest, src, name, dtype, chunk):
    '''Copy a TIF stack to an hdf file
    
    dest - name of HDF5 file
    src - name of TIF stack
    name - path to stack in the hdf5 file
    dtype - type of data set
    '''
    url = "file:" + urllib.pathname2url(os.path.abspath(src))
    metadata = subimager.client.get_metadata(url)
    metadata = subimager.omexml.OMEXML(metadata)
    x = metadata.image(0).Pixels.SizeX
    y = metadata.image(0).Pixels.SizeY
    z = metadata.image(0).Pixels.SizeZ
    h5_file = h5py.File(dest, "a")
    h5_file.require_dataset(name, (y, x, z), dtype, chunks = chunk)
    for k in range(z):
        plane = subimager.client.get_image(url, index=k).astype(dtype)
        h5_file[name][:,:,k] = plane
    h5_file.close()
    
def copy_hdf_to_tif_stack(src, dest, name):
    url = "file:" + urllib.pathname2url(os.path.abspath(dest))
    h5_file = h5py.File(src, "r")
    prediction = h5_file[name]
    metadata = subimager.omexml.OMEXML()
    pixels = metadata.image(0).Pixels
    assert isinstance(pixels, subimager.omexml.OMEXML.Pixels)
    pixels.SizeX = prediction.shape[1]
    pixels.SizeY = prediction.shape[0]
    pixels.SizeZ = prediction.shape[2]
    pixels.DimensionOrder = subimager.omexml.DO_XYZCT
    pixels.PixelType = subimager.omexml.PT_FLOAT
    pixels.plane_count = prediction.shape[2]
    for i in range(prediction.shape[2]):
        pixels.Plane(i).TheZ = i
        pixels.Plane(i).TheT = 0
        pixels.Plane(i).PositionX = 0
        pixels.Plane(i).PositionY = 0
        pixels.Plane(i).PositionZ = i * 50
        
    xml = metadata.to_xml()
    for i in range(prediction.shape[2]):
        subimager.client.post_image(url, prediction[:,:,i],
                                    xml, index=str(i))
            
if __name__=="__main__":
    import sys
    subimager.client.start_subimager()
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "write":
            name = "predicted_train_labels"
            if len(sys.argv) > 2:
                name = sys.argv[2]
            dest = "../train_prediction.tif"
            if len(sys.argv) > 3:
                dest = sys.argv[3]
            copy_hdf_to_tif_stack("../challenge.h5", 
                                  dest, 
                                  name)
        else:
            copy_tif_stack_to_hdf("../challenge.h5", "../test-volume.tif", 
                                  "test_volume", np.float32, (64,64,5))
            copy_tif_stack_to_hdf("../challenge.h5", "../train-labels.tif",
                                  "train_labels", np.uint8, (64, 64, 5))
            copy_tif_stack_to_hdf("../challenge.h5", "../train-volume.tif",
                                  "train_volume", np.float32, (64, 64, 5))
    finally:
        subimager.client.stop_subimager()
else:
    h5_file = h5py.File("../challenge.h5")
    test_volume = h5_file["test_volume"]
    train_labels = h5_file["train_labels"]
    train_volume = h5_file["train_volume"]
    