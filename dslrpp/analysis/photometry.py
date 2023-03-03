"""
"""

from photutils import aperture_photometry
from astropy.stats import sigma_clipped_stats
import numpy as np
from matplotlib import pyplot as plt

__all__ = ["SNR", "instrumental_flux", "lightcurve", "save_lcData"]


def SNR(*imgs):
    stars = []
    for s in imgs[0].stars:
        stars.append(s)
    SNRs = []
    for img in imgs:
        _SNRs = []
        for s in stars:
            print(s, img)
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


def lightcurve(
        *imgs, return_error=True, include_refstars=False,
        plot=True, jd_time=True
               ):
    n_stars = len(imgs[0].stars)
    if return_error:
        snrs = SNR(*imgs)
    fluxes = instrumental_flux(*imgs)
    mags = -2.5 * np.log10(fluxes)
    ideal_lc = mags[:, 1:].mean(axis=1)  # usrednjavamo krive sjaja ref zvezda
    for m in mags.T:
        m -= ideal_lc  # tu krivu oduzimamo od svih
    ref_mag = np.mean([s.mag for s in imgs[0].stars[1:]])
    mags += ref_mag
    if return_error:
        errors = np.array([1.0857/np.sqrt(snrs[:, i]) for i in range(n_stars)])
    times = np.array([img.jdate for img in imgs])
    if not jd_time:
        times -= times.min()
    plt.figure()
    plt.title('Photometry')
    plt.xlabel('mag')
    plt.ylabel('t')
    if include_refstars:
        for i in range(1, n_stars):
            plt.errorbar(
                    times, mags[:, i], yerr=errors[i],
                    label=imgs[0].stars[i].name, capsize=2
                    )
    plt.errorbar(
        times, mags[:, 0], yerr=errors[0], label=imgs[0].stars[0].name,
        capsize=2
        )
    if return_error:
        if include_refstars:
            return times, mags.T, errors
        return times, mags[:, 0], errors[0]
    return times, mags[:, 0]


def save_lcData(path, t, m, e=None, desc="\b"):
    print("Saving lightcurve data...")
    n = 1
    if e is not None:
        data = np.transpose([t, m, e])
    else:
        data = np.transpose([t, m])
    try:
        np.savetxt(
                path + "/lightcurve_data_{}.csv".format(desc), data,
                delimiter=','
                )
    except(OSError):
        error = True
        while error is True:
            try:
                np.savetxt(
                        path + "/lightcurve_data_{}_{}.csv".format(desc, n),
                        data, delimiter=','
                        )
                error = False
            except OSError:
                n += 1
        print(
                "File of the same name already exists, file written to",
                path + "/lightcurve_data_{}_{}.csv".format(desc, n)
                )
