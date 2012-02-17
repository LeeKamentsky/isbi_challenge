CellProfiler Pipeline: http://www.cellprofiler.org
Version:2
DateRevision:20120216200413

LoadImages:[module_num:1|svn_version:\'Unknown\'|variable_revision_number:11|show_window:False|notes:\x5B\'Load the test prediction generated from the machine learning together with the test image. The test image is only used for visualization.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    File type to be loaded:tif,tiff,flex,zvi movies
    File selection method:Text-Exact match
    Number of images in each group?:3
    Type the text that the excluded images have in common:Do not use
    Analyze all subfolders within the selected folder?:None
    Input image file location:Default Input Folder\x7CNone
    Check image sets for unmatched or duplicate files?:Yes
    Group images by metadata?:No
    Exclude certain files?:No
    Specify metadata fields to group by:
    Select subfolders to analyze:
    Image count:2
    Text that these images have in common (case-sensitive):test_prediction.tif
    Position of this image in each group:1
    Extract metadata from where?:None
    Regular expression that finds metadata in the file name:^(?P<Plate>.*)_(?P<Well>\x5BA-P\x5D\x5B0-9\x5D{2})_s(?P<Site>\x5B0-9\x5D)
    Type the regular expression that finds metadata in the subfolder path:.*\x5B\\\\\\\\/\x5D(?P<Date>.*)\x5B\\\\\\\\/\x5D(?P<Run>.*)$
    Channel count:1
    Group the movie frames?:No
    Grouping method:Interleaved
    Number of channels per group:3
    Load the input as images or objects?:Images
    Name this loaded image:prediction
    Name this loaded object:Nuclei
    Retain outlines of loaded objects?:No
    Name the outline image:LoadedImageOutlines
    Channel number:1
    Rescale intensities?:Yes
    Text that these images have in common (case-sensitive):test_volume
    Position of this image in each group:2
    Extract metadata from where?:None
    Regular expression that finds metadata in the file name:^(?P<Plate>.*)_(?P<Well>\x5BA-P\x5D\x5B0-9\x5D{2})_s(?P<Site>\x5B0-9\x5D)
    Type the regular expression that finds metadata in the subfolder path:.*\x5B\\\\\\\\/\x5D(?P<Date>.*)\x5B\\\\\\\\/\x5D(?P<Run>.*)$
    Channel count:1
    Group the movie frames?:No
    Grouping method:Interleaved
    Number of channels per group:3
    Load the input as images or objects?:Images
    Name this loaded image:image
    Name this loaded object:Nuclei
    Retain outlines of loaded objects?:No
    Name the outline image:LoadedImageOutlines
    Channel number:1
    Rescale intensities?:Yes

ApplyThreshold:[module_num:2|svn_version:\'6746\'|variable_revision_number:6|show_window:False|notes:\x5B\'Threshold the prediction pretty heavily in order to over-segment it. This initial segmentation is used to find many putative centers of tissue surrounded by membrane\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Select the input image:prediction
    Name the output image:BinaryPrediction
    Select the output image type:Binary (black and white)
    Set pixels below or above the threshold to zero?:Below threshold
    Subtract the threshold value from the remaining pixel intensities?:No
    Number of pixels by which to expand the thresholding around those excluded bright pixels:0.0
    Select the thresholding method:Manual
    Manual threshold:0.5
    Lower and upper bounds on threshold:0.000000,1.000000
    Threshold correction factor:1
    Approximate fraction of image covered by objects?:0.01
    Select the input objects:None
    Two-class or three-class thresholding?:Two classes
    Minimize the weighted variance or the entropy?:Weighted variance
    Assign pixels in the middle intensity class to the foreground or the background?:Foreground
    Select the measurement to threshold with:None

Crop:[module_num:3|svn_version:\'Unknown\'|variable_revision_number:2|show_window:False|notes:\x5B\'This cropping step draws a rectangle around the edge of the image and helps force the distance transform off from the edge of the image.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Select the input image:BinaryPrediction
    Name the output image:CroppedBinaryPrediction
    Select the cropping shape:Rectangle
    Select the cropping method:Coordinates
    Apply which cycle\'s cropping pattern?:Every
    Left and right rectangle positions:1,-1
    Top and bottom rectangle positions:1,-1
    Coordinates of ellipse center:500,500
    Ellipse radius, X direction:400
    Ellipse radius, Y direction:200
    Use Plate Fix?:No
    Remove empty rows and columns?:No
    Select the masking image:None
    Select the image with a cropping mask:None
    Select the objects:None

Morph:[module_num:4|svn_version:\'Unknown\'|variable_revision_number:2|show_window:False|notes:\x5B\'Take the distance transform of the binary. The maxima in this are points furthest away from the membrane. Before doing so, erase little blobs in the segmentation. An alternative might be an opening operation...\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Select the input image:CroppedBinaryPrediction
    Name the output image:DistanceTransformPrediction
    Select the operation to perform:open
    Number of times to repeat operation:Once
    Repetition number:200
    Scale:5.0
    Select the operation to perform:close
    Number of times to repeat operation:Once
    Repetition number:2
    Scale:5.0
    Select the operation to perform:fill small holes
    Number of times to repeat operation:Once
    Maximum hole area:200
    Scale:3
    Select the operation to perform:distance
    Number of times to repeat operation:Once
    Repetition number:2
    Scale:3

Smooth:[module_num:5|svn_version:\'Unknown\'|variable_revision_number:1|show_window:False|notes:\x5B\'Smooth the distance transform to help remove double peaks.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Select the input image:DistanceTransformPrediction
    Name the output image:SmoothedDistanceTransform
    Select smoothing method:Gaussian Filter
    Calculate artifact diameter automatically?:No
    Typical artifact diameter, in  pixels:6.0
    Edge intensity difference:0.1

Morph:[module_num:6|svn_version:\'Unknown\'|variable_revision_number:2|show_window:False|notes:\x5B"This is the first step in finding local maxima. Typically, you\'d use IdentifyPrimaryObjects which does this maxima finding step, but I\'ve done it explicitly to have more control and to be able to over-segment. Perform a grayscale dilation. Any point whose value is the same as its grayscale dilation is a maximum."\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Select the input image:SmoothedDistanceTransform
    Name the output image:DilatedPrediction
    Select the operation to perform:dilate
    Number of times to repeat operation:Once
    Repetition number:2
    Scale:8.0

ImageMath:[module_num:7|svn_version:\'Unknown\'|variable_revision_number:3|show_window:False|notes:\x5B\'Subtract the original from the dilated. Any point at zero should be a local maximum. We multiply by -500, so any non-maximal point will be negative\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Operation:Subtract
    Raise the power of the result by:1
    Multiply the result by:-500.0
    Add to result:0
    Set values less than 0 equal to 0?:Yes
    Set values greater than 1 equal to 1?:Yes
    Ignore the image masks?:Yes
    Name the output image:InvLocalPredictionMaxima
    Image or measurement?:Image
    Select the first image:SmoothedDistanceTransform
    Multiply the first image by:1
    Measurement:
    Image or measurement?:Image
    Select the second image:DilatedPrediction
    Multiply the second image by:1
    Measurement:

ImageMath:[module_num:8|svn_version:\'Unknown\'|variable_revision_number:3|show_window:False|notes:\x5B\'Invert the image so that zero becomes 1.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Operation:Invert
    Raise the power of the result by:1
    Multiply the result by:1
    Add to result:0
    Set values less than 0 equal to 0?:Yes
    Set values greater than 1 equal to 1?:Yes
    Ignore the image masks?:No
    Name the output image:LocalPredictionMaxima
    Image or measurement?:Image
    Select the first image:InvLocalPredictionMaxima
    Multiply the first image by:1
    Measurement:
    Image or measurement?:Image
    Select the second image:
    Multiply the second image by:1
    Measurement:

ApplyThreshold:[module_num:9|svn_version:\'6746\'|variable_revision_number:6|show_window:False|notes:\x5B"The distance transform is at a local maximum when it\'s zero for areas larger than the dilation. Don\'t pick up any points where the distance transform is zero (inside the membrane)."\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Select the input image:DistanceTransformPrediction
    Name the output image:NonzeroDistanceTransform
    Select the output image type:Binary (black and white)
    Set pixels below or above the threshold to zero?:Below threshold
    Subtract the threshold value from the remaining pixel intensities?:No
    Number of pixels by which to expand the thresholding around those excluded bright pixels:0.0
    Select the thresholding method:Manual
    Manual threshold:0.00001
    Lower and upper bounds on threshold:0.000000,1.000000
    Threshold correction factor:1
    Approximate fraction of image covered by objects?:0.01
    Select the input objects:None
    Two-class or three-class thresholding?:Two classes
    Minimize the weighted variance or the entropy?:Weighted variance
    Assign pixels in the middle intensity class to the foreground or the background?:Foreground
    Select the measurement to threshold with:None

ImageMath:[module_num:10|svn_version:\'Unknown\'|variable_revision_number:3|show_window:False|notes:\x5B\'Multiplying an image by a binary image produced by ApplyThresholded masks all points below threshold, setting their value to zero.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Operation:Multiply
    Raise the power of the result by:1
    Multiply the result by:1
    Add to result:0
    Set values less than 0 equal to 0?:Yes
    Set values greater than 1 equal to 1?:Yes
    Ignore the image masks?:No
    Name the output image:MaskedLocalMaxima
    Image or measurement?:Image
    Select the first image:LocalPredictionMaxima
    Multiply the first image by:1
    Measurement:
    Image or measurement?:Image
    Select the second image:NonzeroDistanceTransform
    Multiply the second image by:1
    Measurement:

ApplyThreshold:[module_num:11|svn_version:\'6746\'|variable_revision_number:6|show_window:False|notes:\x5B\'Threshold - this is a trivial conversion of a numeric image to a binary one.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Select the input image:MaskedLocalMaxima
    Name the output image:LocalMaximaBinary
    Select the output image type:Binary (black and white)
    Set pixels below or above the threshold to zero?:Below threshold
    Subtract the threshold value from the remaining pixel intensities?:No
    Number of pixels by which to expand the thresholding around those excluded bright pixels:0.0
    Select the thresholding method:Manual
    Manual threshold:0.4999
    Lower and upper bounds on threshold:0.000000,1.000000
    Threshold correction factor:1
    Approximate fraction of image covered by objects?:0.01
    Select the input objects:None
    Two-class or three-class thresholding?:Two classes
    Minimize the weighted variance or the entropy?:Weighted variance
    Assign pixels in the middle intensity class to the foreground or the background?:Foreground
    Select the measurement to threshold with:None

GrayToColor:[module_num:12|svn_version:\'Unknown\'|variable_revision_number:2|show_window:True|notes:\x5B"This is a handy display where you can interactively composite one image against another. It\'s useful to make sure your local maxima are good."\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Select a color scheme:RGB
    Select the input image to be colored red:MaskedLocalMaxima
    Select the input image to be colored green:SmoothedDistanceTransform
    Select the input image to be colored blue:NonzeroDistanceTransform
    Name the output image:ColorImage
    Relative weight for the red image:1
    Relative weight for the green image:1
    Relative weight for the blue image:1
    Select the input image to be colored cyan:LocalMaximaBinary
    Select the input image to be colored magenta:Leave this black
    Select the input image to be colored yellow:Leave this black
    Select the input image that determines brightness:image
    Relative weight for the cyan image:1
    Relative weight for the magenta image:1
    Relative weight for the yellow image:1
    Relative weight for the brightness image:1
    Select the input image to add to the stacked image:None

IdentifyPrimaryObjects:[module_num:13|svn_version:\'Unknown\'|variable_revision_number:9|show_window:False|notes:\x5B\'This just turns the maxima into "objects" which can then be used to seed the watershed in IdentifySecondaryObjects.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Select the input image:LocalMaximaBinary
    Name the primary objects to be identified:LocalMaxima
    Typical diameter of objects, in pixel units (Min,Max):4,10
    Discard objects outside the diameter range?:No
    Try to merge too small objects with nearby larger objects?:No
    Discard objects touching the border of the image?:No
    Select the thresholding method:Binary image
    Threshold correction factor:1
    Lower and upper bounds on threshold:0.000000,1.000000
    Approximate fraction of image covered by objects?:0.01
    Method to distinguish clumped objects:None
    Method to draw dividing lines between clumped objects:Intensity
    Size of smoothing filter:10
    Suppress local maxima that are closer than this minimum allowed distance:7
    Speed up by using lower-resolution image to find local maxima?:Yes
    Name the outline image:PrimaryOutlines
    Fill holes in identified objects?:No
    Automatically calculate size of smoothing filter?:No
    Automatically calculate minimum allowed distance between local maxima?:Yes
    Manual threshold:0.499
    Select binary image:LocalMaximaBinary
    Retain outlines of the identified objects?:No
    Automatically calculate the threshold using the Otsu method?:Yes
    Enter Laplacian of Gaussian threshold:0.5
    Two-class or three-class thresholding?:Two classes
    Minimize the weighted variance or the entropy?:Weighted variance
    Assign pixels in the middle intensity class to the foreground or the background?:Foreground
    Automatically calculate the size of objects for the Laplacian of Gaussian filter?:No
    Enter LoG filter diameter:5
    Handling of objects if excessive number of objects identified:Continue
    Maximum number of objects:500
    Select the measurement to threshold with:None
    Method to calculate adaptive window size:Image size
    Size of adaptive window:10

IdentifySecondaryObjects:[module_num:14|svn_version:\'Unknown\'|variable_revision_number:8|show_window:False|notes:\x5B"Here\'s the big workhorse. IdentifySecondary thresholds the prediction. It then uses the seeds from IdentifyPrimary to perform a seeded watershed. We use the predicted locations of the membrane as saddle points which divide the watershed. The result is over-segmented with shallow saddles improperly breaking tissue not separated by membrane."\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Select the input objects:LocalMaxima
    Name the objects to be identified:Segmentation
    Select the method to identify the secondary objects:Watershed - Image
    Select the input image:prediction
    Select the thresholding method:Manual
    Threshold correction factor:1
    Lower and upper bounds on threshold:0.000000,1.000000
    Approximate fraction of image covered by objects?:0.01
    Number of pixels by which to expand the primary objects:10
    Regularization factor:0.05
    Name the outline image:SecondaryOutlines
    Manual threshold:0.5
    Select binary image:None
    Retain outlines of the identified secondary objects?:Yes
    Two-class or three-class thresholding?:Two classes
    Minimize the weighted variance or the entropy?:Weighted variance
    Assign pixels in the middle intensity class to the foreground or the background?:Foreground
    Discard secondary objects touching the border of the image?:No
    Discard the associated primary objects?:No
    Name the new primary objects:FilteredNuclei
    Retain outlines of the new primary objects?:No
    Name the new primary object outlines:FilteredNucleiOutlines
    Select the measurement to threshold with:None
    Fill holes in identified objects?:Yes
    Method to calculate adaptive window size:Image size
    Size of adaptive window:10

EMCleanup:[module_num:15|svn_version:\'Unknown\'|variable_revision_number:1|show_window:False|notes:\x5B\'This is a custom module I wrote for the challenge. The big thing is to join objects if there is not enough evidence to separate them. There is a description of a similar technique in "Combining intensity, edge and shape information for 2D and 3D segmentation of cell nuclei in tissue sections", Wahlby, Journal of Microscopy Vol 215 Pt 1 July 2004, pp 67-76.\', \'The module also draws single-pixel dividers between touching objects which is needed to conform to the challenge. It removes objects that are uniformly very dark and small objects. These are artifacts which my pixel classifier fails to classify properly.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Prediction image\x3A:prediction
    Input image\x3A:image
    Input segmentation\x3A:Segmentation
    Output segmentation\x3A:CleanedSegmentation
    Dark cutoff\x3A:0.3
    Minimum object area\x3A:30
    Minimum support\x3A:0.375
    Minimum border between objects\x3A:5
    Outlines name\x3A:CleanedOutlines

OverlayOutlines:[module_num:16|svn_version:\'Unknown\'|variable_revision_number:2|show_window:True|notes:\x5B\'Display the image with the original segmentation and the final one after cleanup.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Display outlines on a blank image?:No
    Select image on which to display outlines:image
    Name the output image:ImageOverlay
    Select outline display mode:Color
    Select method to determine brightness of outlines:Max of image
    Width of outlines:1
    Select outlines to display:SecondaryOutlines
    Select outline color:Red
    Select outlines to display:CleanedOutlines
    Select outline color:Green

OverlayOutlines:[module_num:17|svn_version:\'Unknown\'|variable_revision_number:2|show_window:True|notes:\x5B\'Display the prediction and overlays\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Display outlines on a blank image?:No
    Select image on which to display outlines:prediction
    Name the output image:PredictionOverlay
    Select outline display mode:Color
    Select method to determine brightness of outlines:Max of image
    Width of outlines:1
    Select outlines to display:SecondaryOutlines
    Select outline color:Red
    Select outlines to display:CleanedOutlines
    Select outline color:Green

ConvertObjectsToImage:[module_num:18|svn_version:\'Unknown\'|variable_revision_number:1|show_window:False|notes:\x5B\'Convert the segmentation to an image in preparation for saving\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Select the input objects:CleanedSegmentation
    Name the output image:PredictionMask
    Select the color type:Binary (black & white)
    Select the colormap:Default

SaveImages:[module_num:19|svn_version:\'Unknown\'|variable_revision_number:7|show_window:False|notes:\x5B\'Save the prediction.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Select the type of image to save:Image
    Select the image to save:PredictionMask
    Select the objects to save:None
    Select the module display window to save:None
    Select method for constructing file names:Sequential numbers
    Select image name for file prefix:None
    Enter file prefix:TrainPrediction
    Do you want to add a suffix to the image file name?:No
    Text to append to the image name:
    Select file format to use:tif
    Output file location:Default Output Folder\x7CNone
    Image bit depth:8
    Overwrite existing files without warning?:Yes
    Select how often to save:Every cycle
    Rescale the images? :No
    Save as grayscale or color image?:Grayscale
    Select colormap:gray
    Store file and path information to the saved image?:No
    Create subfolders in the output folder?:No

SaveImages:[module_num:20|svn_version:\'Unknown\'|variable_revision_number:7|show_window:False|notes:\x5B\'Save one of the pictures of the segmentation.\'\x5D|batch_state:array(\x5B\x5D, dtype=uint8)]
    Select the type of image to save:Image
    Select the image to save:ImageOverlay
    Select the objects to save:None
    Select the module display window to save:None
    Select method for constructing file names:Sequential numbers
    Select image name for file prefix:None
    Enter file prefix:SegmentationPicture
    Do you want to add a suffix to the image file name?:No
    Text to append to the image name:
    Select file format to use:tif
    Output file location:Default Output Folder\x7CNone
    Image bit depth:8
    Overwrite existing files without warning?:Yes
    Select how often to save:Every cycle
    Rescale the images? :No
    Save as grayscale or color image?:Grayscale
    Select colormap:gray
    Store file and path information to the saved image?:No
    Create subfolders in the output folder?:No
