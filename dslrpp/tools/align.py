import numpy as np
from scipy import signal

def LCT(img1, img2, corrmode='same'):
    img1 = img1.astype('float')
    img1 /= img1.max()
    print('norm1')
    img2 = img2.astype('float')
    img2 /= img2.max()
    print('norm2')
    corr=signal.correlate2d(img1,img2, mode=corrmode)
    maxi=np.argmax(abs(corr))
    x, y = np.unravel_index(maxi, corr.shape)
    y -= (len(img1)//2 - 1)
    x -= (len(img1[0])//2 - 1)
    return x, y