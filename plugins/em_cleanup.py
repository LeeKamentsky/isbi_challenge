'''<b>EmCleanup</b> Segmentation cleanup for ISBI 2012 challenge
<hr>
This module cleans up the segmentation result for the EM images by looking
at the borders between objects and by applying some heuristics. It will merge
objects if the border between them has little support in the prediction. It
will also remove small objects and objects that are much darker than their
surroundings.
'''
#################################
#
# Imports from useful Python libraries
#
#################################

import numpy as np
from scipy.sparse import coo_matrix

#################################
#
# Imports from CellProfiler
#
# The package aliases are the standard ones we use
# throughout the code.
#
##################################

import cellprofiler.cpimage as cpi
import cellprofiler.cpmodule as cpm
import cellprofiler.objects as cpo
import cellprofiler.settings as cps
import cellprofiler.preferences as cpprefs
import cellprofiler.cpmath.outline
from cellprofiler.cpmath.cpmorphology import all_connected_components
from cellprofiler.cpmath.cpmorphology import fill_labeled_holes


###################################
#
# The module class
#
# Your module should "inherit" from cellprofiler.cpmodule.CPModule.
# This means that your module will use the methods from CPModule unless
# you re-implement them. You can let CPModule do most of the work and
# implement only what you need.
#
###################################

class EMCleanup(cpm.CPModule):
    ###############################################
    #
    # The module starts by declaring the name that's used for display,
    # the category under which it is stored and the variable revision
    # number which can be used to provide backwards compatibility if
    # you add user-interface functionality later.
    #
    ###############################################
    module_name = "EMCleanup"
    category = "Object Processing"
    variable_revision_number = 1
    
    ###############################################
    #
    # create_settings is where you declare the user interface elements
    # (the "settings") which the user will use to customize your module.
    #
    # You can look at other modules and in cellprofiler.settings for
    # settings you can use.
    #
    ################################################
    
    def create_settings(self):
        #
        # The ImageNameSubscriber "subscribes" to all ImageNameProviders in 
        # prior modules. Modules before yours will put images into CellProfiler.
        # The ImageSubscriber gives your user a list of these images
        # which can then be used as inputs in your module.
        #
        self.prediction_image_name = cps.ImageNameSubscriber(
            # The text to the left of the edit box
            "Prediction image:",
            # HTML help that gets displayed when the user presses the
            # help button to the right of the edit box
            doc = """The prediction output from machine learning. Low values
            are predicted to be membrane.
            """)
        self.input_image_name = cps.ImageNameSubscriber(
            "Input image:",
            doc = """The volume EM image""")
        self.input_objects = cps.ObjectNameSubscriber(
            "Input segmentation:",
            doc = """The segmentation that needs to be cleaned up""")
        self.output_objects = cps.ObjectNameProvider(
            "Output segmentation:",
            doc = """The segmentation produced by this module""")
        self.darkness = cps.Float(
            "Dark cutoff:", .2,
            doc = """If the average intensity of an object is in this percentile,
            then we remove the object because it's too dark""")
        self.min_area = cps.Integer(
            "Minimum object area:", 300,
            doc = """If an object has an area lower than this, we merge with
            the largest adjacent touching object""")
        self.min_support = cps.Float(
            "Minimum support:", .3,
            doc = """If the border pixels between two object have an average
            prediction less than this, we merge them""")
        self.min_border = cps.Integer(
            "Minimum border between objects:", 30,
            doc = """Minimum # of border pixels before we consider a merge""")
        self.output_outlines_name = cps.OutlineNameProvider(
            "Outlines name:", "Outlines")
        
    #
    # The "settings" method tells CellProfiler about the settings you
    # have in your module. CellProfiler uses the list for saving
    # and restoring values for your module when it saves or loads a
    # pipeline file.
    #
    def settings(self):
        return [self.prediction_image_name,self.input_image_name, 
                self.input_objects, self.output_objects, self.darkness,
                self.min_area, self.min_support, self.min_border,
                self.output_outlines_name]

    #
    # CellProfiler calls "run" on each image set in your pipeline.
    # This is where you do the real work.
    #
    def run(self, workspace):
        import cellprofiler.modules.identify as I
        #
        # Get the input and output image names. You need to get the .value
        # because otherwise you'll get the setting object instead of
        # the string name.
        #
        input_image_name = self.input_image_name.value
        prediction_image_name = self.prediction_image_name.value
        input_objects_name = self.input_objects.value
        output_objects_name = self.output_objects.value
        #
        # Get the image set. The image set has all of the images in it.
        # The assert statement makes sure that it really is an image set,
        # but, more importantly, it lets my editor do context-sensitive
        # completion for the image set.
        #
        image_set = workspace.image_set
        assert isinstance(image_set, cpi.ImageSet)
        #
        # Get the input image object. We want a grayscale image here.
        # The image set will convert a color image to a grayscale one
        # and warn the user.
        #
        input_image = image_set.get_image(input_image_name,
                                          must_be_grayscale = True).pixel_data
        #
        # I do something a little odd here and elsewhere. I normalize the
        # brightness by ordering the image pixels by brightness. I notice that
        # the samples vary in intensity (why?) and EM is a scanning technology
        # (right?) so there should be uniform illumination across an image.
        #
        r = np.random.RandomState()
        r.seed(np.sum((input_image * 65535).astype(np.uint16)))
        npixels = np.prod(input_image.shape)
        shape = input_image.shape
        order = np.lexsort([r.uniform(size=npixels),
                            input_image.flatten()])
        input_image = np.zeros(npixels)
        input_image[order] = np.arange(npixels).astype(float) / npixels
        input_image.shape = shape
        
        prediction_image = image_set.get_image(prediction_image_name,
                                               must_be_grayscale=True).pixel_data
        object_set = workspace.object_set
        assert isinstance(object_set, cpo.ObjectSet)
        input_objects = object_set.get_objects(input_objects_name)
        assert isinstance(input_objects, cpo.Objects)
        input_labeling = input_objects.segmented
        #
        # Find the border pixels - 4 connected
        #
        # There will be some repeats in here - I'm being lazy and I'm not
        # removing them. The inaccuracies will be random.
        #
        touch = ((input_labeling[1:, :] != input_labeling[:-1, :]) &
                 (input_labeling[1:, :] != 0) &
                 (input_labeling[:-1, :] != 0))
        touchpair = np.argwhere(touch)
        touchpair = np.column_stack([
            # touchpair[:,0:2] are the left coords
            touchpair, 
            # touchpair[:,2:4] are the right coords
            touchpair + np.array([1,0], int)[np.newaxis,:],
            # touchpair[:,4] is the identity of the left object
            input_labeling[touchpair[:,0], touchpair[:, 1]],
            # touchpair[:,5] is the identity of the right object
            input_labeling[touchpair[:,0]+1, touchpair[:, 1]]])
        TP_I0 = 0
        TP_J0 = 1
        TP_I1 = 2
        TP_J1 = 3
        TP_L0 = 4
        TP_L1 = 5
            
        touch = ((input_labeling[:, 1:] != input_labeling[:, :-1]) &
                  (input_labeling[:, 1:] != 0) &
                  (input_labeling[:, :-1] != 0))
        tp2 = np.argwhere(touch)
        
        touchpair = np.vstack([touchpair, np.column_stack([
            tp2, 
            tp2 + np.array([0, 1], int)[np.newaxis,:],
            input_labeling[tp2[:, 0], tp2[:, 1]],
            input_labeling[tp2[:, 0], tp2[:, 1]+1]])])
        #
        # Broadcast the touchpair counts and scores into sparse arrays.
        # The sparse array convention is to sum duplicates
        #
        counts = coo_matrix(
            (np.ones(touchpair.shape[0], int),
             (touchpair[:,TP_L0], touchpair[:,TP_L1]))).toarray()
        scores = coo_matrix(
            (prediction_image[touchpair[:, TP_I0],
                              touchpair[:, TP_J0]] +
             prediction_image[touchpair[:, TP_I1],
                              touchpair[:, TP_J1]],
             (touchpair[:,TP_L0], touchpair[:,TP_L1]))).toarray() / 2.0
        scores = scores / counts
        to_remove = ((counts > self.min_border.value) &
                     (scores > 1 - self.min_support.value))
        #
        # For all_connected_components, do forward and backward links and
        # self-to-self links
        #
        remove_pairs = np.vstack([
            np.argwhere(to_remove), 
            np.argwhere(to_remove.transpose()),
            np.column_stack([np.arange(np.max(input_labeling)+1)] * 2)])
        #
        # Find small objects and dark objects
        #
        areas = np.bincount(input_labeling.flatten())
        brightness = np.bincount(input_labeling.flatten(), input_image.flatten())
        brightness = brightness / areas
        #
        to_remove = ((areas < self.min_area.value) | 
                     (brightness < self.darkness.value))
        to_remove[0] = False
        #
        # Find the biggest neighbor to all. If no neighbors, label = 0
        #
        largest = np.zeros(areas.shape[0], np.uint32)
        largest[:counts.shape[1]] = np.argmax(counts, 0)
        remove_pairs = np.vstack([
            remove_pairs,
            np.column_stack([np.arange(len(to_remove))[to_remove],
                             largest[to_remove]])])
        lnumbers = all_connected_components(remove_pairs[:, 0], 
                                            remove_pairs[:, 1]).astype(np.uint32)
        #
        # Renumber.
        #
        output_labeling = lnumbers[input_labeling]
        #
        # Fill holes.
        #
        output_labeling = fill_labeled_holes(output_labeling)
        #
        # Remove the border pixels. This is for the challenge which requires
        # a mask. 
        #
        can_remove = lnumbers[touchpair[:, TP_L0]] != lnumbers[touchpair[:, TP_L1]]
        output_labeling[touchpair[can_remove, TP_I0], 
                        touchpair[can_remove, TP_J0]] = 0
        output_labeling[touchpair[can_remove, TP_I1], 
                        touchpair[can_remove, TP_J1]] = 0
        output_objects = cpo.Objects()
        output_objects.segmented = output_labeling
        object_set.add_objects(output_objects, output_objects_name)
        nobjects = np.max(output_labeling)
        I.add_object_count_measurements(workspace.measurements,
                                        output_objects_name,
                                        nobjects)
        I.add_object_location_measurements(workspace.measurements,
                                           output_objects_name, 
                                           output_labeling, nobjects)
        # Make an outline image
        outline_image = cellprofiler.cpmath.outline.outline(output_labeling).astype(bool)
        out_img = cpi.Image(outline_image,
                            parent_image = image_set.get_image(input_image_name))
        workspace.image_set.add(self.output_outlines_name.value, out_img)
        
        workspace.display_data.input_pixels = input_image
        workspace.display_data.input_labels = input_labeling
        workspace.display_data.output_labels = output_labeling
        workspace.display_data.outlines = outline_image
                                           
    #
    # is_interactive tells CellProfiler whether "run" uses any interactive
    # GUI elements. If you return False here, CellProfiler will run your
    # module on a separate thread which will make the user interface more
    # responsive.
    #
    def is_interactive(self):
        return False
    #
    # display lets you use matplotlib to display your results. 
    #
    def display(self, workspace):
        #
        # the "figure" is really the frame around the figure. You almost always
        # use figure.subplot or figure.subplot_imshow to get axes to draw on
        # so we pretty much ignore the figure.
        #
        figure = workspace.create_or_find_figure(subplots=(3,1))
        #
        # Show the user the input image
        #
        cimg = (workspace.display_data.input_pixels[:,:,np.newaxis] *
                np.ones(3)[np.newaxis, np.newaxis, :])
        color = cpprefs.get_primary_outline_color()
        cimg[workspace.display_data.outlines, 0] = float(color[0]) / 255
        cimg[workspace.display_data.outlines, 1] = float(color[1]) / 255
        cimg[workspace.display_data.outlines, 2] = float(color[2]) / 255
        figure.subplot_imshow_color(
            0, 0, # show the image in the first row and column
            cimg,
            title = self.input_image_name.value)
        lead_subplot = figure.subplot(0,0)
        figure.subplot_imshow_labels(
            1, 0, # show the image in the first row and second column
            workspace.display_data.input_labels,
            title = self.input_objects.value, 
            sharex = lead_subplot, sharey = lead_subplot)
        figure.subplot_imshow_labels(
            2, 0, # show the image in the first row and last column
            workspace.display_data.output_labels,
            title = self.output_objects.value,
            sharex = lead_subplot, sharey = lead_subplot)
        
    def get_measurement_columns(self, pipeline):
        import cellprofiler.modules.identify as I
        return I.get_object_measurement_columns(self.output_objects.value)
