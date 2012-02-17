'''Make a classifier.h5 file with a trained classifier.

Inputs: train-volume.tif, train-labels.tif, test-volume.tif

Outputs: classifier.h5 which has the following pieces
         train_volume - the image stack for the training volume
         train_labels - the image stack for the training labels
         ordinal_train_volume - the train volume stack normalized by 
                                pixel intensity order
         ordinal_test_volume - the test volume in ordinal form
         predicted_train_labels - the training label predictions
         predicted_test_labels - the test label predictions 
         training_features - the feature vectors for the training subset
         training_classification - the classifications of those pixels
         classifier - the Random Forest classifier
         
         train_prediction.tif - TIF 32-bit float file of training predictions
                                by the classifier
         test_prediction.tif - TIF 32-bit float file of test predictions
                                by the classifier
'''

import subprocess
import logging
import logging.config

logging.config.dictConfig({"version":1,
                           "formatters": {
                               "brief": {
                                   "format":"%(asctime)s: %(message)s",
                                   "datefmt":'%Y-%m-%d %H:%M:%S'}},
                           "handlers":
                           { "console":
                             { "class": "logging.StreamHandler",
                               "formatter": "brief",
                               "level": "INFO"}},
                           "loggers":
                           { "root": { "handlers": ["console"] }} })

logger = logging.getLogger("root")
logger.setLevel(logging.INFO)
logger.info("Running make_classifier")

# Put the challenge .tif files into the .hdf file
subprocess.call(["python", "tiffcvt.py"], stdout=subprocess.PIPE)
logger.info("Challenge files created")
# Create the ordinal images
subprocess.call(["python", "ordinalimage.py", "test_volume", 
                 "ordinal_test_volume", "../ordinal_test_volume.tif"])
logger.info("Test ordinal image created")
subprocess.call(["python", "ordinalimage.py", "train_volume", 
                 "ordinal_train_volume", "../ordinal_train_volume.tif"])
logger.info("Train ordinal image created")
#
# Create the first training set
#
subprocess.call(["python", "training_set.py"])
logger.info("Training set created")
#
# Train using the training set
#
subprocess.call(["python", "train.py"])
logger.info("First training complete")
#
# Score the training data
#
subprocess.call(["python", "score.py", "train"])
logger.info("First training scoring complete")
#
# Refine the training set (add false positive and negatives)
#
subprocess.call(["python", "training_set.py", "refine"])
logger.info("Refined training set created")
#
# Retrain
#
subprocess.call(["python", "train.py"])
logger.info("Second training complete")
#
# Rescore the training data
#
subprocess.call(["python", "score.py", "train"])
logger.info("second scoring complete")
#
# Output a TIF of it
#
subprocess.call(["python", "tiffcvt.py", "write"])
logger.info("Wrote predicted training scores")
#
# Score the test data
#
subprocess.call(["python", "score.py", "test"])
logger.info("Scored test data")
#
# Output a TIF of it
#
subprocess.call(["python", "tiffcvt.py", "write", "predicted_test_labels", 
                 "../test_prediction.tif"])
logger.info("Wrote predicted test scores")
