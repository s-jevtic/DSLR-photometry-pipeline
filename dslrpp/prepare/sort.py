import os
from astropy.io import fits
from . import ImageType, Color
from .process import splitChannels, DSLRImage
import rawpy

def readRaw(impath):
    print("Reading file: " + impath)
    with rawpy.imread(impath) as img:
        return img.postprocess()

def saveFITS(im, impath):
    impath += im.fname + ".fits"
    hdu = fits.PrimaryHDU(im.imdata)
    print("Writing image " + str(im) + " to file: " + impath)
    try:
        hdu.writeto(impath)
    except OSError:
        os.remove(impath)
        hdu.writeto(impath)

def _listdir(path):
    return [path + '\\' + d for d in os.listdir(path)]

def _makedirs(path):
    try:
        os.makedirs(path)
    except FileExistsError:
        pass

def _sort(path, red=False, green=True, blue=False, binX=None, binY=None):
    lights = [readRaw(f) for f in _listdir(path + "\\Light_frames")]
    lR, lG, lB = (
            [splitChannels(im)[0] for im in lights],
            [splitChannels(im)[1] for im in lights],
            [splitChannels(im)[2] for im in lights]
            )
    _lR = [DSLRImage(im, ImageType.LIGHT, Color.RED, binX, binY) for im in lR]
    _lG = [DSLRImage(im, ImageType.LIGHT, Color.GREEN, binX, binY) for im in lG]
    _lB = [DSLRImage(im, ImageType.LIGHT, Color.BLUE, binX, binY) for im in lB]
    
    bias = [readRaw(f) for f in _listdir(path + "\\Bias_frames")]
    bR, bG, bB = (
            [splitChannels(im)[0] for im in bias],
            [splitChannels(im)[1] for im in bias],
            [splitChannels(im)[2] for im in bias]
            )
    _bR = [DSLRImage(im, ImageType.BIAS, Color.RED, binX, binY) for im in bR]
    _bG = [DSLRImage(im, ImageType.BIAS, Color.GREEN, binX, binY) for im in bG]
    _bB = [DSLRImage(im, ImageType.BIAS, Color.BLUE, binX, binY) for im in bB]
    
    darks = [readRaw(f) for f in _listdir(path + "\\Dark_frames")]
    dR, dG, dB = (
            [splitChannels(im)[0] for im in darks],
            [splitChannels(im)[1] for im in darks],
            [splitChannels(im)[2] for im in darks]
            )
    _dR = [DSLRImage(im, ImageType.DARK, Color.RED, binX, binY) for im in dR]
    _dG = [DSLRImage(im, ImageType.DARK, Color.GREEN, binX, binY) for im in dG]
    _dB = [DSLRImage(im, ImageType.DARK, Color.BLUE, binX, binY) for im in dB]
    
    flats = [readRaw(f) for f in _listdir(path + "\\Flat_fields")]
    fR, fG, fB = (
            [splitChannels(im)[0] for im in flats],
            [splitChannels(im)[1] for im in flats],
            [splitChannels(im)[2] for im in flats]
            )
    _fR = [DSLRImage(im, ImageType.FLAT, Color.RED, binX, binY) for im in fR]
    _fG = [DSLRImage(im, ImageType.FLAT, Color.GREEN, binX, binY) for im in fG]
    _fB = [DSLRImage(im, ImageType.FLAT, Color.BLUE, binX, binY) for im in fB]
    
    if(red):
        _makedirs(path + "\\processedR\\Light_frames")
        _makedirs(path + "\\processedR\\Bias_frames")
        _makedirs(path + "\\processedR\\Dark_frames")
        _makedirs(path + "\\processedR\\Flat_fields")
        
        for im in _lR:
            saveFITS(im, path + "\\processedR\\Light_frames\\")
        for im in _bR:
            saveFITS(im, path + "\\processedR\\Bias_frames\\")
        for im in _dR:
            saveFITS(im, path + "\\processedR\\Dark_frames\\")
        for im in _fR:
            saveFITS(im, path + "\\processedR\\Flat_fields\\")
    if(green):
        _makedirs(path + "\\processedG\\Light_frames")
        _makedirs(path + "\\processedG\\Bias_frames")
        _makedirs(path + "\\processedG\\Dark_frames")
        _makedirs(path + "\\processedG\\Flat_fields")
        
        for im in _lG:
            saveFITS(im, path + "\\processedG\\Light_frames\\")
        for im in _bG:
            saveFITS(im, path + "\\processedG\\Bias_frames\\")
        for im in _dG:
            saveFITS(im, path + "\\processedG\\Dark_frames\\")
        for im in _fG:
            saveFITS(im, path + "\\processedG\\Flat_fields\\")
    if(blue):
        _makedirs(path + "\\processedB\\Light_frames")
        _makedirs(path + "\\processedB\\Bias_frames")
        _makedirs(path + "\\processedB\\Dark_frames")
        _makedirs(path + "\\processedB\\Flat_fields")
        
        for im in _lB:
            saveFITS(im, path + "\\processedB\\Light_frames\\")
        for im in _bB:
            saveFITS(im, path + "\\processedB\\Bias_frames\\")
        for im in _dB:
            saveFITS(im, path + "\\processedB\\Dark_frames\\")
        for im in _fB:
            saveFITS(im, path + "\processedB\\Flat_fields\\")
