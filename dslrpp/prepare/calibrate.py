"""
"""
import numpy as np
from ..tools.stack import stack
from .process import ImageType, Monochrome

def calibrate(
        lights, bias, dark, flat, fbias=[], fdark=[], masterMode='median'
        ):
    """Calibrates (reduces) the light frames by subtracting bias and dark
    frames from light frames and flat fields, then dividing the calibrated
    light frames by the master flat field.

    If calibration frames for flat
    fields are not provided, calibration frames for light frames will be used.
    """
    images = (
            im for im in np.concatenate(
                    (lights, bias, dark, flat, fbias, fdark)
                    )
    )

    dtypes = {type(im) for im in images}
    if dtypes != {Monochrome}:
        raise TypeError(
                "The arguments must contain only Monochrome types (provided: "
                + str(dtypes) + ")"
                )

    cols = {im.imcolor for im in images}
    if(len(cols) > 1):
        raise ValueError("Frames must be the same color")

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
    dark = stack(dark, mode=masterMode) # creating master frames
#    if fbias == []:
#        fbias = bias
#    else:
#        print("fbias:", fbias)
#        fbias = stack(fbias, mode=masterMode)
#    if fdark == []:
#        fdark = dark
#    else:
#        print("fdark", fdark)
#        fdark = stack(fdark, mode=masterMode)

    for im in flat: # calibrating flat fields
        if fdark != []:
            if im.exptime != fdark.exptime:
                raise ValueError(
                        "Dark frames must have the same exposure as their "
                        "respective light frames (provided "
                        + str(fdark.exptime) + " instead of "
                        + str(im.exptime) + ")"
                        )
            im.imdata = np.subtract(im.imdata, fdark.imdata)
        if fbias != []:
            im.imdata = np.subtract(im.imdata, fbias.imdata)
    flat = stack(flat, mode=masterMode)

    for im in lights: # calibrating science frames
        if im.exptime != dark.exptime:
            raise ValueError(
                    "Dark frames must have the same exposure as their "
                    "respective light frames (provided " + str(fdark.exptime)
                    + " instead of " + str(im.exptime) + ")"
                    )
        print(im.imdata, '-\n', dark.imdata)
        im.imdata = np.subtract(im.imdata, dark.imdata)
        print(im.imdata, '-\n', bias.imdata)
        im.imdata = np.subtract(im.imdata, bias.imdata)
        print(im.imdata, '/\n', flat.imdata)
        im.imdata = np.true_divide(im.imdata, flat.imdata)