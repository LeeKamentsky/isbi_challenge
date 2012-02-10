import numpy as np
import numpy.linalg
from tiffcvt import h5_file
from extract_features import fv
import pylab

nkernels = 30

a = h5_file["training_features"][::64,:]

means = np.mean(a, 0)
sds = np.std(a, 0)
U, S, V = numpy.linalg.svd((a[:,:] - means[np.newaxis, :]) / sds[np.newaxis, :],
                           full_matrices = False)
components = V.T[:, :nkernels]
components = components.transpose()
pictures = components.reshape((nkernels, 2, 19, 19))

for i in range(nkernels):
    pylab.subplot(5, 12, i*2+1).imshow(pictures[i,0,:,:])
    pylab.subplot(5, 12, i*2+2).imshow(pictures[i,1,:,:])
if "components" in h5_file.keys():
    del h5_file["components"]
h5_file.create_dataset("components", data = components)
pylab.savefig("../kernels.pdf")

