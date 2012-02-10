from vigra.learning import RandomForest
from extract_features import extract_features, blur_image
import numpy as np
import sys

clf = RandomForest('../challenge.h5', '/classifier')

import tiffcvt

if len(sys.argv) < 2 or sys.argv[1] == "train":
    predicted = tiffcvt.h5_file.require_dataset("predicted_train_labels",
                                                tiffcvt.train_volume.shape,
                                                np.float32,
                                                chunks=(64,64,1))
    img = tiffcvt.h5_file["ordinal_train_volume"][:,:,:]
else:
    predicted = tiffcvt.h5_file.require_dataset("predicted_test_labels",
                                                tiffcvt.train_volume.shape,
                                                np.float32,
                                                chunks=(64,64,1))
    img = tiffcvt.h5_file["ordinal_test_volume"][:,:,:]
    
bimg = blur_image(img)
for i in range(0, img.shape[0], 64):
    for j in range(0, img.shape[1], 64):
        for k in range(img.shape[2]):
            coords = np.mgrid[i:(i+64), j:(j+64),k:(k+1)].reshape(3, 64*64).transpose()
            features = extract_features(img, bimg, coords)
            score = clf.predictProbabilities(features)[:,1]
            score.shape = (64,64)
            predicted[i:(i+64),j:(j+64),k] = score
            print "Finished block %d, %d, %d" % (i, j, k)
tiffcvt.h5_file.close()
