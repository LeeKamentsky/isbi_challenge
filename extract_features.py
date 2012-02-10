import numpy as np
from scipy.ndimage import gaussian_filter

fv = np.mgrid[-9:10,-9:10,0:1].reshape(3, 19*19).transpose()
blur_fv = np.mgrid[-36:37:4,-36:37:4,0:1].reshape(3, 19 * 19).transpose()
n_features = fv.shape[0] + blur_fv.shape[0]

def blur_image(img):
    '''Return the blurred image that's used when sampling'''
    return gaussian_filter(img, (4, 4, 1))

def extract_features(img, blur_img, indices, oob_value=65535):
    '''Extract the feature vector from a portion of the image
    
    img - a 3-d ndarray'ish object
    blur_img - image blurred with blur_image
    indices - an Nx3 array of indices of the pixels to have their values
              sampled.
    oob_value - value that signals out-of-bounds, default is 65535 which
                is far enough from the value range that it should be a class-
                signifier of an OOB pixel rather than something that can
                be part of a linear combination.
              
    returns an NxM matrix of features where M is the width of the feature vector
    
    '''
    sampler = np.ones((indices.shape[0], n_features), img.dtype) * oob_value
    for xfv, ximg, offset, end in (
        (fv, img, 0, fv.shape[0]), 
        (blur_fv, blur_img, fv.shape[0], n_features)):
        x = (indices[:, 0, np.newaxis] + xfv[np.newaxis, :, 0])
        y = (indices[:, 1, np.newaxis] + xfv[np.newaxis, :, 1])
        z = (indices[:, 2, np.newaxis] + xfv[np.newaxis, :, 2])
        #
        # Find only the good samples - the ones that are in-bounds
        #
        good = ((x >= 0) & (x < ximg.shape[0]) &
                (y >= 0) & (y < ximg.shape[1]) &
                (z >= 0) & (z < ximg.shape[2]))
        sampler[:, offset:end][good] = \
            ximg[x[good, :],
                 y[good, :],
                 z[good, :]]
    return sampler

    
