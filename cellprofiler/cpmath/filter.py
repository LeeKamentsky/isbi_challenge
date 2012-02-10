'''filter.py - functions for applying filters to images

CellProfiler is distributed under the GNU General Public License,
but this file is licensed under the more permissive BSD license.
See the accompanying file LICENSE for details.

Copyright (c) 2003-2009 Massachusetts Institute of Technology
Copyright (c) 2009-2012 Broad Institute
All rights reserved.

Please see the AUTHORS file for credits.

Website: http://www.cellprofiler.org
'''
__version__="$Revision$"

import numpy as np
from scipy.ndimage import gaussian_filter, laplace, convolve, label
from scipy.ndimage import generate_binary_structure, binary_erosion
from scipy.ndimage import map_coordinates

from _filter import paeth_decoder

def smooth_with_function_and_mask(image, function, mask):
    """Smooth an image with a linear function, ignoring the contribution of masked pixels
    
    image - image to smooth
    function - a function that takes an image and returns a smoothed image
    mask  - mask with 1's for significant pixels, 0 for masked pixels
    
    This function calculates the fractional contribution of masked pixels
    by applying the function to the mask (which gets you the fraction of
    the pixel data that's due to significant points). We then mask the image
    and apply the function. The resulting values will be lower by the bleed-over
    fraction, so you can recalibrate by dividing by the function on the mask
    to recover the effect of smoothing from just the significant pixels.
    """
    not_mask               = np.logical_not(mask)
    bleed_over             = function(mask.astype(float))
    masked_image           = np.zeros(image.shape, image.dtype)
    masked_image[mask]     = image[mask]
    smoothed_image         = function(masked_image)
    output_image           = smoothed_image / (bleed_over + np.finfo(float).eps)
    return output_image

def canny(image, mask, sigma, low_threshold, high_threshold, 
          ridge = False, use_image_magnitude = False):
    '''Edge filter an image using the Canny algorithm.
    
    sigma - the standard deviation of the Gaussian used
    low_threshold - threshold for edges that connect to high-threshold
                    edges
    high_threshold - threshold of a high-threshold edge
    
    ridge - detect ridges instead of edges by taking the laplacian of the
            gaussian and use kernels sensitive to the resulting ridges.
            
    use_image_magnitude - if true, use the image's magnitude for thresholding.
            This is appropriate for the ridge detector since you're looking
            to follow the ridge. If this is a number, it's used to smooth
            the image.
    
    Canny, J., A Computational Approach To Edge Detection, IEEE Trans. 
    Pattern Analysis and Machine Intelligence, 8:679-714, 1986
    
    William Green's Canny tutorial
    http://www.pages.drexel.edu/~weg22/can_tut.html
    '''
    #
    # The steps involved:
    #
    # * Smooth using the Gaussian with sigma above.
    #
    # * Apply the horizontal and vertical Sobel operators to get the gradients
    #   within the image. The edge strength is the sum of the magnitudes
    #   of the gradients in each direction.
    #
    # * Find the normal to the edge at each point using the arctangent of the
    #   ratio of the Y sobel over the X sobel - pragmatically, we can
    #   look at the signs of X and Y and the relative magnitude of X vs Y
    #   to sort the points into 4 categories: horizontal, vertical,
    #   diagonal and antidiagonal.
    #
    # * Look in the normal and reverse directions to see if the values
    #   in either of those directions are greater than the point in question.
    #   Use interpolation to get a mix of points instead of picking the one
    #   that's the closest to the normal.
    #
    # * Label all points above the high threshold as edges.
    # * Recursively label any point above the low threshold that is 8-connected
    #   to a labeled point as an edge.
    #
    # Regarding masks, any point touching a masked point will have a gradient
    # that is "infected" by the masked point, so it's enough to erode the
    # mask by one and then mask the output. We also mask out the border points
    # because who knows what lies beyond the edge of the image?
    #
    if ridge:
        smoothed = laplace(gaussian_filter(image, sigma))
        jsobel_kernel = [[-1, 2, -1], [-2, 4, -2], [-1, 2, -1]]
        isobel_kernel = [[-1, -2, -1], [2, 4, 2], [-1, -2, -1]]
    else:
        fsmooth = lambda x: gaussian_filter(x, sigma, mode='constant')
        jsobel_kernel = [[-1,0,1],[-2,0,2],[-1,0,1]]
        isobel_kernel = [[-1,-2,-1],[0,0,0],[1,2,1]]
        smoothed = smooth_with_function_and_mask(image, fsmooth, mask)
    jsobel = convolve(smoothed, jsobel_kernel)
    isobel = convolve(smoothed, isobel_kernel)
    abs_isobel = np.abs(isobel)
    abs_jsobel = np.abs(jsobel)
    if ridge:
        if use_image_magnitude:
            if not isinstance(use_image_magnitude, bool):
                fsmooth = lambda x: \
                    gaussian_filter(x, use_image_magnitude, mode='constant')
                magnitude = smooth_with_function_and_mask(image, fsmooth, mask)
            else:
                magnitude = image
        else:
            magnitude = smoothed
    else:
        magnitude = np.sqrt(isobel*isobel + jsobel*jsobel)
    #
    # Make the eroded mask. Setting the border value to zero will wipe
    # out the image edges for us.
    #
    s = generate_binary_structure(2,2)
    emask = binary_erosion(mask, s, border_value = 0)
    emask = emask & (magnitude > 0)
    #
    #--------- Find local maxima --------------
    #
    # Assign each point to have a normal of 0-45 degrees, 45-90 degrees,
    # 90-135 degrees and 135-180 degrees.
    #
    local_maxima = np.zeros(image.shape,bool)
    #----- 0 to 45 degrees ------
    pts_plus = (isobel >= 0) & (jsobel >= 0) & (abs_isobel >= abs_jsobel)
    pts_minus = (isobel <= 0) & (jsobel <= 0) & (abs_isobel >= abs_jsobel)
    pts = (pts_plus | pts_minus) & emask
    # Get the magnitudes shifted left to make a matrix of the points to the
    # right of pts. Similarly, shift left and down to get the points to the
    # top right of pts.
    c1 = magnitude[1:,:][pts[:-1,:]]
    c2 = magnitude[1:,1:][pts[:-1,:-1]]
    m  = magnitude[pts]
    w  = abs_jsobel[pts] / abs_isobel[pts]
    c_plus  = c2 * w + c1 * (1-w) <= m
    c1 = magnitude[:-1,:][pts[1:,:]]
    c2 = magnitude[:-1,:-1][pts[1:,1:]]
    c_minus =  c2 * w + c1 * (1-w) <= m
    local_maxima[pts] = c_plus & c_minus
    #----- 45 to 90 degrees ------
    # Mix diagonal and vertical
    #
    pts_plus = np.logical_and(isobel >= 0, 
                              np.logical_and(jsobel >= 0, 
                                             abs_isobel <= abs_jsobel))
    pts_minus = np.logical_and(isobel <= 0,
                               np.logical_and(jsobel <= 0, 
                                              abs_isobel <= abs_jsobel))
    pts = np.logical_or(pts_plus, pts_minus)
    pts = np.logical_and(emask, pts)
    c1 = magnitude[:,1:][pts[:,:-1]]
    c2 = magnitude[1:,1:][pts[:-1,:-1]]
    m  = magnitude[pts]
    w  = abs_isobel[pts] / abs_jsobel[pts]
    c_plus  = c2 * w + c1 * (1-w) <= m
    c1 = magnitude[:,:-1][pts[:,1:]]
    c2 = magnitude[:-1,:-1][pts[1:,1:]]
    c_minus =  c2 * w + c1 * (1-w) <= m
    local_maxima[pts] = np.logical_and(c_plus, c_minus)
    #----- 90 to 135 degrees ------
    # Mix anti-diagonal and vertical
    #
    pts_plus = np.logical_and(isobel <= 0, 
                              np.logical_and(jsobel >= 0, 
                                             abs_isobel <= abs_jsobel))
    pts_minus = np.logical_and(isobel >= 0,
                               np.logical_and(jsobel <= 0, 
                                              abs_isobel <= abs_jsobel))
    pts = np.logical_or(pts_plus, pts_minus)
    pts = np.logical_and(emask, pts)
    c1a = magnitude[:,1:][pts[:,:-1]]
    c2a = magnitude[:-1,1:][pts[1:,:-1]]
    m  = magnitude[pts]
    w  = abs_isobel[pts] / abs_jsobel[pts]
    c_plus  = c2a * w + c1a * (1.0-w) <= m
    c1 = magnitude[:,:-1][pts[:,1:]]
    c2 = magnitude[1:,:-1][pts[:-1,1:]]
    c_minus =  c2 * w + c1 * (1.0-w) <= m
    cc = np.logical_and(c_plus,c_minus)
    local_maxima[pts] = np.logical_and(c_plus, c_minus)
    #----- 135 to 180 degrees ------
    # Mix anti-diagonal and anti-horizontal
    #
    pts_plus = np.logical_and(isobel <= 0, 
                              np.logical_and(jsobel >= 0, 
                                             abs_isobel >= abs_jsobel))
    pts_minus = np.logical_and(isobel >= 0,
                               np.logical_and(jsobel <= 0, 
                                              abs_isobel >= abs_jsobel))
    pts = np.logical_or(pts_plus, pts_minus)
    pts = np.logical_and(emask, pts)
    c1 = magnitude[:-1,:][pts[1:,:]]
    c2 = magnitude[:-1,1:][pts[1:,:-1]]
    m  = magnitude[pts]
    w  = abs_jsobel[pts] / abs_isobel[pts]
    c_plus  = c2 * w + c1 * (1-w) <= m
    c1 = magnitude[1:,:][pts[:-1,:]]
    c2 = magnitude[1:,:-1][pts[:-1,1:]]
    c_minus =  c2 * w + c1 * (1-w) <= m
    local_maxima[pts] = np.logical_and(c_plus, c_minus)
    #
    #---- Create two masks at the two thresholds.
    #
    high_mask = np.logical_and(local_maxima, magnitude >= high_threshold)
    low_mask  = np.logical_and(local_maxima, magnitude >= low_threshold)
    #
    # Segment the low-mask, then only keep low-segments that have
    # some high_mask component in them 
    #
    labels,count = label(low_mask, np.ndarray((3,3),bool))
    if count == 0:
        return low_mask
    
    sums = np.bincount(labels.flatten(), high_mask.flatten())
    sums[0] = 0
    good_label = np.zeros((count+1,),bool)
    good_label[:len(sums)] = sums > 0
    output_mask = good_label[labels]
    return output_mask  

def bilateral_filter(image, mask, sigma_spatial, sigma_range,
                     sampling_spatial = None, sampling_range = None):
    """Bilateral filter of an image
    
    image - image to be bilaterally filtered
    mask  - mask of significant points in image
    sigma_spatial - standard deviation of the spatial Gaussian
    sigma_range   - standard deviation of the range Gaussian
    sampling_spatial - amt to reduce image array extents when sampling
                       default is 1/2 sigma_spatial
    sampling_range - amt to reduce the range of values when sampling
                     default is 1/2 sigma_range
    
    The bilateral filter is described by the following equation:
    
    sum(Fs(||p - q||)Fr(|Ip - Iq|)Iq) / sum(Fs(||p-q||)Fr(|Ip - Iq))
    where the sum is over all points in the kernel
    p is all coordinates in the image
    q is the coordinates as perturbed by the mask
    Ip is the intensity at p
    Iq is the intensity at q
    Fs is the spatial convolution function, for us a Gaussian that
    falls off as the distance between falls off
    Fr is the "range" distance which falls off as the difference
    in intensity increases.
    
    1 / sum(Fs(||p-q||)Fr(|Ip - Iq)) is the weighting for point p
    
    """
    # The algorithm is taken largely from code by Jiawen Chen which miraculously
    # extends to the masked case:
    # http://groups.csail.mit.edu/graphics/bilagrid/bilagrid_web.pdf
    #
    # Form a 3-d array whose extent is reduced in the i,j directions
    # by the spatial sampling parameter and whose extent is reduced in the
    # z (image intensity) direction by the range sampling parameter.
    
    # Scatter each significant pixel in the image into the nearest downsampled
    # array address where the pixel's i,j coordinate gives the corresponding
    # i and j in the matrix and the intensity value gives the corresponding z
    # in the array.
    
    # Count the # of values entered into each 3-d array element to form a
    # weight.
    
    # Similarly convolve the downsampled value and weight arrays with a 3-d
    # Gaussian kernel whose i and j Gaussian is the sigma_spatial and whose
    # z is the sigma_range.
    #
    # Divide the value by the weight to scale each z value appropriately
    #
    # Linearly interpolate using an i x j x 3 array where [:,:,0] is the
    # i coordinate in the downsampled array, [:,:,1] is the j coordinate
    # and [:,:,2] is the unrounded index of the z-slot 
    #
    # One difference is that I don't pad the intermediate arrays. The
    # weights bleed off the edges of the intermediate arrays and this
    # accounts for the ring of zero values used at the border bleeding
    # back into the intermediate arrays during convolution
    #
     
    if sampling_spatial is None:
        sampling_spatial = sigma_spatial / 2.0
    if sampling_range is None:
        sampling_range = sigma_range / 2.0
    
    if np.all(np.logical_not(mask)):
        return image
    masked_image = image[mask]
    image_min = np.min(masked_image)
    image_max = np.max(masked_image)
    image_delta = image_max - image_min
    if image_delta == 0:
        return image
    
    #
    # ds = downsampled. Calculate the ds array sizes and sigmas.
    #
    ds_sigma_spatial = sigma_spatial / sampling_spatial
    ds_sigma_range   = sigma_range / sampling_range
    ds_i_limit       = int(image.shape[0] / sampling_spatial) + 2
    ds_j_limit       = int(image.shape[1] / sampling_spatial) + 2
    ds_z_limit       = int(image_delta / sampling_range) + 2
    
    grid_data    = np.zeros((ds_i_limit, ds_j_limit, ds_z_limit))
    grid_weights = np.zeros((ds_i_limit, ds_j_limit, ds_z_limit))
    #
    # Compute the downsampled i, j and z coordinates at each point
    #
    di,dj = np.mgrid[0:image.shape[0],
                     0:image.shape[1]].astype(float) / sampling_spatial
    dz = (masked_image - image_min) / sampling_range
    #
    # Treat this as a list of 3-d coordinates from now on
    #
    di = di[mask]
    dj = dj[mask]
    #
    # scatter the unmasked image points into the data array and
    # scatter a value of 1 per point into the weights
    #
    grid_data[(di + .5).astype(int), 
              (dj + .5).astype(int),
              (dz + .5).astype(int)] += masked_image
    grid_weights[(di + .5).astype(int), 
                 (dj + .5).astype(int),
                 (dz + .5).astype(int)] += 1
    #
    # Make a Gaussian kernel
    #
    kernel_spatial_limit = int(2 * ds_sigma_spatial) + 1
    kernel_range_limit   = int(2 * ds_sigma_range) + 1
    ki,kj,kz = np.mgrid[-kernel_spatial_limit : kernel_spatial_limit+1,
                        -kernel_spatial_limit : kernel_spatial_limit+1,
                        -kernel_range_limit : kernel_range_limit+1]
    kernel = np.exp(-.5 * ((ki**2 + kj**2) / ds_sigma_spatial ** 2 +
                           kz**2 / ds_sigma_range ** 2))
     
    blurred_grid_data = convolve(grid_data, kernel, mode='constant')
    blurred_weights = convolve(grid_weights, kernel, mode='constant')
    weight_mask = blurred_weights > 0
    normalized_blurred_grid = np.zeros(grid_data.shape)
    normalized_blurred_grid[weight_mask] = ( blurred_grid_data[weight_mask] /
                                             blurred_weights[weight_mask])
    #
    # Now use di, dj and dz to find the coordinate of the point within
    # the blurred grid to use. We actually interpolate between points
    # here (both in the i,j direction to get intermediate z values and in
    # the z direction to get the slot, roughly where we put our original value)
    #
    dijz = np.vstack((di, dj, dz))
    image_copy = image.copy()
    image_copy[mask] = map_coordinates(normalized_blurred_grid, dijz,
                                       order = 1)
    return image_copy

