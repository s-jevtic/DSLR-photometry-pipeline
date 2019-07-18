import numpy as np
# from scipy import signal
from skimage.feature import register_translation as get_shift
# from matplotlib import pyplot as plt


def LCT(img1, img2):
    img1 = img1.astype('float')
    img1 /= img1.mean()
    # print('norm1')
    img2 = img2.astype('float')
    img2 /= img2.mean()
    # print('norm2')
#    corr = signal.correlate2d(img1, img2, mode=corrmode)
#    plt.imshow(corr)
#    plt.show()
#    maxi = np.argmax(abs(corr))
#    x, y = np.unravel_index(maxi, corr.shape)
#    y -= (len(img1)//2 - 1)
#    x -= (len(img1[0])//2 - 1)
    (y, x), _, _ = get_shift(
            img1, img2, return_error=False
            )
    return y, -x


def translate(img, dy, dx):
    res = img.shape
    transimg = (img[dy:] if dy >= 0 else img[:dy])
    transimg = (transimg[:,dx:] if dx >= 0 else transimg[:,:dx])
    if dy < 0:
        transimg = np.flip(transimg, 0)
    if dx < 0:
        transimg = np.flip(transimg, 1)
    transimg = np.append(transimg, np.zeros((dy, res[1] - dx)), axis=0)
    transimg = np.append(transimg, np.zeros((res[0], dx)), axis=1)
    if dy < 0:
        transimg = np.flip(transimg, 0)
    if dx < 0:
        transimg = np.flip(transimg, 1)
    return transimg

# cao savo sta radis *upitnik*

# sajuz nerushimny respublik svobodnih splatila naveky velikaya rus
# da zdravstvuet sozdami voley narodov edini moguchy sovyetsky sayuz
