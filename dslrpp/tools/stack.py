"""A submodule for combining several frames into one
"""
import numpy as np
from ..prepare import Monochrome

def stack(images, mode='median'):
    """Stacks the data from several images using specified function
    (default is median). Raises exception if frames are not monochrome or
    if their types and colors don't match.
    """
    dtypes = {type(im) for im in images}
    if dtypes is not {Monochrome}:
        raise TypeError("The argument must contain only Monochrome type")
    cols = {im.imcolor for im in images}
    if(len(cols) > 1):
        raise ValueError("Frames must be the same color")
        itypes = {im.imtype for im in images}
    if(len(itypes) > 1):
        raise ValueError("Frames must be the same image type")
    
    imdata = np.array([im._getData() for im in images])
    
    if mode is 'median':
        stack = np.median(imdata, axis=0)
    elif mode is 'mean':
        stack = np.mean(imdata, axis=0)
    else:
        raise ValueError("Invalid argument for 'mode' parameter")
        
    return Monochrome(
            stack, images[0].impath, images[0].imtype, images[0].imcolor,
            stacked=True
            )