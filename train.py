from vigra.learning import RandomForest
import numpy as np
import h5py

if __name__=="__main__":
    clf = RandomForest()
    h5_file = h5py.File("../challenge.h5")
    training_set = h5_file["training_features"][:,:].astype(np.float32)
    training_class = h5_file["training_classification"][:].astype(np.uint32)
    clf.learnRF(training_set, training_class)
    if "classifier" in h5_file.keys():
        del h5_file['classifier']
    h5_file.close()
    clf.writeHDF5('../challenge.h5', '/classifier', True)
else:
    classifier = RandomForest("../challenge.h5", "/classifier")