"""
"""

from photutils import aperture_photometry
from astropy.stats import sigma_clipped_stats
import numpy as np


def SNR(*imgs):
    stars = []
    for s in imgs[0].stars:
        stars.append(s)
    SNRs = []
    for img in imgs:
        _SNRs = []
        for s in stars:
            ap = s.apertures[img]
            signal = aperture_photometry(img.imdata, ap)['aperture_sum'][0]
            mean_signal = signal/ap.area
            mask = s.annuli[img].to_mask(method='center')
            bkg = mask.multiply(img.imdata)
            noise = bkg[mask.data > 0]
            std_noise = np.std(noise)
            SNR = mean_signal / std_noise * np.sqrt(ap.area)
            # ovako se dobija SNR za CCD
            # nije pouzdano da li je validno za DSLR
            _SNRs.append(SNR)
        SNRs.append(_SNRs)
    return np.array(SNRs)


def instrumental_flux(*imgs, subtract_bkg=True,
                      method='median', sigma_clip=True):
    varstars = []
    refstars = []
    fluxes = []
    for s in imgs[0].stars:
        if s.isVar:
            varstars.append(s)
        else:
            refstars.append(s)
    if sigma_clip:
        for img in imgs:
            _fluxes = []
            for s in varstars + refstars:
                ap = s.apertures[img]
                an = s.annuli[img]
                phot_data = aperture_photometry(img.imdata, ap)
                mask = an.to_mask(method='center')
                noise = mask.multiply(img.imdata)[mask.data > 0]
                bkg_mean_sc, bkg_median_sc, _ = sigma_clipped_stats(noise)
                if method == 'mean':
                    bkg = bkg_mean_sc
                elif method == 'median':
                    bkg = bkg_median_sc
                else:
                    raise ValueError(
                        "The 'method' argument must be 'mean' or 'median'"
                        )
                flux = phot_data['aperture_sum'][0]
                if subtract_bkg:
                    _fluxes.append(flux - bkg)
                else:
                    _fluxes.append(flux)
            fluxes.append(_fluxes)
        return np.array(fluxes)
    if method == 'mean':
        for img in imgs:
            _fluxes = []
            for s in varstars + refstars:
                ap = s.apertures[img]
                an = s.annuli[img]
                phot_data = aperture_photometry(img.imdata, [ap, an])
                bkg_avg = phot_data['aperture_sum_1'][0] / an.area
                bkg = bkg_avg * ap.area
                flux = phot_data['aperture_sum_0'][0]
                if subtract_bkg:
                    _fluxes.append(flux - bkg)
                else:
                    _fluxes.append(flux)
            fluxes.append(_fluxes)
        return np.array(fluxes)
    if method == 'median':
        for img in imgs:
            _fluxes = []
            for s in varstars + refstars:
                ap = s.apertures[img]
                an = s.annuli[img]
                phot_data = aperture_photometry(img.imdata, ap)
                mask = an.to_mask(method='center')
                noise = mask.multiply(img.imdata)[mask.data > 0]
                bkg = np.median(noise)
                flux = phot_data['aperture_sum'][0]
                if subtract_bkg:
                    _fluxes.append(flux - bkg)
                else:
                    _fluxes.append(flux)
            fluxes.append(_fluxes)
        return np.array(fluxes)
    raise ValueError("The 'method' argument must be 'mean' or 'median'")
