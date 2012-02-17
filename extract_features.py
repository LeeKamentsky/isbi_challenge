import numpy as np
from scipy.ndimage import gaussian_filter, laplace

fv = np.mgrid[-9:10,-9:10,0:1].reshape(3, 19*19).transpose()
log_fv = np.mgrid[-27:28:3,-27:28:3,0:1].reshape(3, 19 * 19).transpose()
blur_fv = np.mgrid[-72:73:8, -72:73:8, 0:1].reshape(3, 19 * 19).transpose()
n_features = fv.shape[0] + blur_fv.shape[0] + log_fv.shape[0]

def blur_image(img):
    '''Return the blurred image that's used when sampling'''
    blur = np.zeros(list(img.shape)+[2], img.dtype)
    for z in range(img.shape[2]):
        blur[:,:,z, 0] = laplace(gaussian_filter(img[:,:,z], 3))
        blur[:,:,z, 1] = gaussian_filter(img[:,:,z], 5)
    return blur

def extract_features(img, blur, indices):
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
    log_img = blur[:,:,:,0]
    blur_img = blur[:,:,:,1]
    sampler = np.ones((indices.shape[0], n_features), img.dtype)
    for xfv, ximg, offset, end in (
        (fv, img, 0, fv.shape[0]), 
        (log_fv, log_img, fv.shape[0], fv.shape[0] + log_fv.shape[0]),
        (blur_fv, blur_img, fv.shape[0] + log_fv.shape[0], n_features)):
        x = (indices[:, 0, np.newaxis] + xfv[np.newaxis, :, 0])
        y = (indices[:, 1, np.newaxis] + xfv[np.newaxis, :, 1])
        z = (indices[:, 2, np.newaxis] + xfv[np.newaxis, :, 2])
        #
        # Reflect out-of-bounds values back into the image
        #
        x[x < 0] *= -1
        x[x >= ximg.shape[0]] = ximg.shape[0] * 2 - x[x >= ximg.shape[0]] - 1
        y[y < 0] *= -1
        y[y >= ximg.shape[1]] = ximg.shape[1] * 2 - y[y >= ximg.shape[1]] - 1
        z[z < 0] *= -1
        z[z >= ximg.shape[2]] = ximg.shape[2] * 2 - z[z >= ximg.shape[2]] - 1
        sampler[:, offset:end] = ximg[x, y, z]
    return sampler

def extract_eigenfeatures(img, blur_img, components, indices):
    from eigentexture import normalize
    features = extract_features(img, blur_img, indices)
    features = normalize(features)
    efeatures = np.dot(features, components.transpose())
    return efeatures
