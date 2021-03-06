"""A submodule used for aligning several images according to the position of
stars (or other celestial objects).
"""
import numpy as np
from skimage.feature import register_translation
from ..prepare import Monochrome
from matplotlib import pyplot as plt

__all__ = ["get_offsets"]


def __window(imd, center, hh, hw):
    """Auxiliary function for slicing the array into a window.

    If the window is too large for the image, it will be downsized.

    Parameters
    ----------
    imd : `numpy.ndarray`
        The image array to be sliced.
    center : tuple of `int`\0s
        The center of the window in a (y, x) format
    hh : `int`
        The half-height of the window
    hw : `int`
        The half-width of the window

    Returns
    -------
    window : `numpy.ndarray`
        The sliced array.
    """
    H = len(imd)
    W = len(imd[0])

    if center[0] - hh < 0:
        y1 = 0
    else:
        y1 = int(center[0]) - hh
    if center[0] + hh > H:
        y2 = H
    else:
        y2 = int(center[0]) + hh

    if int(center[1]) - hw < 0:
        x1 = 0
    else:
        x1 = int(center[1]) - hw

    if int(center[1]) + hw > W:
        x2 = W
    else:
        x2 = int(center[1]) + hw
    return imd[y1:y2, x1:x2]


def __get_shift(img1, img2, hh=20, hw=20):
    """Auxiliary function; computes the offset between two images.

    Takes the positions of stars, does a FFT-based cross-correlation on the
    windows around the specified positions and calculates the pixel offset in a
    (y, x) format.

    Parameters
    ----------
    img1 : `Monochrome`
        The reference image.
    img2 : `Monochrome`
        The image used to compute the offset
    hh : `int`, optional
        The half-height of the windows
    hw : `int`, optional
        The half-width of the windows

    Returns
    -------
    y : `int`
        The height component of the offset
    x : `int`
        The width component of the offset
    """
    imd1 = img1.imdata / img1.imdata.mean()
    imd2 = img2.imdata / img2.imdata.mean()
    offsets = []
    for s in img1.stars:
        if s.isVar:
            pass
        w1 = __window(imd1, (s.y[img1], s.x[img1]), hh, hw)
        w2 = __window(imd2, (s.y[img1], s.x[img1]), hh, hw)
        offset = register_translation(w1, w2)[0]
        offsets.append(offset)
        if np.abs(offset[0]*offset[1]) > 100:
            fig, (a1, a2) = plt.subplots(ncols=2)
            plt.title(str(offsets[0]))
            a1.imshow(w1, cmap='gray')
            plt.title(str(offsets[3]))
            a2.imshow(w2, cmap='gray')
            a1.plot()
            plt.show()
            input()
        else:
            print(str(np.abs(offset[0]*offset[1])), "<", "100")
            input()
#        print("{}:{}".format(s.x[img1] - hw, s.x[img1] + hw))
    print(offsets)
    y, x = np.median(offsets, axis=0)
    return -int(y), -int(x)


def __translate(imd, dy, dx):
    """Auxiliary function; translates the specified image by a specified vector
    .

    Takes the height and width components of the offset, and translates
    the image accordingly. The leftover space will be filled with zeros.

    Parameters
    ----------
    img1 : `numpy.ndarray`
        The image array to be translated
    dy : `int`
        The height component of the translation vector
    dx : `int`
        The width component of the translation vector

    Returns
    -------
    transimg : `numpy.ndarray`
        The translated image
    """
    res = imd.shape
    transimd = (imd[dy:] if dy >= 0 else imd[:dy])
    transimd = (transimd[:, dx:] if dx >= 0 else transimd[:, :dx])
    if dy < 0:
        transimd = np.flip(transimd, 0)
    if dx < 0:
        transimd = np.flip(transimd, 1)
    transimd = np.append(
            transimd,
            np.zeros((np.abs(dy), np.abs(res[1] - np.abs(dx)))),
            axis=0
            )
    transimd = np.append(
            transimd,
            np.zeros((np.abs(res[0]), np.abs(dx))),
            axis=1
            )
    if dy < 0:
        transimd = np.flip(transimd, 0)
    if dx < 0:
        transimd = np.flip(transimd, 1)
    return transimd


def get_offsets(*imgs, hh=20, hw=20, gauss=False, global_offset=False):
    """Computes the offset between images based on star positions.

    Computes the offset between images based on star positions, using
    cross-correlation.

    Parameters
    ----------
    *imgs : `numpy.ndarray`\0s
        The images whose offsets need to be found. The first image in the
        sequence will have the offset (0,0) by default.

    Returns
    -------
    aligned : `numpy.ndarray`
        The array of tuples representing the offset in a (y, x) format.
    """
    offsets = np.array([[0, 0]])
    for i in range(1, len(imgs)):
        # y, x = __get_shift(imgs[i-1], imgs[i], hh, hw)
        y, x = -register_translation(imgs[i-1].imdata, imgs[i].imdata)[0]
        for s in imgs[i-1].stars:
            if global_offset:
                imgs[i].inherit_star(
                        s, imgs[i-1], shift=[y, x], gauss=gauss,
                        hh=int(hh//2), hw=int(hw//2)
                        )
            else:
                imgs[i].inherit_star(
                        s, imgs[i-1], gauss=gauss,
                        hh=int(hh//2), hw=int(hw//2)
                        )
        imgs[i].make_current()
        offsets = np.concatenate((offsets, [[y, x]]), axis=0)
        print('diff offset:', offsets[i], '/', offsets[i-1])
        offsets[i] += offsets[i-1]
        print('full offset:', offsets[i], '/', offsets[i-1])
        print("{}/{}".format(i, len(imgs) - 1))
    return offsets


def align_imgs(*imgs, hh=20, hw=20):
    """Translates the images in order for star coordinates to match.

    Computes the offset between images based on star positions, and translates
    the images accordingly. The leftover space will be filled with zeros.

    Parameters
    ----------
    *imgs : `numpy.ndarray`\0s
        The images to be aligned. The first image in the sequence will be used
        as the reference image and will not be translated.

    Returns
    -------
    aligned : `numpy.ndarray`
        The array of translated/aligned images
    """
    im0 = imgs[0]
    aligned = [im0]
    offs = get_offsets(*imgs)
    print(offs)
    for i in range(1, len(imgs)):
        (y, x) = offs[i]
        print(type(y), x)
        new_imd = __translate(imgs[i].imdata, y, x)
        new_img = Monochrome(new_imd, imgs[i], translated=True)
        aligned.append(new_img)
    return aligned
