import numpy as np
import tiffcvt

def make_ordinal_image(img):
    '''Order pixels by intensity and then give them the intensity of that pixel'''
    r = np.random.RandomState()
    r.seed(12345)
    order = np.lexsort([r.uniform(size=np.prod(img.shape)), img.flatten()])
    result = np.zeros(len(order), np.float32)
    result[order] = np.arange(len(order)).astype(np.float32)
    result.shape = img.shape
    result = result / len(order)
    return result

if __name__ == "__main__":
    import sys
    import subimager.client
    f = tiffcvt.h5_file
    img_in = f[sys.argv[1]]
    img_out = f.require_dataset(sys.argv[2], img_in.shape, np.float32)
    for z in range(img_in.shape[2]):
        img_out[:,:,z] = make_ordinal_image(img_in[:,:,z])
    subimager.client.start_subimager()
    tiffcvt.copy_hdf_to_tif_stack("../challenge.h5", sys.argv[3], sys.argv[2])
    subimager.client.stop_subimager()