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
from astropy.modeling import models, fitting
from photutils import CircularAperture, CircularAnnulus
from photutils.centroids import centroid_2dg
from skimage.registration import phase_cross_correlation
from skimage.measure import block_reduce
import exifread
import numpy as np
import rawpy
from matplotlib import pyplot as plt

__all__ = ["ImageType", "Color", "DSLRImage", "Monochrome", "Star"]

w = 5
# polusirina prozora
# jos uvek ne znamo koja vrednost bi morala da bude
CurrentFrame = None


class ImageType(IntEnum):
    LIGHT = 0
    BIAS = 1
    DARK = 2
    FLAT = 3


class Color(IntEnum):
    RED = 0
    GREEN = 1
    BLUE = 2


def _get_current_frame():
    return CurrentFrame


def _demosaic(im):
    """Demosaics the image,
    i.e. turns a RGGB monochrome array into a RGB array.
    """
    _im = np.resize(im, (len(im)-len(im) % 2, len(im[0])-len(im[0]) % 2))
    _im = np.reshape(_im, (len(im)//2, 2, len(im[0])//2, 2))
    im = np.empty((len(im)//2, len(im[0])//2, 3))
    im[:, :, 0] = _im[:, 0, :, 0]
    im[:, :, 1] = (_im[:, 0, :, 1] + _im[:, 1, :, 0])/2
    im[:, :, 2] = _im[:, 1, :, 1]
    return im


def isRaw(f):
    print("Checking if file is in RAW format:", f)
    try:
        rawpy.imread(f)
        return True
    except Exception as e:
        if type(e) is rawpy.NotSupportedError:
            print("File unsupported:", f)
        else:
            print("Error:", e)
        print("Ignoring this file.")
        return False


class DSLRImage:
    """Loads an image from RAW format, stores the metadata and writes the image
    as a NumPy array.
    """

    fnum = np.zeros((4, 4), dtype=int)
    # Declares a NumPy 2d array for filename serialization

    def __init__(
            self, impath, itype=ImageType.LIGHT, color=None
            ):
        print('Initializing image class from file:', impath)
        self.impath = impath
        self.imtype = itype
        self.imcolor = None
        self.imdata, self.exptime, self.jdate = self.__parseData(impath)
        self._genPath()  # generates the serialized filename
        self._binX = 1
        self._binY = 1
        print("Initialized image class: " + str(self))

    def binImage(self, x, y=None):
        """Bins the data from the image. Requires the window width.
        If window height is not specified, the window is assumed to be square.
        """
        if x is None:
            x = 1
        if y is None:
            y = x
        if (x == 1) and (y == 1):
            return
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
                self.imdata, (x, y, 1), np.mean, np.mean(self.imdata)
                )
        self.imdata = bindata
        self._binX *= x
        self._binY *= y

    def extractChannel(self, color):
        """Extracts the specified channel (R,G,B) from the RGB image."""
        print("Extracting " + color.name + " channel from image " + str(self))
        try:
            imdata = self.imdata[:, :, color.value]
        except AttributeError:
            print("AttributeError for", str(self))
        return Monochrome(imdata, self, color)

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
        ftype = {0: "light", 1: "bias", 2: "dark", 3: "flat"}[itype]
        try:
            self.fname = (
                    ftype + "_" + str(cls.fnum[itype][color])
                    + '_' + self.imcolor.name
                    )
        except AttributeError:
            self.fname = ftype + "_" + str(cls.fnum[itype][color])
        cls.fnum[itype][color] += 1

        self.tmpPath = os.path.dirname(self.impath) + '/temp/'
        try:
            os.makedirs(self.tmpPath)
        except(OSError):
            pass

    def __parseData(self, impath):
        # reads the metadata from the RAW file
        print("Reading file: " + impath)
        with rawpy.imread(impath) as img:
            iarray = img.raw_image.copy()
            if len(iarray.shape) == 2:
                idata = _demosaic(iarray)
            else:
                idata = iarray
        with open(impath, 'rb') as f:
            tags = exifread.process_file(f)
            exptime = float(
                    Fraction(tags.get('EXIF ExposureTime').printable)
                    )
            dt = tags.get('EXIF DateTimeOriginal').printable
            (date, _, time) = dt.partition(' ')
            dt = tuple([int(i) for i in date.split(':') + time.split(':')])
            dt = datetime(*dt).isoformat()
            #ofs = tags.get('EXIF TimeZoneOffset').printable
            jdate = Time(dt, format='isot', scale='utc').jd
        return idata, exptime, jdate

    def __str__(self):
        try:
            return(
                    "DSLRImage(imtype=" + str(self.imtype)
                    + ", color=" + str(self.imcolor)
                    + ", fname=" + self.fname
                    + ")"
                    )
        except(AttributeError):
            return(
                    "DSLRImage(imtype=" + str(self.imtype)
                    + ", color=" + str(self.imcolor)
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
            stacked=False, translated=False
            ):
        self.exptime = origin.exptime
        self.jdate = origin.jdate
        self.impath = origin.impath
        self.imtype = origin.imtype
        self._binX = origin._binX
        self._binY = origin._binY
        if type(origin) == Monochrome:
            self.imcolor = origin.imcolor
        else:
            self.imcolor = color
        self._genPath()
        self.imdata = imdata
        self.stars = []

    def saveFITS(self, path, fname=None):
        """Writes the data to a FITS file."""
        impath = path + (self.fname if fname is None else fname)
        hdu = fits.PrimaryHDU(self.imdata.astype('uint16'))
        print("Writing image " + str(self) + " to file: " + impath + ".fits")
        hdu.header['EXPTIME'] = self.exptime
        d = Time(self.jdate, format='jd', scale='utc').isot
        hdu.header['DATE-OBS'] = d
        hdu.header['IMAGETYP'] = self.imtype.name
        hdu.header['XBINNING'] = self._binX
        hdu.header['YBINNING'] = self._binY
        n = 1
        try:
            hdu.writeto(impath + ".fits")
        except OSError as e:
            if(type(e) == FileNotFoundError):
                os.makedirs(path)
                hdu.writeto(impath + ".fits")
                return
            error = True
            while(error is True):
                try:
                    hdu.writeto(impath + "_" + str(n) + ".fits")
                    error = False
                except OSError:
                    n += 1
            print(
                    "File of the same name already exists, file written to",
                    impath + "_" + str(n) + ".fits"
                  )

    def binImage(self, x, y=None, fn='mean'):
        """Same as the binImage method in the superclass, but optimized for
        monochrome arrays.
        """
        if x is None:
            x = 1
        if y is None:
            y = x
        if (x == 1) and (y == 1):
            return
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
                self.imdata, (x, y), np.mean, np.mean(self.imdata)
                )
        self.imdata = bindata
        self._binX *= x
        self._binY *= y

    def add_star(self, y, x, mag=None, name=None):
        print("Adding star ({},{})".format(x, y))
        self.make_current()
        if mag is not None:
            isVar = False
        else:
            isVar = True
        st = Star(self, x, y, isVar, mag=mag, name=name)
        self.stars.append(st)
        r = np.mean([s.r for s in self.stars])
        d_d = np.mean([s.d_d for s in self.stars])
        d_a = np.mean([s.d_a for s in self.stars])
        print("Added star", st)
        for s in self.stars:
            s.apertures[self] = CircularAperture((s.x[self], s.y[self]), r)
            s.annuli[self] = CircularAnnulus(
                    (s.x[self], s.y[self]), r + d_d, r + d_d + d_a
                    )
            s.r = r
            s.d_d = d_d
            s.d_a = d_a
            print("\tUpdated aperture radii of star"
                  "({},{}) to ({}, {}~{})".format(
                          np.around(s.x[self], decimals=2),
                          np.around(s.y[self], decimals=2),
                          np.around(r, decimals=2),
                          np.around(r + d_d, decimals=2),
                          np.around(r + d_d + d_a, decimals=2)
                          )
                  )

    def inherit_star(self, s, parent, shift=None, gauss=False, hh=20, hw=20):
        hasStar = False
        print("Inheriting star:", s)
        for _s in self.stars:
            if s.name == _s.name:
                s = _s
                hasStar = True
                break
        if not hasStar:
            self.stars.append(s)
        if shift is None:
            x = int(s.get_x())
            y = int(s.get_y())
            w1 = parent.imdata[y-hh:y+hh, x-hw:x+hw]
            w2 = self.imdata[y-hh:y+hh, x-hw:x+hw]
            # shift = -register_translation(w1, w2)[0]
            shift = -phase_cross_correlation(w1, w2)[0]
            print("Local offset for star", s, ":", shift)
        print(
                "(looking around({}, {}))".format(
                        int(s.get_x() + shift[1]),
                        int(s.get_y() + shift[0])
                        )
            )
        s.updateCoords(
                self, s.get_x() + shift[1], s.get_y() + shift[0], gauss=gauss
                )
        print("Inherited star:", s)

    def make_current(self):
        global CurrentFrame
        CurrentFrame = self

    def show(self):
        self.make_current()
        plt.figure(figsize=(20, 15))
        ax = plt.axes()
        ax.imshow(np.log(self.imdata), cmap='gray')
        for s in self.stars:
            s.drawAperture(self, ax)
        plt.show()


class Star:
    def __init__(
            self, parent, x, y, isVar, mag=None, r=None, d_d=None,
            d_a=None, name=None
            ):
        parent.make_current()
        cls = type(self)
        if hasattr(cls, 'n'):
            cls.n += 1
        else:
            cls.n = 1
        if name is not None:
            self.name = name
        else:
            self.name = 'Star_' + str(cls.n)
        self.mag = mag
        self.isVar = isVar
        if(self.isVar):
            self.varMag = dict()
        self.apertures = dict()
        self.annuli = dict()
        self.x = dict()
        self.y = dict()
        window = parent.imdata[y-w:y+w, x-w:x+w]
        centroid = centroid_2dg(window)
        x += centroid[0] - w
        y += centroid[1] - w
        if r is None:
            g2d_model = models.Gaussian2D()
            fitter = fitting.TRFLSQFitter()
            mgx, mgy = np.mgrid[:2*w, :2*w]
            gaussian = fitter(g2d_model, mgx, mgy, z=window)
            r = 2 * np.sqrt(gaussian.x_stddev + gaussian.y_stddev) \
                * np.sqrt(2*np.log(2))
        if d_d is None:
            d_d = r
        if d_a is None:
            d_a = r
        R = r + d_d
        self.apertures[parent] = CircularAperture([x, y], r)
        self.annuli[parent] = CircularAnnulus([x, y], R, R+d_a)
        self.r = r
        self.d_d = d_d
        self.d_a = d_a
        self.x[parent] = x
        self.y[parent] = y
        print("Created star", self, "in frame", parent)

    def get_x(self):
        return self.x[_get_current_frame()]

    def get_y(self):
        return self.y[_get_current_frame()]

    def updateCoords(self, frame, x, y, gauss=False):
        x = int(x)
        y = int(y)
        if gauss:
            try:
#                plt.figure()
#                plt.imshow(frame.imdata[y-2*w:y+2*w, x-2*w:x+2*w], cmap='gray')
#                plt.title('Gaussian fitting space')
#                plt.show()
                centroid = centroid_2dg(frame.imdata[y-w:y+w, x-w:x+w])
                x += centroid[0] - w
                y += centroid[1] - w
            except ValueError:
                print(
                        '({}, {}: [{}:{}, {}:{}]'.format(
                            self.x[frame], self.y[frame], y-w, y+w, x-w, x+w
                        )
                      )
        self.apertures[frame] = CircularAperture([x, y], self.r)
        self.annuli[frame] = CircularAnnulus(
                [x, y], self.r+self.d_d, self.r+self.d_d+self.d_a
                )
        self.x[frame] = x
        self.y[frame] = y

    def defMag(self, frame, mag):
        if not self.isVar:
            raise AttributeError('Variable magnitude can only be defined on'
                                 'variable stars')
        self.varMag[frame] = mag

    def drawAperture(self, frame, ax):
        self.apertures[frame].plot(ax, fc='g', ec='g')
        self.annuli[frame].plot(ax, fc='r', ec='r')

    # def FWHM(self, frame):
        # x = int(self.x[frame])
        # y = int(self.y[frame])
        # gaussian = fit_2dgaussian(frame.imdata[y-w:y+w, x-w:x+w])
        # r = 2 * np.sqrt(gaussian.x_stddev + gaussian.y_stddev
                        # )*(
                                # np.sqrt(2*np.log(2))
                        # )
        # return r

    def centroid(self, frame):
        x = self.x
        y = self.y
        return tuple(centroid_2dg(frame.imdata[y-w:y+w, x-w:x+w]))
        # x = int(self.x[frame])
        # y = int(self.y[frame])
        # gaussian = fit_2dgaussian(frame.imdata[y-w:y+w, x-w:x+w])
        # x += gaussian.x_mean.value - w
        # y += gaussian.y_mean.value - w
        # return x, y

    def __str__(self):
        if self.isVar:
            s = "Variable star: "
        else:
            s = "Fixed-magnitude star: "
        if hasattr(self, 'name'):
            s += self.name + '\n'
        else:
            s += "(no name)\n"
        try:
            s += "Centroid: ({}, {})\n".format(
                    int(np.around(self.get_x())),
                    int(np.around(self.get_y()))
                    )
        except KeyError:
            s += "Centroid unknown\n"
        s += "Apertures present on images:\n"
        for img in self.apertures.keys():
            s += '\t'
            s += str(img)
            s += '\n'
        # s += "Aperture radius: " + str(np.around(self.r, decimals=2)) + "\n"
        # s += "Annulus radii: {}~{}\n".format(
                # np.around(self.r+self.d_d, decimals=2),
                # np.around(self.r+self.d_d+self.d_a, decimals=2)
                # )
        return s


class _debugImage(Monochrome):
    def __init__(self, im):
        if type(im) is np.ndarray:
            self.imdata = im
            self.exptime = None
            self.jdate = None
            self._binX = None
            self._binY = None
        else:
            self.imdata = im.data
            self.exptime = im.header['EXPTIME']
            dt = im.header['DATE-OBS']
            self.jdate = Time(dt, format='isot', scale='utc').jd
            try:
                self._binX = im.header['XBINNING']
                self._binY = im.header['YBINNING']
            except KeyError:
                self._binX = None
                self._binY = None
        self.impath = None
        self.imtype = ImageType.LIGHT
        self.imcolor = Color.GREEN
        self.stars = []
