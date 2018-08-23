"""
"""
import numpy as np
from ..tools.stack import stack
from .process import ImageType, Monochrome

def calibrate(
        lights, bias, dark, flat, fbias=None, fdark=None, masterMode='median'
        ):
    """Calibrates (reduces) the light frames by subtracting bias and dark
    frames from light frames and flat fields, then dividing the calibrated
    light frames by the master flat field.

    If calibration frames for flat
    fields are not provided, calibration frames for light frames will be used.
    """
    images = np.concatenate(lights, bias, dark, flat, fbias, fdark)

    dtypes = {type(im) for im in images}
    if dtypes != {Monochrome}:
        raise TypeError("The arguments must contain only Monochrome types")

    cols = {im.imcolor for im in images}
    if(len(cols) > 1):
        raise ValueError("Frames must be the same color")

    del images

    itypes = {im.imtype for im in lights}
    if itypes != {ImageType.LIGHT}:
        raise ValueError("Light frames must be LIGHT image type")
    itypes = {im.imtype for im in bias + fbias}
    if itypes != {ImageType.BIAS}:
        raise ValueError("Bias frames must be BIAS image type")
    itypes = {im.imtype for im in flat}
    if itypes != {ImageType.FLAT}:
        raise ValueError("Flat field frames must be FLAT image type")
    itypes = {im.imtype for im in dark + fdark}
    if itypes != {ImageType.DARK}:
        raise ValueError("Dark frames must be DARK image type")

    bias = stack(bias, mode=masterMode)
    dark = stack(dark, mode=masterMode)
    flat = stack(flat, mode=masterMode) # creating master frames
    if fbias is None:
        fbias = stack(bias, mode=masterMode)
    else:
        fbias = stack(fbias, mode=masterMode)
    if fdark is None:
        fdark = stack(dark, mode=masterMode)
    else:
        fdark = stack(fdark, mode=masterMode)

    for im in flat: # calibrating flat fields
        im.imdata -= fbias
        im.imdata -= fdark
    flat = stack(flat, mode=masterMode)

    for im in lights: # calibrating light/science frames
        im.imdata -= bias
        im.imdata -= dark
        im.imdata /= flat