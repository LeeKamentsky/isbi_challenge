from vigra.learning import RandomForest
import numpy as np
import h5py
import sys
from tiffcvt import h5_file

if __name__=="__main__":
    clf = RandomForest(treeCount=40)
    training_set = h5_file["training_features"][:,:].astype(np.float32)
    training_class = h5_file["training_classification"][:].astype(np.uint32)
    if len(sys.argv) > 1 and sys.argv[1] == "eigentexture":
        from eigentexture import normalize
        training_set = normalize(training_set)
        components = h5_file["components"][:,:].transpose()
        training_set = np.dot(training_set, components).astype(np.float32)
        classifier_name = "etclassifier"
    else:
        classifier_name = "classifier"
    clf.learnRF(training_set, training_class)
    if classifier_name in h5_file.keys():
        del h5_file[classifier_name]
    h5_file.close()
    clf.writeHDF5('../challenge.h5', "/"+classifier_name, True)
else:
    classifier = RandomForest("../challenge.h5", "/classifier")
    et_classifier = RandomForest("../challenge.h5", "/etclassifier")