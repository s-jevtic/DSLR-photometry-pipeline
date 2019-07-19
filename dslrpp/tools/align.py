import numpy as np
from skimage.feature import register_translation


def __get_shift(img1, img2):
    img1 = img1.astype('float')
    img1 /= img1.mean()
    img2 = img2.astype('float')
    img2 /= img2.mean()
    (y, x), _, _ = register_translation(img1, img2)
    return -y, -x


def __translate(img, dy, dx):
    res = img.shape
    transimg = (img[dy:] if dy >= 0 else img[:dy])
    transimg = (transimg[:, dx:] if dx >= 0 else transimg[:, :dx])
    if dy < 0:
        transimg = np.flip(transimg, 0)
    if dx < 0:
        transimg = np.flip(transimg, 1)
    transimg = np.append(
            transimg,
            np.zeros((np.abs(dy), np.abs(res[1] - np.abs(dx)))),
            axis=0
            )
    transimg = np.append(
            transimg,
            np.zeros((np.abs(res[0]), np.abs(dx))),
            axis=1
            )
    if dy < 0:
        transimg = np.flip(transimg, 0)
    if dx < 0:
        transimg = np.flip(transimg, 1)
    return transimg


def get_offsets(*imgs):
    im0 = imgs[0]
    offsets = np.array([[0,0]])
    for i in imgs:
        y, x = __get_shift(im0, i)
        np.append(offsets, [y, x])
    return offsets


def align_imgs(*imgs):
    im0 = imgs[0]
    aligned = np.array([im0])
    for i in imgs:
        y, x = __get_shift(im0, i)
        np.append(aligned, __translate(i, y, x))
    return aligned


# cao savo sta radis *upitnik*

# sajuz nerushimny respublik svobodnih splatila naveky velikaya rus
# da zdravstvuet sozdami voley narodov edini moguchy sovyetsky sayuz
