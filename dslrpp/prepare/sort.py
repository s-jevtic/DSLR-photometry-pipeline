"""This submodule serves the purpose of preparing the frames
for further processing.
"""
import os
from .process import DSLRImage, Color, ImageType

def __listdir(path):
    # optimizes the os.listdir function
    return [
            path + '\\' + d for d in os.listdir(path)
            if os.path.isfile(path + '\\' + d)
            ]

def __makedirs(path):
    # optimizes the os.makedirs function
    try:
        os.makedirs(path)
    except FileExistsError:
        pass

def sort(path, red=False, green=True, blue=False, binX=None, binY=None):
    """Initializes DSLRImage classes for each frame,
    then bins them and stores specified monochrome images to FITS.
    """
    lights = [
            DSLRImage(f, itype = ImageType.LIGHT)
            for f in __listdir(path + "\\Light_frames")
            ]
    bias = [
            DSLRImage(f, itype = ImageType.BIAS)
            for f in __listdir(path + "\\Bias_frames")
            ]
    darks = [
            DSLRImage(f, itype = ImageType.DARK)
            for f in __listdir(path + "\\Dark_frames")
            ]
    flats = [
            DSLRImage(f, itype = ImageType.FLAT) 
            for f in __listdir(path + "\\Flat_fields")
            ]
    
    images = lights + bias + darks + flats
    
    for im in images:
        im.binImage(binX, binY)
        
    if(red):
        __makedirs(path + "\\processedR\\Light_frames")
        __makedirs(path + "\\processedR\\Bias_frames")
        __makedirs(path + "\\processedR\\Dark_frames")
        __makedirs(path + "\\processedR\\Flat_fields")
        
        imM = [im.extractChannel(Color.RED) for im in images]
        
        for im in imM:
            fdir = {
                    0:"Light_frames", 1:"Bias_frames", 2:"Dark_frames",
                    3:"Flat_fields"
                    }[im.imtype.value]
            im.saveFITS(path + "\\processedR\\" + fdir + "\\")
            
    if(green):
        __makedirs(path + "\\processedG\\Light_frames")
        __makedirs(path + "\\processedG\\Bias_frames")
        __makedirs(path + "\\processedG\\Dark_frames")
        __makedirs(path + "\\processedG\\Flat_fields")
        
        imM = [im.extractChannel(Color.GREEN) for im in images]
        
        for im in imM:
            fdir = {
                    0:"Light_frames", 1:"Bias_frames", 2:"Dark_frames",
                    3:"Flat_fields"
                    }[im.imtype.value]
            im.saveFITS(path + "\\processedG\\" + fdir + "\\")
            
    if(blue):
        __makedirs(path + "\\processedB\\Light_frames")
        __makedirs(path + "\\processedB\\Bias_frames")
        __makedirs(path + "\\processedB\\Dark_frames")
        __makedirs(path + "\\processedB\\Flat_fields")
        
        imM = [im.extractChannel(Color.BLUE) for im in images]
        
        for im in imM:
            fdir = {
                    0:"Light_frames", 1:"Bias_frames", 2:"Dark_frames",
                    3:"Flat_fields"
                    }[im.imtype.value]
            im.saveFITS(path + "\\processedB\\" + fdir + "\\")
