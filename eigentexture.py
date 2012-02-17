import numpy as np
import numpy.linalg
from tiffcvt import h5_file
import pylab

nkernels = 48

if __name__ == "__main__":
    a = h5_file["training_features"][:,:]
    
    means = np.mean(a, 0)
    sds = np.std(a, 0)
    U, S, V = numpy.linalg.svd((a[:,:] - means[np.newaxis, :]) / sds[np.newaxis, :],
                               full_matrices = False)
    components = V.T[:, :nkernels]
    components = components.transpose()
    
    for i in range(nkernels):
        pixels = components[i,:(19*19)].reshape(19,19)
        log = components[i,(19*19):(19*19*2)].reshape(19,19)
        gauss = components[i,(19*19*2):].reshape(9,9)
        pylab.subplot(8, 18, i*3+1).imshow(pixels)
        pylab.subplot(8, 18, i*3+2).imshow(log)
        pylab.subplot(8, 18, i*3+3).imshow(gauss)
    if "components" in h5_file.keys():
        del h5_file["components"]
    if "feature_means" in h5_file.keys():
        del h5_file["feature_means"]
    if "feature_sds" in h5_file.keys():
        del h5_file["feature_sds"]
    h5_file.create_dataset("components", data = components)
    h5_file.create_dataset("feature_means", data = means)
    h5_file.create_dataset("feature_sds", data = sds)
    h5_file.close()
    pylab.savefig("../kernels.pdf")
else:
    means = h5_file["feature_means"][:]
    sds = h5_file["feature_sds"][:]
    
def normalize(features):
    return (features - means[np.newaxis, :]) / sds[np.newaxis, :]


