"""This submodule serves the purpose of preparing the frames
for further processing.
"""
import os
from .process import DSLRImage, Color, ImageType, isRaw
from .calibrate import calibrate
import numpy as np

__all__ = ["sort"]


def __listdir(path):
    # optimizes the os.listdir function
    return [
            path + '/' + d for d in os.listdir(path)
            if os.path.isfile(path + '/' + d)
            ]


def __listraw(path):
    return [f for f in __listdir(path) if isRaw(f)]


def sort(path, red=False, green=True, blue=False, binX=None, binY=None):
    """Initializes DSLRImage classes for each frame,
    then bins them and stores specified monochrome images to FITS.
    """
    if binY is None:
        binY = binX

    lights = [
            DSLRImage(f, itype=ImageType.LIGHT)
            for f in __listraw(path + "/Light_frames")
            ]
    bias = [
            DSLRImage(f, itype=ImageType.BIAS)
            for f in __listraw(path + "/Bias_frames")
            ]
    darks = [
            DSLRImage(f, itype=ImageType.DARK)
            for f in __listraw(path + "/Dark_frames")
            ]
    flats = [
            DSLRImage(f, itype=ImageType.FLAT)
            for f in __listraw(path + "/Flat_fields")
            ]

    imagesR = np.empty(())
    imagesG = np.empty(())
    imagesB = np.empty(())

    if(red):
        clights = np.array([im.extractChannel(Color.RED) for im in lights])
        cbias = np.array([im.extractChannel(Color.RED) for im in bias])
        cflats = np.array([im.extractChannel(Color.RED) for im in flats])
        cdarks = np.array([im.extractChannel(Color.RED) for im in darks])
        calibrate(clights, cbias, cdarks, cflats)
        imagesR = clights
    if(green):
        clights = np.array([im.extractChannel(Color.GREEN) for im in lights])
        cbias = np.array([im.extractChannel(Color.GREEN) for im in bias])
        cflats = np.array([im.extractChannel(Color.GREEN) for im in flats])
        cdarks = np.array([im.extractChannel(Color.GREEN) for im in darks])
        calibrate(clights, cbias, cdarks, cflats)
        imagesG = clights
    if(blue):
        clights = np.array([im.extractChannel(Color.BLUE) for im in lights])
        cbias = np.array([im.extractChannel(Color.BLUE) for im in bias])
        cflats = np.array([im.extractChannel(Color.BLUE) for im in flats])
        cdarks = np.array([im.extractChannel(Color.BLUE) for im in darks])
        calibrate(clights, cbias, cdarks, cflats)
        imagesB = clights

    for im in np.concatenate((imagesR, imagesG, imagesB)):
        im.binImage(binX, binY)

    return (imagesR, imagesG, imagesB)
