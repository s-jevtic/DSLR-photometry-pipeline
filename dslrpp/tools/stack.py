"""A submodule for combining several frames into one
"""
import numpy as np
from ..prepare import Monochrome


def stack(images, mode='median'):
    """Stacks the data from several images using specified function
    (default is median). Raises exception if frames are not monochrome or
    if their types and colors don't match.
    """
    print("Stacking images:")
    for im in images:
        print('\t' + str(type(im)) + ':', str(im))
    dtypes = {type(im) for im in images}
    if dtypes != {Monochrome}:
        raise TypeError(
                "The arguments must contain only Monochrome types (provided: "
                + str(dtypes) + ")"
                )
    cols = {im.imcolor for im in images}
    if(len(cols) > 1):
        raise ValueError("Frames must be the same color")
    itypes = {im.imtype for im in images}
    if(len(itypes) > 1):
        raise ValueError("Frames must be the same image type")

    imdata = np.array([im.imdata for im in images])

    if mode is 'median':
        stack = np.median(imdata, axis=0)
    elif mode is 'mean':
        stack = np.mean(imdata, axis=0)
    else:
        raise ValueError("Invalid argument for 'mode' parameter")

    return Monochrome(
            stack.astype('uint16'), images[0], images[0].imcolor,
            stacked=True
            )
