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
    images = np.concatenate((lights, bias, dark, flat, fbias, fdark))

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
        raise ValueError("Light frames must be LIGHT image type; given:", itypes)
    itypes = {im.imtype for im in np.concatenate((bias, fbias))}
    if itypes != {ImageType.BIAS}:
        raise ValueError("Bias frames must be BIAS image type; given:", itypes)
    itypes = {im.imtype for im in flat}
    if itypes != {ImageType.FLAT}:
        raise ValueError("Flat field frames must be FLAT image type; given:", itypes)
    itypes = {im.imtype for im in np.concatenate((dark, fdark))}
    if itypes != {ImageType.DARK}:
        raise ValueError("Dark frames must be DARK image type; given:", itypes)

    bias = stack(bias, mode=masterMode) # creating master bias frame
    print("Master bias: [" + str(bias.imdata.min()) + ", " + str(bias.imdata.max()) + "]")
    
    if len(fbias) == 0:
        fbias = bias
    else:
        fbias = stack(fbias, mode=masterMode)

    for im in dark:
        print("dark: [" + str(im.imdata.min()) + ", " + str(im.imdata.max()) + "]")
        im.imdata -= bias.imdata
        print("\tdark: [" + str(im.imdata.min()) + ", " + str(im.imdata.max()) + "]")
    dark = stack(dark, mode=masterMode) # creating master dark frame
    print("Master dark: [" + str(dark.imdata.min()) + ", " + str(dark.imdata.max()) + "]")
    
    if len(fdark) > 0:
        for im in fdark:
            im.imdata -= fbias.imdata
        fdark = stack(fdark, mode=masterMode)

    for im in flat: # calibrating flat fields
        if len(fdark) > 0:
            if im.exptime != fdark.exptime:
                raise ValueError(
                        "Dark frames must have the same exposure as their "
                        "respective light frames (provided "
                        + str(fdark.exptime) + " instead of "
                        + str(im.exptime) + ")"
                        )
            im.imdata -= fdark.imdata
            im.imdata -= fbias.imdata
    flat = stack(flat, mode=masterMode)
    print("Master flat: [" + str(flat.imdata.min()) + ", " + str(flat.imdata.max()) + "]")

    for im in lights: # calibrating science frames
        if im.exptime != dark.exptime:
            raise ValueError(
                    "Dark frames must have the same exposure as their "
                    "respective light frames (provided " + str(fdark.exptime)
                    + " instead of " + str(im.exptime) + ")"
                    )
        print(str(im) + ':')
        print('0:', '[' + str(im.imdata.min()) + ',' + str(im.imdata.max()) + ']')
        im.imdata -= dark.imdata
        print('dark:', '[' + str(im.imdata.min()) + ',' + str(im.imdata.max()) + ']')
        im.imdata -= bias.imdata
        print('bias:', '[' + str(im.imdata.min()) + ',' + str(im.imdata.max()) + ']')
        nflat = flat.imdata.astype('float')/flat.imdata.mean()
        im.imdata /= flat.imdata
        #im.imdata /= nflat
        print('flat:', '[' + str(im.imdata.min()) + ',' + str(im.imdata.max()) + ']')