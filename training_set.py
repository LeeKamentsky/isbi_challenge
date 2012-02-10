# Sample from the training volume to get a training set

from scipy.ndimage import distance_transform_edt
import extract_features
import tiffcvt
import numpy as np
import sys
r = np.random.RandomState()
r.seed(12345)

img = tiffcvt.h5_file["ordinal_train_volume"][:,:,:]
labels = tiffcvt.train_labels[:,:,:]
blur_img = extract_features.blur_image(img)
#
# The idea here is to train all the membrane points because there are few
# of them and to train all points nearby labeled points to get a sharp
# border. After that, we pick randomly from what remains to get some sampling
# of non-membrane, but that is not so crucial.
#
L_MEMBRANE = 0
distance = 3
is_membrane = labels == L_MEMBRANE
coords = [np.argwhere(is_membrane)]
pos = np.sum(is_membrane)
for i in range(labels.shape[2]):
    d = ((distance_transform_edt(~ is_membrane[:,:,i]) <= distance) &  
         ~ is_membrane[:,:,i])
    dc = np.argwhere(d)
    coords.append(np.column_stack([dc.astype(int), np.ones(dc.shape[0], int)]))
coords = np.vstack(coords)
neg = coords.shape[0] - pos
i,j,k = np.mgrid[0:labels.shape[0], 0:labels.shape[1], 0:labels.shape[2]]
i,j,k = i.flatten(), j.flatten(), k.flatten()
background = ~ is_membrane[i,j,k]
i,j,k = i[background], j[background], k[background]
p = r.permutation(len(i))[0:neg]
coords = np.vstack([coords, np.column_stack([i[p], j[p], k[p]])])
npts_sampled = 100000
if len(sys.argv) > 1 and sys.argv[1] == "refine":
    #
    # Add the false positives and false negatives to the training set
    #
    error = []
    prediction = tiffcvt.h5_file["predicted_train_labels"]
    for plane in range(img.shape[2]):
        p = prediction[:,:,plane] > .5
        i,j = np.argwhere(p != (labels[:,:,plane] != 0)).transpose()
        error.append(np.column_stack([i, j, np.ones(len(i), int) * plane]))
    #
    # Train with 3/4 of the sample + 1/4 of the error
    #
    error_count = sum([e.shape[0] for e in error])
    keep_count = max(error_count * 3, npts_sampled - error_count)
    if coords.shape[0] > keep_count:
        coords = coords[r.permutation(coords.shape[0])[:keep_count], :]
    coords = np.vstack([coords] + error)
p = r.permutation(coords.shape[0])[:npts_sampled]
coords = coords[p, :]
coords = coords[np.lexsort(coords.transpose())]

if ("training_features" in tiffcvt.h5_file.keys() and 
    (tiffcvt.h5_file["training_features"].shape[1] != extract_features.n_features or
     tiffcvt.h5_file["training_features"].shape[0] != npts_sampled)):
    del tiffcvt.h5_file["training_features"]
    del tiffcvt.h5_file["training_classification"]
tf = tiffcvt.h5_file.require_dataset("training_features", 
                                     (npts_sampled, extract_features.n_features),
                                     np.float32)
tc = tiffcvt.h5_file.require_dataset("training_classification", 
                                     (npts_sampled, ), np.uint32)
for i in range(0, coords.shape[0], 1024):
    my_slice = slice(i, min(i+1024, coords.shape[0]))
    tf[my_slice,:] = extract_features.extract_features(
        img, blur_img, coords[my_slice,:])
    tc[my_slice] = labels[coords[my_slice,0],
                          coords[my_slice,1],
                          coords[my_slice,2]]
    print "Finished %d of %d" % (i+1024, npts_sampled)
tiffcvt.h5_file.close()
