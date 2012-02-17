from vigra.learning import RandomForest
import numpy as np
import sys

if len(sys.argv) < 3 or sys.argv[2] != "eigentexture":
    clf = RandomForest('../challenge.h5', '/classifier')
else:
    clf = RandomForest('../challenge.h5', '/etclassifier')
    
import tiffcvt
from extract_features import extract_features, blur_image, extract_eigenfeatures

if len(sys.argv) < 2 or sys.argv[1] == "train":
    labels_name = "%s_train_labels"
    labels_shape = tiffcvt.train_volume.shape
    img = tiffcvt.h5_file["ordinal_train_volume"][:,:,:]
else:
    labels_name = "%s_test_labels"
    labels_shape = tiffcvt.test_volume.shape
    img = tiffcvt.h5_file["ordinal_test_volume"][:,:,:]

if len(sys.argv) < 3 or sys.argv[2] != "eigentexture":
    extract_fn = extract_features
    labels_name = labels_name % "predicted"
else:
    components = tiffcvt.h5_file["components"][:,:]
    extract_fn = lambda img, bimg, indices:\
       extract_eigenfeatures(img, bimg, components, indices)
    labels_name = labels_name % "eigenpredicted"
    
predicted = tiffcvt.h5_file.require_dataset(labels_name,
                                            labels_shape,
                                            np.float32,
                                            chunks=(64,64,1))
bimg = blur_image(img)
for i in range(0, img.shape[0], 64):
    for j in range(0, img.shape[1], 64):
        for k in range(img.shape[2]):
            coords = np.mgrid[i:(i+64), j:(j+64),k:(k+1)].reshape(3, 64*64).transpose()
            features = extract_fn(img, bimg, coords)
            score = clf.predictProbabilities(features)[:,1]
            score.shape = (64,64)
            predicted[i:(i+64),j:(j+64),k] = score
            print "Finished block %d, %d, %d" % (i, j, k)
tiffcvt.h5_file.close()
