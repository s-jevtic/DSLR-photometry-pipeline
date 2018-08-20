import os
from fractions import Fraction
from datetime import datetime
from astropy.time import Time
from astropy.io import fits
import exifread
import numpy as np
import rawpy
from . import ImageType, Color

class DSLRImage:
    fnum=np.zeros((4,4), dtype=int)
    def __init__(
            self, impath, itype=ImageType.LIGHT, color=None
            ):
        self.impath = impath
        self.imtype = itype
        imdata, self.exptime, self.jdate = self.__parseData(impath)
        self._genPath()
        self._setData(imdata)
        del imdata
            
    def binImage(self, x, y=None, fn='mean'):
        imdata = self.getData()
        if y is None:
            y = x
        print("Binning image: " + str(self) + " (" + str(x) + "x" + str(y)+ ")")
        h = len(imdata)
        w = len(imdata[0])
        hb = h - h%y
        wb = w - w%x
        imdata_resized = imdata.copy()
        imdata_resized.resize((hb, w, 3))
        imdata_resized1 = np.empty((hb, wb, 3))
        for r in range(len(imdata_resized)):
            imdata_resized1[r] = np.resize(imdata_resized[r], (wb, 3))
        imdata_resized1 = imdata_resized1.reshape((h//x, wb, y, 3), order='A')      
        imdata_resized1 = imdata_resized1.reshape((h//y, w//x, y, x, 3), order='F')
        bindata=np.empty((h//y, w//x, 3))
        for r in range(len(bindata)):
            for c in range(len(bindata[r])):
                if fn is 'mean':
                    bindata[r][c] = np.mean(imdata_resized1[r][c])
                elif fn is 'median':
                    bindata[r][c] = np.median(imdata_resized1[r][c])
                else:
                    raise ValueError('Invalid argument for \'fn\' parameter')
        bindata = np.resize(bindata, (h//y, w//x, 1, 1, 3))
        bindata = bindata.reshape(h//y, w//x, 3)
        self._setData(bindata)
        
    def extractChannel(self, color):
        print("Extracting " + color.name + " channel from image " + str(self))
        imdata = self.getData()[:,:,color.value]
        return Monochrome(imdata, self.impath, self.imtype, color)
    
    def saveFITS(self, impath):
        impath += self.fname + ".fits"
        hdu = fits.PrimaryHDU(self.getData())
        print("Writing image " + str(self) + " to file: " + impath)
        try:
            hdu.writeto(impath)
        except OSError:
            os.remove(impath)
            hdu.writeto(impath)
            
    def getData(self):
        return np.load(self.tmpPath + self.fname + '.npy')
    
    def _setData(self, idata):
        np.save(self.tmpPath + self.fname, idata)
        
    def _genPath(self):
        cls = type(self)
        itype = self.imtype
        try:
            color = self.imcolor.value
        except(AttributeError):
            self.imcolor = None
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
        print("Initializing image class: " + str(self))
        self.tmpPath = os.path.dirname(self.impath) + '\\temp\\'
        try:
            os.makedirs(self.tmpPath)
        except(OSError):
            pass
        
    def __parseData(self, impath):
        print("Reading file: " + impath)
        with rawpy.imread(impath) as img:
            idata = img.postprocess()
            with open(impath, 'rb') as f:
                tags = exifread.process_file(f)
                exptime = float(Fraction(tags.get('EXIF ExposureTime').printable))
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
                          + ")")
        
    def __del__(self):
        print("Deleting image class: " + str(self))
        os.remove(self.tmpPath + self.fname + '.npy')
        try:
            os.rmdir(self.tmpPath)
        except OSError:
            pass

class Monochrome(DSLRImage):
    def __init__(
            self, imdata, impath, itype=ImageType.LIGHT, color=Color.GREEN 
            ):
        self.impath = impath
        self.imcolor = color
        self.imtype = itype
        self._genPath()
        self._setData(imdata)
        del imdata
        
    def binImage(self, x, y=None, fn='mean'):
        imdata = self.getData()
        if y is None:
            y = x
        print("Binning image: " + str(self) + " (" + str(x) + "x" + str(y)+ ")")
        h = len(imdata)
        w = len(imdata[0])
        hb = h - h%y
        wb = w - w%x
        imdata_resized = imdata.copy()
        imdata_resized.resize((hb, w))
        imdata_resized1 = np.empty((hb, wb))
        for r in range(len(imdata_resized)):
            imdata_resized1[r] = np.resize(imdata_resized[r], wb)
        imdata_resized1 = imdata_resized1.reshape((h//x, wb, y), order='A')      
        imdata_resized1 = imdata_resized1.reshape((h//y, w//x, y, x), order='F')
        bindata=np.empty((h//y, w//x))
        for r in range(len(bindata)):
            for c in range(len(bindata[r])):
                if fn is 'mean':
                    bindata[r][c] = np.mean(imdata_resized1[r][c])
                elif fn is 'median':
                    bindata[r][c] = np.median(imdata_resized1[r][c])
                else:
                    raise ValueError('Invalid argument for \'fn\' parameter')
        bindata = np.resize(bindata, (h//y, w//x, 1, 1))
        bindata = bindata.reshape(h//y, w//x)
        self._setData(bindata)