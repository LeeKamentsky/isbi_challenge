"""omexml.py read and write OME xml

"""
# CellProfiler is distributed under the GNU General Public License.
# See the accompanying file LICENSE for details.
# 
# Developed by the Broad Institute
# Copyright 2003-2011
# 
# Please see the AUTHORS file for credits.
# 
# Website: http://www.cellprofiler.org
#
import xml.dom
from xml.dom.minidom import parseString
import datetime
import logging
logger = logging.getLogger(__file__)
import re
import uuid

def xsd_now():
    '''Return the current time in xsd:dateTime format'''
    return datetime.datetime.now().isoformat()

DEFAULT_NOW = xsd_now()
#
# The namespaces
#
NS_OME = "http://www.openmicroscopy.org/Schemas/OME/2011-06"
NS_BINARY_FILE = "http://www.openmicroscopy.org/Schemas/BinaryFile/2011-06"
NS_SA = "http://www.openmicroscopy.org/Schemas/SA/2011-06"
NS_ORIGINAL_METADATA = "openmicroscopy.org/OriginalMetadata"
NS_SPW = "http://www.openmicroscopy.org/Schemas/SPW/2011-06"

default_xml = """<?xml version="1.0" encoding="UTF-8"?>
<OME xmlns="%(NS_OME)s" 
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
     xsi:schemaLocation="http://www.openmicroscopy.org/Schemas/OME/2011-06 http://www.openmicroscopy.org/Schemas/OME/2011-06/ome.xsd">
  <Image ID="Image:0" Name="default.png">
    <AcquiredDate>%(DEFAULT_NOW)s</AcquiredDate>
    <Pixels DimensionOrder="XYCTZ" 
            ID="Pixels:0" 
            SizeC="1" 
            SizeT="1" 
            SizeX="512" 
            SizeY="512"
            SizeZ="1"
            Type="uint8">
<Channel ID="Channel:0:0" SamplesPerPixel="1">
        <LightPath/>
      </Channel>
      <BinData xmlns="%(NS_BINARY_FILE)s" 
       BigEndian="false" Length="0"/>
    </Pixels>
  </Image>
  <StructuredAnnotations xmlns="%(NS_SA)s"/>
</OME>
""" % globals()
#
# These are the OME-XML pixel types - not all supported by subimager
#
PT_INT8 = "int8"
PT_INT16 = "int16"
PT_INT32 = "int32"
PT_UINT8 = "uint8"
PT_UINT16 = "uint16"
PT_UINT32 = "uint32"
PT_FLOAT = "float"
PT_BIT = "bit"
PT_DOUBLE = "double"
PT_COMPLEX = "complex"
PT_DOUBLECOMPLEX = "double-complex"
#
# The allowed dimension types
#
DO_XYZCT = "XYZCT"
DO_XYZTC = "XYZTC"
DO_XYCTZ = "XYCTZ"
DO_XYCZT = "XYCZT"
DO_XYTCZ = "XYTCZ"
DO_XYTZC = "XYTZC"
#
# Original metadata corresponding to TIFF tags
# The text for these can be found in 
# loci.formats.in.BaseTiffReader.initStandardMetadata
#
'''IFD # 254'''
OM_NEW_SUBFILE_TYPE = "NewSubfileType"
'''IFD # 256'''
OM_IMAGE_WIDTH = "ImageWidth"
'''IFD # 257'''
OM_IMAGE_LENGTH = "ImageLength"
'''IFD # 258'''
OM_BITS_PER_SAMPLE = "BitsPerSample"

'''IFD # 262'''
OM_PHOTOMETRIC_INTERPRETATION = "PhotometricInterpretation"
PI_WHITE_IS_ZERO = "WhiteIsZero"
PI_BLACK_IS_ZERO = "BlackIsZero"
PI_RGB = "RGB"
PI_RGB_PALETTE = "Palette"
PI_TRANSPARENCY_MASK = "Transparency Mask"
PI_CMYK = "CMYK"
PI_Y_CB_CR = "YCbCr"
PI_CIE_LAB = "CIELAB"
PI_CFA_ARRAY = "Color Filter Array"

'''BioFormats infers the image type from the photometric interpretation'''
OM_METADATA_PHOTOMETRIC_INTERPRETATION = "MetaDataPhotometricInterpretation"
MPI_RGB = "RGB"
MPI_MONOCHROME = "Monochrome"
MPI_CMYK = "CMYK"

'''IFD # 263'''
OM_THRESHHOLDING = "Threshholding" # (sic)
'''IFD # 264 (but can be 265 if the orientation = 8)'''
OM_CELL_WIDTH = "CellWidth"
'''IFD # 265'''
OM_CELL_LENGTH = "CellLength"
'''IFD # 266'''
OM_FILL_ORDER = "FillOrder"
'''IFD # 279'''
OM_DOCUMENT_NAME = "Document Name"
'''IFD # 271'''
OM_MAKE = "Make"
'''IFD # 272'''
OM_MODEL = "Model"
'''IFD # 274'''
OM_ORIENTATION = "Orientation"
'''IFD # 277'''
OM_SAMPLES_PER_PIXEL = "SamplesPerPixel"
'''IFD # 280'''
OM_MIN_SAMPLE_VALUE = "MinSampleValue"
'''IFD # 281'''
OM_MAX_SAMPLE_VALUE = "MaxSampleValue"
'''IFD # 282'''
OM_X_RESOLUTION = "XResolution"
'''IFD # 283'''
OM_Y_RESOLUTION = "YResolution"
'''IFD # 284'''
OM_PLANAR_CONFIGURATION = "PlanarConfiguration"
PC_CHUNKY = "Chunky"
PC_PLANAR = "Planar"

'''IFD # 286'''
OM_X_POSITION = "XPosition"
'''IFD # 287'''
OM_Y_POSITION = "YPosition"
'''IFD # 288'''
OM_FREE_OFFSETS = "FreeOffsets"
'''IFD # 289'''
OM_FREE_BYTECOUNTS = "FreeByteCounts"
'''IFD # 290'''
OM_GRAY_RESPONSE_UNIT = "GrayResponseUnit"
'''IFD # 291'''
OM_GRAY_RESPONSE_CURVE = "GrayResponseCurve"
'''IFD # 292'''
OM_T4_OPTIONS = "T4Options"
'''IFD # 293'''
OM_T6_OPTIONS = "T6Options"
'''IFD # 296'''
OM_RESOLUTION_UNIT = "ResolutionUnit"
'''IFD # 297'''
OM_PAGE_NUMBER = "PageNumber"
'''IFD # 301'''
OM_TRANSFER_FUNCTION = "TransferFunction"

'''IFD # 305'''
OM_SOFTWARE = "Software"
'''IFD # 306'''
OM_DATE_TIME = "DateTime"
'''IFD # 315'''
OM_ARTIST = "Artist"
'''IFD # 316'''
OM_HOST_COMPUTER = "HostComputer"
'''IFD # 317'''
OM_PREDICTOR = "Predictor"
'''IFD # 318'''
OM_WHITE_POINT = "WhitePoint"
'''IFD # 322'''
OM_TILE_WIDTH = "TileWidth"
'''IFD # 323'''
OM_TILE_LENGTH = "TileLength"
'''IFD # 324'''
OM_TILE_OFFSETS = "TileOffsets"
'''IFD # 325'''
OM_TILE_BYTE_COUNT = "TileByteCount"
'''IFD # 332'''
OM_INK_SET = "InkSet"
'''IFD # 33432'''
OM_COPYRIGHT = "Copyright"
#
# Well row/column naming conventions
#
NC_LETTER = "letter"
NC_NUMBER = "number"

def page_name_original_metadata(index):
    '''Get the key name for the page name metadata data for the indexed tiff page
    
    These are TIFF IFD #'s 285+
    
    index - zero-based index of the page
    '''
    return "PageName #%d" % index

def get_text(node):
    '''Get the contents of text nodes in a parent node'''
    node.normalize()
    for child in iter_children(node, xml.dom.Node.TEXT_NODE):
        return child.data
    return None

def set_text(node, text):
    '''Set the text of a parent'''
    node.normalize()
    child = node.firstChild
    for child in iter_children(node, xml.dom.Node.TEXT_NODE):
        child.data = text
        return
    dom = get_dom(node)
    node.appendChild(dom.createTextNode(text))
    
def make_text_node(parent, namespace, tag_name, text):
    '''Either make a new node and add the given text or replace the text
    
    parent - the parent node to the node to be created or found
    namespace - the namespace of the node's qualified name
    tag_name - the tag name of  the node's qualified name
    text - the text to be inserted
    '''
    nodes = parent.getElementsByTagNameNS(namespace, tag_name)
    if len(nodes) == 0:
        node = get_dom(parent).createElementNS(namespace, tag_name)
        parent.appendChild(node)
    else:
        node = nodes[0]
    set_text(node, text)

def get_dom(node):
    '''Get the document node given a rooted node'''
    while node.nodeType != xml.dom.Node.DOCUMENT_NODE:
        node = node.parentNode
    return node

def insert_after(prior, subsequent):
    '''Insert an unrooted node after a prior, rooted node'''
    if prior.nextSibling is None:
        prior.parentNode.appendChild(subsequent)
    else:
        prior.parentNode.insertBefore(subsequent, prior.nextSibling)

def iter_children(parent, node_type = None):
    '''Iterate among the children of a node

    parent - parent node
    node_type - if present, only return children of that type.
    '''
    child = parent.firstChild
    while child is not None:
        if (node_type is None) or (child.nodeType == node_type):
            yield child
        child = child.nextSibling
    return

class OMEXML(object):
    '''The OMEXML class reads and writes OME-XML with methods to get and set it
    
    The OMEXML class has four main purposes - to parse OME-XML, to output
    OME-XML, to provide a structured mechanism for inspecting OME-XML and to
    let the caller create and modify OME-XML.
    
    There are two ways to invoke the constructor. If you supply XML as a string
    or unicode string, the constructor will parse it and will use it as the
    base for any inspection and modification. If you don't supply XML, you'll
    get a bland OME-XML object which has a one-channel image. You can modify
    it programatically and get the modified OME-XML back out by calling to_xml.
    
    There are two ways to get at the XML. The arduous way is to get the
    root_node of the DOM and explore it yourself using the DOM API
    (http://docs.python.org/library/xml.dom.html#module-xml.dom). The easy way,
    where it's supported is to use properties on OMEXML and on some of its
    derived objects. For instance:
    
    o = OMEXML()
    print o.image().AcquiredDate
    
    will get you the date that image # 0 was acquired.
    
    o = OMEXML()
    
    o.image().Name = "MyImage"
    
    will set the image name to "MyImage"
    
    You can add and remove objects using the "count" properties. Each of these
    handles hooking up and removing orphaned elements for you and should be
    less error prone than creating orphaned elements and attaching them. For
    instance, to create a three-color image:
    
    o = OMEXML()
    
    o.image().Pixels.channel_count = 3
    
    o.image().Pixels.Channel(0).Name = "Red"
    
    o.image().Pixels.Channel(1).Name = "Green"
    
    o.image().Pixels.Channel(2).Name = "Blue"
    
    You can view the OME-XML schema documentation online at:
    http://git.openmicroscopy.org/src/develop/components/specification/Documentation/Generated/OME-2011-06/ome.html
    '''
    def __init__(self, xml=default_xml):
        self.dom = parseString(xml)
        
    def __str__(self):
        return self.dom.toprettyxml(encoding="utf-8")
    
    def to_xml(self, indent="\t", newline="\n", encoding = "utf-8"):
        return self.dom.toprettyxml(indent = indent,
                                    newl = newline,
                                    encoding = encoding)

    @property
    def root_node(self):
        return self.dom.getElementsByTagName("OME")[0]
    
    def get_image_count(self):
        '''The number of images (= series) specified by the XML'''
        return len(self.root_node.getElementsByTagName("Image"))
    
    def set_image_count(self, value):
        '''Add or remove image nodes as needed'''
        assert value > 0
        root = self.root_node
        while(self.image_count > value):
            last = self.root_node.getElementsByTagNameNS(NS_OME, "Image")[-1]
            root.removeChild(last)
            last.unlink()
        while(self.image_count < value):
            last_image = self.root_node.getElementsByTagNameNS(NS_OME,"Image")[-1]
            new_image = self.Image(self.dom.createElementNS(NS_OME, "Image"))
            insert_after(last_image, new_image.node)
            new_image.ID = str(uuid.uuid4())
            new_image.Name = "default.png"
            new_image.AcquiredDate = xsd_now()
            new_pixels = self.Pixels(self.dom.createElementNS(NS_OME, "Pixels"))
            new_image.node.appendChild(new_pixels.node)
            new_pixels.ID = str(uuid.uuid4())
            new_pixels.DimensionOrder = DO_XYCTZ
            new_pixels.PixelType = PT_UINT8
            new_pixels.SizeC = 1
            new_pixels.SizeT = 1
            new_pixels.SizeX = 512
            new_pixels.SizeY = 512
            new_pixels.SizeZ = 1
            new_channel = self.Channel(self.dom.createElementNS(NS_OME, "Channel"))
            new_pixels.node.appendChild(new_channel.node)
            new_channel.ID = "Channel%d:0" % self.image_count
            new_channel.Name = new_channel.ID
            new_channel.SamplesPerPixel = 1
            
    image_count = property(get_image_count, set_image_count)
    
    @property
    def plates(self):
        return self.PlatesDucktype(self.root_node)
    
    @property
    def structured_annotations(self):
        '''Return the structured annotations container
        
        returns a wrapping of OME/StructuredAnnotations. It creates
        the element if it doesn't exist.
        '''
        nodes = self.root_node.getElementsByTagNameNS(
            NS_SA, "StructuredAnnotations")
        if len(nodes) == 0:
            node = self.dom.createElementNS(NS_SA, "StructuredAnnotations")
            self.root_node.addChild(node)
        else:
            node = nodes[0]
        return self.StructuredAnnotations(node)
    
    class Image(object):
        '''Representation of the OME/Image element'''
        def __init__(self, node):
            '''Initialize with the DOM Image node'''
            self.node = node
            
        def get_ID(self):
            return self.node.getAttribute("ID")
        def set_ID(self, value):
            self.node.setAttribute("ID", value)
        ID = property(get_ID, set_ID)

        def get_Name(self):
            return self.node.getAttribute("Name")
        def set_Name(self, value):
            self.node.setAttribute("Name", value)
        Name = property(get_Name, set_Name)
        
        def get_AcquiredDate(self):
            '''The date in ISO-8601 format'''
            acquired_dates = self.node.getElementsByTagNameNS(NS_OME, "AcquiredDate")
            if len(acquired_dates) == 0:
                return None
            return get_text(acquired_dates[0])
        
        def set_AcquiredDate(self, date):
            acquired_dates = self.node.getElementsByTagNameNS(NS_OME, "AcquiredDate")
            if len(acquired_dates) == 0:
                dom = get_dom(self.node)
                acquired_date = dom.createElementNS(NS_OME, "AcquiredDate")
                self.node.appendChild(acquired_date)
            else:
                acquired_date = acquired_dates[0]
            set_text(acquired_date, date)
        AcquiredDate = property(get_AcquiredDate, set_AcquiredDate)
            
        @property
        def Pixels(self):
            '''The OME/Image/Pixels element'''
            return OMEXML.Pixels(self.node.getElementsByTagNameNS(NS_OME, "Pixels")[0])
        
    def image(self, index=0):
        '''Return an image node by index'''
        return self.Image(self.root_node.getElementsByTagNameNS(NS_OME, "Image")[index])
    
    class Channel(object):
        '''The OME/Image/Pixels/Channel element'''
        def __init__(self, node):
            self.node = node
            
        def get_ID(self):
            return self.node.getAttribute("ID")
        def set_ID(self, value):
            self.node.setAttribute("ID", value)
        ID = property(get_ID, set_ID)
        
        def get_Name(self):
            return self.node.getAttribute("Name")
        def set_Name(self, value):
            self.node.setAttribute("Name", value)
        Name = property(get_Name, set_Name)
        
        def get_SamplesPerPixel(self):
            return int(self.node.getAttribute("SamplesPerPixel"))
        def set_SamplesPerPixel(self, value):
            self.node.setAttribute("SamplesPerPixel", str(value))
        SamplesPerPixel = property(get_SamplesPerPixel, set_SamplesPerPixel)

    class Plane(object):
        '''The OME/Image/Pixels/Plane element
        
        The Plane element represents one 2-dimensional image plane. It
        has the Z, C and T indices of the plane and optionally has the
        X, Y, Z, exposure time and a relative time delta.
        '''
        def __init__(self, node):
            self.node = node
            
        def get_TheZ(self):
            '''The Z index of the plane'''
            if self.node.hasAttribute("TheZ"):
                return int(self.node.getAttribute("TheZ"))
            return None
        
        def set_TheZ(self, value):
            self.node.setAttribute("TheZ", str(value))
            
        TheZ = property(get_TheZ, set_TheZ)
        
        def get_TheC(self):
            '''The channel index of the plane'''
            if self.node.hasAttribute("TheC"):
                return int(self.node.getAttribute("TheC"))
            return None
        
        def set_TheC(self, value):
            self.node.setAttribute("TheC", str(value))
            
        TheC = property(get_TheC, set_TheC)
        
        def get_TheT(self):
            '''The T index of the plane'''
            if self.node.hasAttribute("TheT"):
                return int(self.node.getAttribute("TheT"))
            return None
        
        def set_TheT(self, value):
            self.node.setAttribute("TheT", str(value))
            
        TheT = property(get_TheT, set_TheT)
        
        def get_DeltaT(self):
            '''# of seconds since the beginning of the experiment'''
            if self.node.hasAttribute("DeltaT"):
                return float(self.node.getAttribute("DeltaT"))
            return None
        
        def set_DeltaT(self, value):
            self.node.setAttribute("DeltaT", str(value))
            
        DeltaT = property(get_DeltaT, set_DeltaT)
        
        @property
        def ExposureTime(self):
            '''Units are seconds. Duration of acquisition????'''
            if self.node.hasAttribute("ExposureTime"):
                return float(self.node.getAttribute("ExposureTime"))
            return None
        
        def get_PositionX(self):
            '''X position of stage'''
            if self.node.hasAttribute("PositionX"):
                return float(self.node.getAttribute("PositionX"))
            return None
        
        def set_PositionX(self, value):
            self.node.setAttribute("PositionX", str(value))
            
        PositionX = property(get_PositionX, set_PositionX)
        
        def get_PositionY(self):
            '''Y position of stage'''
            if self.node.hasAttribute("PositionY"):
                return float(self.node.getAttribute("PositionY"))
            return None
        
        def set_PositionY(self, value):
            self.node.setAttribute("PositionY", str(value))
            
        PositionY = property(get_PositionY, set_PositionY)
        
        def get_PositionZ(self):
            '''Z position of stage'''
            if self.node.hasAttribute("PositionZ"):
                return float(self.node.getAttribute("PositionZ"))
            return None
        
        def set_PositionZ(self, value):
            self.node.setAttribute("PositionZ", str(value))
            
        PositionZ = property(get_PositionZ, set_PositionZ)
        
    class Pixels(object):
        '''The OME/Image/Pixels element
        
        The Pixels element represents the pixels in an OME image and, for
        an OME-XML encoded image, will actually contain the base-64 encoded
        pixel data. It has the X, Y, Z, C, and T extents of the image
        and it specifies the channel interleaving and channel depth.
        '''
        def __init__(self, node):
            self.node = node
            
        def get_ID(self):
            return self.node.getAttribute("ID")
        def set_ID(self, value):
            self.node.setAttribute("ID", value)
        ID = property(get_ID, set_ID)
        
        def get_DimensionOrder(self):
            '''The ordering of image planes in the file

            A 5-letter code indicating the ordering of pixels, from the most
            rapidly varying to least. Use the DO_* constants (for instance
            DO_XYZCT) to compare and set this.
            '''
            return self.node.getAttribute("DimensionOrder")
        def set_DimensionOrder(self, value):
            self.node.setAttribute("DimensionOrder", value)
        DimensionOrder = property(get_DimensionOrder, set_DimensionOrder)
        
        def get_PixelType(self):
            '''The pixel bit type, for instance PT_UINT8
            
            The pixel type specifies the datatype used to encode pixels
            in the image data. You can use the PT_* constants to compare
            and set the pixel type.
            '''
            return self.node.getAttribute("Type")
        def set_PixelType(self, value):
            self.node.setAttribute("Type", value)
        PixelType = property(get_PixelType, set_PixelType)
        
        def get_SizeX(self):
            '''The dimensions of the image in the X direction in pixels'''
            return int(self.node.getAttribute("SizeX"))
        def set_SizeX(self, value):
            self.node.setAttribute("SizeX", str(value))
        SizeX = property(get_SizeX, set_SizeX)
        
        def get_SizeY(self):
            '''The dimensions of the image in the Y direction in pixels'''
            return int(self.node.getAttribute("SizeY"))
        def set_SizeY(self, value):
            self.node.setAttribute("SizeY", str(value))
        SizeY = property(get_SizeY, set_SizeY)
        
        def get_SizeZ(self):
            '''The dimensions of the image in the Z direction in pixels'''
            return int(self.node.getAttribute("SizeZ"))
        def set_SizeZ(self, value):
            self.node.setAttribute("SizeZ", str(value))
        SizeZ = property(get_SizeZ, set_SizeZ)
        
        def get_SizeT(self):
            '''The dimensions of the image in the T direction in pixels'''
            return int(self.node.getAttribute("SizeT"))
        def set_SizeT(self, value):
            self.node.setAttribute("SizeT", str(value))
        SizeT = property(get_SizeT, set_SizeT)
        
        def get_SizeC(self):
            '''The dimensions of the image in the C direction in pixels'''
            return int(self.node.getAttribute("SizeC"))
        def set_SizeC(self, value):
            self.node.setAttribute("SizeC", str(value))
        SizeC = property(get_SizeC, set_SizeC)
        
        def get_channel_count(self):
            '''The number of channels in the image
            
            You can change the number of channels in the image by
            setting the channel_count:
            
            pixels.channel_count = 3
            pixels.Channel(0).Name = "Red"
            ...
            '''
            return len(self.node.getElementsByTagNameNS(NS_OME, "Channel"))
        
        def set_channel_count(self, value):
            assert value > 0
            dom = get_dom(self.node)
            while(self.channel_count > value):
                last = self.node.getElementsByTagNameNS(NS_OME, "Channel")[-1]
                self.node.removeChild(last)
                last.unlink()
            
            while(self.channel_count < value):
                last = self.node.getElementsByTagNameNS(NS_OME, "Channel")[-1]
                new_channel = OMEXML.Channel(dom.createElementNS(NS_OME, "Channel"))
                insert_after(last, new_channel.node)
                new_channel.ID = str(uuid.uuid4())
                new_channel.Name = new_channel.ID
                new_channel.SamplesPerPixel = 1
                
        channel_count = property(get_channel_count, set_channel_count)
        
        def Channel(self, index=0):
            '''Get the indexed channel from the Pixels element'''
            channel = self.node.getElementsByTagNameNS(NS_OME, "Channel")[index]
            return OMEXML.Channel(channel)
    
        def get_plane_count(self):
            '''The number of planes in the image
            
            An image with only one plane or an interleaved color plane will
            often not have any planes.
            
            You can change the number of planes in the image by
            setting the plane_count:
            
            pixels.plane_count = 3
            pixels.Plane(0).TheZ=pixels.Plane(0).TheC=pixels.Plane(0).TheT=0
            ...
            '''
            return len(self.node.getElementsByTagNameNS(NS_OME, "Plane"))
        
        def set_plane_count(self, value):
            assert value >= 0
            dom = get_dom(self.node)
            while(self.plane_count > value):
                last = self.node.getElementsByTagNameNS(NS_OME, "Plane")[-1]
                self.node.removeChild(last)
                last.unlink()
            
            while(self.plane_count < value):
                new_plane = OMEXML.Plane(dom.createElementNS(NS_OME, "Plane"))
                if self.plane_count > 0:
                    last = self.node.getElementsByTagNameNS(NS_OME, "Plane")[-1]
                    insert_after(last, new_plane.node)
                else:
                    self.node.appendChild(new_plane.node)
                
        plane_count = property(get_plane_count, set_plane_count)
        
        def Plane(self, index=0):
            '''Get the indexed plane from the Pixels element'''
            plane = self.node.getElementsByTagNameNS(NS_OME, "Plane")[index]
            return OMEXML.Plane(plane)
        
    class StructuredAnnotations(dict):
        '''The OME/StructuredAnnotations element
        
        Structured annotations let OME-XML represent metadata from other file
        formats, for example the tag metadata in TIFF files. The
        StructuredAnnotations element is a container for the structured
        annotations.
        
        Images can have structured annotation references. These match to
        the IDs of structured annotations in the StructuredAnnotations
        element. You can get the structured annotations in an OME-XML document
        using a dictionary interface to StructuredAnnotations.
        
        Pragmatically, TIFF tag metadata is stored as key/value pairs in
        OriginalMetadata annotations - in the context of CellProfiler,
        callers will be using these to read tag data that's not represented
        in OME-XML such as the bits per sample and min and max sample values.
        
        '''
        
        def __init__(self, node):
            self.node = node
            
        def __getitem__(self, key):
            for child in iter_children(self.node, xml.dom.Node.ELEMENT_NODE):
                if child.getAttribute("ID") == key:
                    return child
            raise IndexError('ID "%s" not found' % key)
        
        def keys(self):
            return [child.getAttribute("ID")
                    for child in iter_children(self.node, xml.dom.Node.ELEMENT_NODE)
                    if child.hasAttribute("ID")]
        
        def has_key(self, key):
            for child in iter_children(self.node, xml.dom.Node.ELEMENT_NODE):
                if (child.hasAttribute("ID") and 
                    child.getAttribute("ID") == key):
                    return True
            return False
        
        def add_original_metadata(self, key, value):
            '''Create an original data key/value pair
            
            key - the original metadata's key name, for instance OM_PHOTOMETRIC_INTERPRETATION
            
            value - the value, for instance, "RGB"
            
            returns the ID for the structured annotation.
            '''
            dom = get_dom(self.node)
            xml_annotation = dom.createElementNS(NS_SA, "XMLAnnotation")
            self.node.appendChild(xml_annotation)
            node_id = str(uuid.uuid4())
            xml_annotation.setAttribute("ID", node_id)
            xa_value = dom.createElementNS(NS_SA, "Value")
            xml_annotation.appendChild(xa_value)
            ov = dom.createElementNS(NS_ORIGINAL_METADATA, "OriginalMetadata")
            xa_value.appendChild(ov)
            ov_key = dom.createElementNS(NS_ORIGINAL_METADATA, "Key")
            ov.appendChild(ov_key)
            set_text(ov_key, key)
            ov_value = dom.createElementNS(NS_ORIGINAL_METADATA, "Value")
            ov.appendChild(ov_value)
            set_text(ov_value, value)
            return node_id

        def iter_original_metadata(self):
            '''An iterator over the original metadata in structured annotations
            
            returns (<annotation ID>, (<key, value>))
            
            where <annotation ID> is the ID attribute of the annotation (which
            can be used to tie an annotation to an image)
            
                  <key> is the original metadata key, typically one of the
                  OM_* names of a TIFF tag
                  <value> is the value for the metadata
            '''
            #
            # Here's the XML we're traversing:
            #
            # <StructuredAnnotations>
            #    <XMLAnnotation>
            #        <Value>
            #            <OriginalMetadta>
            #                <Key>Foo</Key>
            #                <Value>Bar</Value>
            #            </OriginalMetadata>
            #        </Value>
            #    </XMLAnnotation>
            # </StructuredAnnotations>
            #
            for annotation_node in self.node.getElementsByTagNameNS(
                NS_SA, "XMLAnnotation"): # <XMLAnnotation/>
                annotation_id = annotation_node.getAttribute("ID")
                for xa_value_node in annotation_node.getElementsByTagNameNS(
                    NS_SA, "Value"):     # <Value/>
                    for om_node in xa_value_node.getElementsByTagNameNS(
                        NS_ORIGINAL_METADATA, "OriginalMetadata"): # <OriginalMetadata>
                        key_nodes = om_node.getElementsByTagNameNS(
                            NS_ORIGINAL_METADATA, "Key")
                        value_nodes = om_node.getElementsByTagNameNS(
                            NS_ORIGINAL_METADATA, "Value")
                        if len(key_nodes) > 0 and len(value_nodes) > 0:
                            key_text = get_text(key_nodes[0])
                            value_text = get_text(value_nodes[0])
                            if key_text is not None and value_text is not None:
                                yield annotation_id, (key_text, value_text)
                            else:
                                logger.warn("Original metadata was missing key or value:" + om_node.toxml())
            return
                    
        def has_original_metadata(self, key):
            '''True if there is an original metadata item with the given key'''
            return any([k == key 
                        for annotation_id, (k, v) 
                        in self.iter_original_metadata()])
        
        def get_original_metadata_value(self, key, default=None):
            '''Return the value for a particular original metadata key
            
            key - key to search for
            default - default value to return if not found
            '''
            for annotation_id, (k, v) in self.iter_original_metadata():
                if k == key:
                    return v
            return default
            
        def get_original_metadata_refs(self, ids):
            '''For a given ID, get the matching original metadata references
            
            ids - collection of IDs to match
            
            returns a dictionary of key to value
            '''
            d = {}
            for annotation_id, (k,v) in self.iter_original_metadata():
                if annotation_id in ids:
                    d[k] = v
            return d
        
        @property
        def OriginalMetadata(self):
            return OMEXML.OriginalMetadata(self)
    
    class OriginalMetadata(dict):
        '''View original metadata as a dictionary
        
        Original metadata holds "vendor-specific" metadata including TIFF
        tag values.
        '''
        def __init__(self, sa):
            '''Initialized with the structured_annotations class instance'''
            self.sa = sa
            
        def __getitem__(self, key):
            return self.sa.get_original_metadata_value(key)
        
        def __setitem__(self, key, value):
            self.sa.add_original_metadata(key, value)
            
        def __iter__(self):
            for annotation_id, (key, value) in self.sa.iter_original_metadata():
                yield key
                
        def __len__(self):
            return len(list(self.sa_iter_original_metadata()))
        
        def keys(self):
            return [key 
                    for annotation_id, (key, value) 
                    in self.sa.iter_original_metadata()]
            
        def has_key(self, key):
            for annotation_id, (k, value) in self.sa.iter_original_metadata():
                if k == key:
                    return True
            return False

        def iteritems(self):
            for annotation_id, (key, value) in self.sa.iter_original_metadata():
                yield key, value
                
    class PlatesDucktype(object):
        '''It looks like a list of plates'''
        def __init__(self, root):
            self.root = root
            
        def __getitem__(self, key):
            plates = self.root.getElementsByTagNameNS(NS_SPW, "Plate")
            if isinstance(key, slice):
                return [OMEXML.Plate(plate) for plate in plates[key]]
            return OMEXML.Plate(plates[key])
        
        def __len__(self):
            return len(self.root.getElementsByTagNameNS(NS_SPW, "Plate"))
        
        def __iter__(self):
            for plate in self.root.getElementsByTagNameNS(NS_SPW, "Plate"):
                yield OMEXML.Plate(plate)
                
        def newPlate(self, name, plate_id = str(uuid.uuid4())):
            new_plate_node = get_dom(self.root).createElementNS(NS_SPW, "Plate")
            self.root.appendChild(new_plate_node)
            new_plate = OMEXML.Plate(new_plate_node)
            new_plate.ID = plate_id
            new_plate.Name = name
            return new_plate
        
    class Plate(object):
        '''The SPW:Plate element
        
        This represents the plate element of the SPW schema:
        http://www.openmicroscopy.org/Schemas/SPW/2007-06/
        '''
        def __init__(self, node):
            self.node = node
            
        def get_ID(self):
            return self.node.getAttribute("ID")
        
        def set_ID(self, value):
            self.node.setAttribute("ID", value)
            
        ID = property(get_ID, set_ID)
        
        def get_Name(self):
            return self.node.getAttribute("Name")
        
        def set_Name(self, value):
            self.node.setAttribute("Name", value)
            
        Name = property(get_Name, set_Name)
        
        def get_Status(self):
            return self.node.getAttribute("Status")
        
        def set_Status(self, value):
            self.node.setAttribute("Status", value)
            
        Status = property(get_Status, set_Status)
        
        def get_ExternalIdentifier(self):
            return self.node.getAttribute("ExternalIdentifier")
        
        def set_ExternalIdentifier(self, value):
            return self.node.setAttribute("ExternalIdentifier", value)
        
        ExternalIdentifier = property(get_ExternalIdentifier, set_ExternalIdentifier)
        
        def get_ColumnNamingConvention(self):
            # Consider a default if not defined of NC_NUMBER
            return self.node.getAttribute("ColumnNamingConvention")
        
        def set_ColumnNamingConvention(self, value):
            assert value in (NC_LETTER, NC_NUMBER)
            self.node.setAttribute("ColumnNamingConvention", value)
        ColumnNamingConvention = property(get_ColumnNamingConvention, 
                                          set_ColumnNamingConvention)
            
        def get_RowNamingConvention(self):
            # Consider a default if not defined of NC_LETTER
            return self.node.getAttribute("RowNamingConvention")
        
        def set_RowNamingConvention(self, value):
            assert value in (NC_LETTER, NC_NUMBER)
            self.node.setAttribute("RowNamingConvention", value)
        RowNamingConvention = property(get_RowNamingConvention,
                                       set_RowNamingConvention)
        
        def get_WellOriginX(self):
            return (float(self.node.getAttribute("WellOriginX")) 
                    if self.node.hasAttribute("WellOriginX") else None)
        
        def set_WellOriginX(self, value):
            self.node.setAttribute("WellOriginX", str(value))
        WellOriginX = property(get_WellOriginX, set_WellOriginX)
        
        def get_WellOriginY(self):
            return (float(self.node.getAttribute("WellOriginY")) 
                    if self.node.hasAttribute("WellOriginY") else None)
        
        def set_WellOriginY(self, value):
            self.node.setAttribute("WellOriginY", str(value))
        WellOriginY = property(get_WellOriginY, set_WellOriginY)
        
        def get_Rows(self):
            return (int(self.node.getAttribute("Rows"))
                    if self.node.hasAttribute("Rows") else None)
        
        def set_Rows(self, value):
            self.node.setAttribute("Rows", str(value))
        Rows = property(get_Rows, set_Rows)
        
        def get_Columns(self):
            return (int(self.node.getAttribute("Columns"))
                    if self.node.hasAttribute("Columns") else None)
        def set_Columns(self, value):
            self.node.setAttribute("Columns", str(value))
        Columns = property(get_Columns, set_Columns)
        
        def get_Description(self):
            descriptions = self.node.getElementByTagNameNS(NS_SPW, "Description")
            if len(descriptions) == 0:
                return None
            return get_text(descriptions[0])
        
        def set_Description(self, text):
            make_text_node(self.node, NS_SPW, "Description", test)
        Description = property(get_Description, set_Description)
        
        def get_Well(self):
            '''The well dictionary / list'''
            return OMEXML.WellsDucktype(self)
        Well = property(get_Well)
        
        def get_well_name(self, well):
            '''Get a well's name, using the row and column convention'''
            result = "".join([
                "%02d" % (i+1) if convention == NC_NUMBER
                else "ABCDEFGHIJKLMNOP"[i]
                for i, convention
                in ((well.Row, self.RowNamingConvention or NC_LETTER),
                    (well.Column, self.ColumnNamingConvention or NC_NUMBER))])
            return result
        
    class WellsDucktype(dict):
        '''The WellsDucktype lets you retrieve and create wells
        
        The WellsDucktype looks like a dictionary but lets you reference
        the wells in a plate using indexing. Types of indexes:
        
        list indexing: e.g. plate.Well[14] gets the 14th well as it appears
                       in the XML
        dictionary_indexing:
            by well name - e.g. plate.Well["A08"]
            by row and column - e.g. plate.Well[1,3] (B03)
            by ID - e.g. plate.Well["Well:0:0:0"]
        If the ducktype is unable to parse a well name, it assumes you're
        using an ID.
        '''
        def __init__(self, plate):
            self.plate_node = plate.node
            self.plate = plate
            
        def __len__(self):
            return len(self.plate_node.getElementsByTagNameNS(NS_SPW, "Well"))
        
        def __getitem__(self, key):
            all_wells = self.plate_node.getElementsByTagNameNS(NS_SPW, "Well")
            if isinstance(key, slice):
                return [OMEXML.Well(w) for w in all_wells[key]]
            if hasattr(key, "__len__") and len(key) == 2:
                well = OMEXML.Well(None)
                for w in all_wells:
                    well.node = w
                    if well.Row == key[0] and well.Column == key[1]:
                        return well
            if isinstance(key, int):
                return OMEXML.Well(all_wells[key])
            well = OMEXML.Well(None)
            for w in all_wells:
                well.node = w
                if self.plate.get_well_name(well) == key:
                    return well
                if well.ID == key:
                    return well
            return None
        
        def __iter__(self):
            '''Return the standard name for all wells on the plate
            
            for instance, 'B03' for a well with Row=1, Column=2 for a plate
            with the standard row and column naming convention
            '''
            all_wells = self.plate_node.getElementsByTagNameNS(NS_SPW, "Well")
            well = OMEXML.Well(None)
            for w in all_wells:
                well.node = w
                yield self.plate.get_well_name(well)
                
        def new(self, row, column, well_id = str(uuid.uuid4())):
            '''Create a new well at the given row and column
            
            row - index of well's row
            column - index of well's column
            well_id - the ID attribute for the well
            '''
            dom = get_dom(self.plate_node)
            well_node = dom.createElementNS(NS_SPW, "Well")
            self.plate_node.appendChild(well_node)
            well = OMEXML.Well(well_node)
            well.Row = row
            well.Column = column
            well.ID = well_id
            return well
            
    class Well(object):
        def __init__(self, node):
            self.node = node
            
        def get_Column(self):
            return int(self.node.getAttribute("Column"))
        def set_Column(self, value):
            self.node.setAttribute("Column", str(value))
        Column = property(get_Column, set_Column)
        
        def get_Row(self):
            return int(self.node.getAttribute("Row"))
        def set_Row(self, value):
            self.node.setAttribute("Row", str(value))
        Row = property(get_Row, set_Row)
        
        def get_ID(self):
            return self.node.getAttribute("ID")
        def set_ID(self, value):
            self.node.setAttribute("ID", value)
        ID = property(get_ID, set_ID)
        
        def get_Sample(self):
            return OMEXML.WellSampleDucktype(self.node)
        Sample = property(get_Sample)
        
        def get_ExternalDescription(self):
            return self.node.getAttribute("ExternalDescription")
        
        def set_ExternalDescription(self, value):
            return self.node.setAttribute("ExternalDescription", value)
        
        ExternalDescription = property(get_ExternalDescription, set_ExternalDescription)
        
        def get_ExternalIdentifier(self):
            return self.node.getAttribute("ExternalIdentifier")
        
        def set_ExternalIdentifier(self, value):
            return self.node.setAttribute("ExternalIdentifier", value)
        
        ExternalIdentifier = property(get_ExternalIdentifier, set_ExternalIdentifier)
        
        def get_Color(self):
            return int(self.node.getAttribute("Color"))
        
        def set_Color(self, value):
            self.node.setAttribute("Color", str(value))
        
    class WellSampleDucktype(list):
        '''The WellSample elements in a well
        
        This is made to look like an indexable list so that you can do
        things like:
        wellsamples[0:2]
        '''
        def __init__(self, well_node):
            self.well_node = well_node
            
        def __len__(self):
            return len(self.well_node.getElementsByTagNameNS(NS_SPW, "WellSample"))
        
        def __getitem__(self, key):
            all_samples = self.well_node.getElementsByTagNameNS(NS_SPW, "WellSample")
            if isinstance(key, slice):
                return [OMEXML.WellSample(s) 
                        for s in all_samples[key]]
            return OMEXML.WellSample(all_samples[int(key)])
        
        def __iter__(self):
            '''Iterate through the well samples.'''
            all_samples = self.well_node.getElementsByTagNameNS(NS_SPW, "WellSample")
            for s in all_samples:
                yield OMEXML.WellSample(s)
                
        def new(self, wellsample_id = str(uuid.uuid4()), index = None):
            '''Create a new well sample
            '''
            if index is None:
                index = reduce(max, [s.Index for s in self], -1) + 1
            new_node = get_dom(self.well_node).createElementNS(NS_SPW, "WellSample")
            self.well_node.appendChild(new_node)
            s = OMEXML.WellSample(new_node)
            s.ID = wellsample_id
            s.Index = index
        
    class WellSample(object):
        '''The WellSample is a location within a well'''
        def __init__(self, node):
            self.node = node
            
        def get_ID(self):
            return self.node.getAttribute("ID")
        def set_ID(self, value):
            self.node.setAttribute("ID", value)
        ID = property(get_ID, set_ID)

        def get_PositionX(self):
            try:
                return float(self.node.getAttribute("PositionX"))
            except:
                return None
            
        def set_PositionX(self, value):
            self.node.setAttribute("PositionX", str(value))
        PositionX = property(get_PositionX, set_PositionX)
        
        def get_PositionY(self):
            try:
                return float(self.node.getAttribute("PositionY"))
            except:
                return None
            
        def set_PositionY(self, value):
            self.node.setAttribute("PositionY", str(value))
        PositionY = property(get_PositionY, set_PositionY)
        
        def get_Timepoint(self):
            return self.node.getAttribute("Timepoint")
        
        def set_Timepoint(self, value):
            if isinstance(value, datetime.datetime):
                value = value.isoformat()
            self.node.setAttribute("Timepoint", value)
        Timepoint = property(get_Timepoint, set_Timepoint)
        
        def get_Index(self):
            try:
                return int(self.node.getAttribute("Index"))
            except:
                return None
        def set_Index(self, value):
            self.node.setAttribute("Index", str(value))
            
        Index = property(get_Index, set_Index)
        
        def get_ImageRef(self):
            '''Get the ID of the image of this site'''
            refs = self.node.getElementsByTagNameNS(NS_SPW, "ImageRef")
            if len(refs) == 0:
                return None
            return refs[0].getAttribute("ID")
        
        def set_ImageRef(self, value):
            '''Add a reference to the image of this site'''
            refs = self.node.getElementsByTagNameNS(NS_SPW, "ImageRef")
            if len(refs) == 0:
                ref = get_dom(self.node).createElementNS(NS_SPW, "ImageRef")
                self.node.appendChild(ref)
            else:
                ref = refs[0]
            ref.setAttribute("ID", value)
        ImageRef = property(get_ImageRef, set_ImageRef)
        