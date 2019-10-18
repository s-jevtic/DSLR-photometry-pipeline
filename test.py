from dslrpp.prepare.process import *
from dslrpp.tools.align import *
from dslrpp.analysis.photometry import *
from dslrpp.prepare.process import _debugImage

import numpy as np
from astropy.io import fits
from matplotlib import pyplot as plt
#from matplotlib.animation import ArtistAnimation as anim

imgs = []
# IGNORISATI OVAJ BLOK
#for n in range(128, 199):
#    try:
#        imgs.append(
#                _debugImage(
#                        fits.open(
#                                "E:/ltbu/!AST/projekat #1 - DSLR/100CANON/bin/"
#                                "split/G/IMG_7{}-G.fit".format(n))[0].data
#                                )
#                        )
for n in range(1, 37):
    try:
        imgs.append(
                _debugImage(
                        fits.open(
                                "E:/ltbu/!AST/projekat #1 - DSLR/stackg/"
                                "Group{}.fit".format(n)
                                )[0]
                        )
                    )
    except FileNotFoundError:
        pass
imgs[0].add_star(683, 784, name='V2455 Cyg')
imgs[0].add_star(511, 999, mag=8.86, name='HD 204569')
imgs[0].add_star(697, 792, mag=9.54, name='BD+46 3328')
imgs[0].add_star(398, 609, mag=8.76, name='HD 204341')

N_IMGS = len(imgs)
N_STARS = len(imgs[0].stars)
# IGNORISATI OVAJ BLOK
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
print(get_offsets(*imgs, global_offset=False, gauss=True))
snrs = SNR(*imgs)
fluxes = instrumental_flux(*imgs)
# IGNORISATI OVAJ BLOK
#FWHMs = np.array(
#        [(img.stars[0].FWHM(img), img.stars[1].FWHM(img)) for img in imgs]
#        )
#v = imgs[0].stars[0]
#r = imgs[0].stars[1]
#xpos = [v.x[img] for img in imgs]
#ypos = [v.y[img] for img in imgs]
#r_xpos = [r.x[img] for img in imgs]
#r_ypos = [r.y[img] for img in imgs]
#xc, yc = np.transpose([img.stars[0].centroid(img) for img in imgs])
#plt.figure()
#plt.imshow(2.5 * np.log10(imgs[0].imdata), cmap='gray')
#plt.plot(xpos, ypos, label='V2455 Cyg')
#plt.plot(r_xpos, r_ypos, label='HD 204569')
#plt.title('Positions')
#plt.axis('equal')
#plt.legend()
#plt.figure()
#plt.plot(ypos, label='Aperture position, LCT')
#plt.title('Y')
#plt.legend()
#for i in range(42, 69):
#    imgs[i].show()
#lum = [np.median(img.imdata) for img in imgs]
#plt.plot(lum)
#input()
#plt.figure()
#plt.title('SNR')
#plt.plot(snrs[:, 0], label='LCT var')
#plt.plot(snrs[:, 1], label='LCT ref')
#plt.legend()
#plt.figure()
#plt.title('Flux')
#plt.plot(fluxes[:, 0], label='LCT var')
#plt.plot(fluxes[:, 1], label='LCT ref')
#plt.legend()
#plt.figure()
#plt.title('FWHM')
#plt.plot(FWHMs[:, 0], label='LCT var')
#plt.plot(FWHMs[:, 1], label='LCT ref')
#plt.legend()
mags = -2.5 * np.log10(fluxes)  # pretvaramo fluks u magnitudu
_, magv, dmag = np.loadtxt(
        "../merenja.txt", delimiter=',', unpack=True
        )[:, :N_IMGS - 1]  # merenja iz MaxIm DL, -1 zbog onog snimka koji fali
print(magv)
magv = np.insert(magv, 12, np.nan)
print(magv)
dmag = np.insert(dmag, 12, np.nan)
ideal_lc = mags[:, 1:].mean(axis=1)  # usrednjavamo krive sjaja ref zvezda
for m in mags.T:
    m -= ideal_lc  # tu krivu oduzimamo od svih
ref_mag = np.mean([s.mag for s in imgs[0].stars[1:]])
mags += ref_mag  # dodamo im srednju vrednost "kataloskih" magnituda
f = plt.figure()
errors = np.array([1.0857/np.sqrt(snrs[:, i]) for i in range(N_STARS)])
times = [i.jdate for i in imgs]
times -= np.min(times)
# prema literaturi
#error_u = -2.5 * np.log10(fluxes[:, 0] + error) - mags[:, 0]
#error_l = -2.5 * np.log10(fluxes[:, 0] - error) - mags[:, 0]
plt.title('Fotometrija')
plt.errorbar(times, magv, yerr=dmag, label='MaxIm DL', capsize=2)
for i in range(1, N_STARS):
    plt.errorbar(
            times, mags[:, i], yerr=errors[i],
            label=imgs[0].stars[i].name, capsize=2
            )
plt.errorbar(
        times, mags[:, 0], yerr=errors[0], label=imgs[0].stars[0].name,
        capsize=2
        )
plt.legend()
plt.show()
