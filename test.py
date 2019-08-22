from dslrpp.prepare.process import *
from dslrpp.tools.align import *
from dslrpp.analysis.photometry import *
from dslrpp.prepare.process import _debugImage

import numpy as np
from astropy.io import fits
from matplotlib import pyplot as plt

imgs = []
for n in range(128, 199):
    try:
        imgs.append(
                _debugImage(
                        fits.open(
                                "E:/ltbu/!AST/projekat #1 - DSLR/100CANON/bin/"
                                "split/G/IMG_7{}-G.fit".format(n))[0].data
                                )
                        )
    except FileNotFoundError:
        pass
imgs[0].add_star(683, 784)
imgs[0].add_star(511, 999, mag=np.nan)
#s_imgs = []
#for n in range(1, 25):
#    s_imgs.append(
#            _debugImage(
#                    fits.open(
#                            "E:/ltbu/!AST/projekat #1 - DSLR/stackg/"
#                            "Group{}.fit".format(n))[0].data
#                            )
#                    )
#s_imgs[0].add_star(683, 784)
#s_imgs[0].add_star(511, 999, mag=np.nan)
print(get_offsets(*imgs))
snrs = SNR(*imgs)
fluxes = instrumental_flux(*imgs)
#v = imgs[0].stars[0]
#r = imgs[0].stars[1]
#xpos = [(v.x[img], v.apertures[img].positions[0]) for img in imgs]
#plt.plot(xpos)
#plt.figure()
#ypos = [(v.y[img], v.apertures[img].positions[1]) for img in imgs]
#plt.plot(ypos)
#for i in range(42, 69):
#    imgs[i].show()
#lum = [np.median(img.imdata) for img in imgs]
#plt.plot(lum)
#input()
plt.figure()
plt.title('SNR')
plt.plot(snrs)
plt.figure()
plt.title('Flux')
plt.plot(fluxes)
plt.figure()
plt.title('FWHM')
FWHMs = [(img.stars[0].FWHM(img), img.stars[1].FWHM(img)) for img in imgs]
plt.plot(FWHMs)
plt.show()
