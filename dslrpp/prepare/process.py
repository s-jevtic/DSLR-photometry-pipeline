import numpy as np
from . import ImageType, Color

def splitChannels(rgb):
    r = rgb[:,:,0]
    g = rgb[:,:,1]
    b = rgb[:,:,2]
    return r, g, b

class DSLRImage:
    imdata=np.empty((0,0))
    imtype=ImageType.LIGHT
    imcolor=Color.GREEN
    def __init__(
            self, idata, itype=ImageType.LIGHT, color=Color.GREEN,
            binX=None, binY=None
            ):
        self.imdata = idata
        self.imtype = itype
        self.imcolor = color
        print(self.imdata.dtype.name)
        print("initializing image class: " + str(self))
        
        if(binX is not None):
            self.binImage(binX, binY)
            
    def binImage(self, x, y=None):
        if y is None:
            y = x
        print("binning image: " + str(self) + " (" + str(x) + "x" + str(y)+ ")")
        h = len(self.imdata)
        w = len(self.imdata[0])
        hb = h - h%y
        wb = w - w%x
        imdata_resized = self.imdata.copy()
        imdata_resized.resize((hb, w))
        imdata_resized1 = np.empty((hb, wb))
        for r in range(len(imdata_resized)):
            imdata_resized1[r] = np.resize(imdata_resized[r], wb)
        imdata_resized1 = imdata_resized1.reshape((h//x, wb, y), order='A')      
        imdata_resized1 = imdata_resized1.reshape((h//y, w//x, y, x), order='F')
        bindata=np.empty((h//y, w//x))
        for r in range(len(bindata)):
            for c in range(len(bindata[r])):
                bindata[r][c] = np.mean(imdata_resized1[r][c])
        bindata = np.resize(bindata, (h//y, w//x, 1, 1))
        bindata = bindata.reshape(h//y, w//x)
        self.imdata = bindata
    def __str__(self):
        return("DSLRImage(imtype=" + str(self.imtype)
                          + ", color=" + str(self.imcolor)
                          + ")"
                          )