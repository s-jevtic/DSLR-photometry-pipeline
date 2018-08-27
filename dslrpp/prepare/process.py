"""This submodule contains the DSLRImage class and its Monochrome subclass.

The DSLRImage class serves the purpose of containing all needed information
for a frame, as well as the methods for binning, extracting monochrome
channels, and writing the file to FITS format.
"""
import os
from enum import IntEnum
from fractions import Fraction
from datetime import datetime
from astropy.time import Time
from astropy.io import fits
from skimage.measure import block_reduce
import exifread
import numpy as np
import rawpy

class ImageType(IntEnum):
    LIGHT = 0
    BIAS = 1
    DARK = 2
    FLAT = 3

class Color(IntEnum):
    RED = 0
    GREEN = 1
    BLUE = 2

class DSLRImage:
    """Loads an image from RAW format, stores the metadata and writes the image
    as a NumPy array.
    """
    fnum=np.zeros((4,4), dtype=int)
    # Declares a NumPy 2d array for filename serialization
    def __init__(
            self, impath, itype=ImageType.LIGHT, color=None
            ):
        self.impath = impath
        self.imtype = itype
        self.imdata, self.exptime, self.jdate = self.__parseData(impath)
        self.imcolor = None
        self._genPath() # generates the serialized filename
        print("Initializing image class: " + str(self))

    def binImage(self, x, y=None, fn='mean'):
        """Bins the data from the image. Requires the window width.
        If window height is not specified, the window is assumed to be square.
        Binning can be performed via arithmetic mean or median, which is
        specified in the fn argument.
        The default is arithmetic mean.
        """
        if y is None:
            y = x
        print(
                "Binning image: " + str(self) + " (" + str(x) + "x" + str(y)
                + ")")
#        h = len(self.imdata)
#        w = len(self.imdata[0])
#        hb = h - h%y
#        wb = w - w%x
#        # reduces the image size in case it isn't divisible by window size
#        imdata_resized = np.resize(self.imdata, (hb, w, 3))
#        imdata_resized1 = np.empty((hb, wb, 3))
#        for r in range(len(imdata_resized)):
#            imdata_resized1[r] = np.resize(imdata_resized[r], (wb, 3))
#        imdata_resized1 = imdata_resized1.reshape((h//x, wb, y, 3), order='A')
#        imdata_resized1 = imdata_resized1.reshape(
#                (h//y, w//x, y, x, 3), order='F'
#                )
#        bindata=np.empty((h//y, w//x, 3))
#        # reshapes the matrix into a set of arrays with length x*y
#        for r in range(len(bindata)):
#            for c in range(len(bindata[r])):
#                # bins the arrays using the specified function
#                if fn is 'mean':
#                    bindata[r][c] = np.mean(imdata_resized1[r][c])
#                elif fn is 'median':
#                    bindata[r][c] = np.median(imdata_resized1[r][c])
#                else:
#                    raise ValueError('Invalid argument for \'fn\' parameter')
#        bindata = np.resize(bindata, (h//y, w//x, 1, 1, 3))
#        bindata = bindata.reshape(h//y, w//x, 3)
#        # reshapes the matrix back to its original form
        bindata = block_reduce(
                self.imdata, (x,y,1), np.mean, np.mean(self.imdata)
                )
        self.imdata = bindata

    def extractChannel(self, color):
        """Extracts the specified channel (R,G,B) from the RGB image."""
        print("Extracting " + color.name + " channel from image " + str(self))
        imdata = self.imdata[:,:,color.value]
        return Monochrome(imdata, self, color)

    def saveFITS(self, impath):
        """Writes the data to a FITS file."""
        impath += self.fname
        hdu = fits.PrimaryHDU(self.imdata)
        print("Writing image " + str(self) + " to file: " + impath + ".fits")
        hdu.header['EXPTIME'] = self.exptime
        d = Time(self.jdate, format='jd', scale='utc').iso.split()
        hdu.header['DATE-OBS'] = d[0]
        hdu.header['TIME-OBS'] = d[1]
        hdu.header['IMAGETYP'] = self.imtype.name
        n = 1
        try:
            hdu.writeto(impath + ".fits")
        except OSError:
            error = True
            while(error is True):
                try:
                    hdu.writeto(impath + "_" + str(n) + ".fits")
                    error = False
                except OSError:
                    n += 1

    #def getData(self):
        # loads the image data from the temporary folder
        #return np.load(self.tmpPath + self.fname + '.npy')

    #def _setData(self, idata):
        # writes the image data to the temporary folder
        #np.save(self.tmpPath + self.fname, idata)

    def _genPath(self):
        # generates a serialized file name in the format
        # imagetype_ordinalnumber
        #
        # if the image is monochrome, the format is
        # imagetype_ordinalnumber_color
        cls = type(self)
        itype = self.imtype
        try:
            color = self.imcolor.value
        except(AttributeError):
            color = 3
        if(cls.fnum[itype][color] is None):
            cls.fnum[itype][color] = 0
        ftype = {0:"light", 1:"bias", 2:"dark", 3:"flat"}[itype]
        try:
            self.fname = (
                    ftype + "_" + str(cls.fnum[itype][color])
                    + '_' + self.imcolor.name
                    )
        except AttributeError:
            self.fname = ftype + "_" + str(cls.fnum[itype][color])
        cls.fnum[itype][color] += 1

        self.tmpPath = os.path.dirname(self.impath) + '\\temp\\'
        try:
            os.makedirs(self.tmpPath)
        except(OSError):
            pass

    def __parseData(self, impath):
        # reads the metadata from the RAW file
        print("Reading file: " + impath)
        with rawpy.imread(impath) as img:
            idata = img.postprocess(
                    output_bps=16, no_auto_bright=True, #no_auto_scale=True
                    )
            with open(impath, 'rb') as f:
                tags = exifread.process_file(f)
                exptime = float(
                        Fraction(tags.get('EXIF ExposureTime').printable)
                        )
                dt = tags.get('EXIF DateTimeOriginal').printable
                (date, _,time) = dt.partition(' ')
                dt = tuple([int(i) for i in date.split(':') + time.split(':')])
                dt = datetime(*dt).isoformat()
                #ofs = tags.get('EXIF TimeZoneOffset').printable
                jdate = Time(dt, format='isot', scale='utc').jd
            return idata, exptime, jdate

    def __str__(self):
        return("DSLRImage(imtype=" + str(self.imtype)
                          + ", color=" + str(self.imcolor)
                          + ", fname=" + self.fname
                          + ")"
                    )

    def __del__(self):
        # deletes the temporary file/folder
        print("Deleting image class: " + str(self))
#        os.remove(self.tmpPath + self.fname + '.npy')
#        try:
#            os.rmdir(self.tmpPath)
#        except OSError:
#            pass

class Monochrome(DSLRImage):
    """A subtype of DSLRImage for single-color images.
    Is meant to be generated from the extractChannel method. Avoid using the
    class directly.
    """
    def __init__(
            self, imdata, origin, color=Color.GREEN,
            stacked=False
            ):
        self.exptime = origin.exptime
        self.jdate = origin.jdate
        self.impath = origin.impath
        self.imtype = origin.imtype
        self.imcolor = color
        self._genPath()
        self.imdata = imdata

    def binImage(self, x, y=None, fn='mean'):
        """Same as the binImage method in the superclass, but optimized for
        monochrome arrays.
        """
        if y is None:
            y = x
        print(
                "Binning monochrome image: " + str(self)
                + " (" + str(x) + "x" + str(y) + ")"
                )
#        h = len(self.imdata)
#        w = len(self.imdata[0])
#        hb = h - h%y
#        wb = w - w%x
#        imdata_resized = np.resize(self.imdata, (hb, w))
#        imdata_resized1 = np.empty((hb, wb))
#        for r in range(len(imdata_resized)):
#            imdata_resized1[r] = np.resize(imdata_resized[r], wb)
#        imdata_resized1 = imdata_resized1.reshape((h//x, wb, y), order='A')
#        imdata_resized1 = imdata_resized1.reshape(
#                (h//y, w//x, y, x), order='F'
#                )
#        bindata=np.empty((h//y, w//x))
#        for r in range(len(bindata)):
#            for c in range(len(bindata[r])):
#                if fn is 'mean':
#                    bindata[r][c] = np.mean(imdata_resized1[r][c])
#                elif fn is 'median':
#                    bindata[r][c] = np.median(imdata_resized1[r][c])
#                else:
#                    raise ValueError('Invalid argument for \'fn\' parameter')
#        bindata = np.resize(bindata, (h//y, w//x, 1, 1))
#        bindata = bindata.reshape(h//y, w//x)
        bindata = block_reduce(
                self.imdata, (x,y), np.mean, np.mean(self.imdata)
                )
        self.imdata = bindata