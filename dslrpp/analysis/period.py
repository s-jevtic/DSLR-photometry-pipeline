"""
"""
import numpy as np
from astropy.timeseries import LombScargle as lsp
from matplotlib import pyplot as plt
from scipy.signal import find_peaks

__all__ = ["periodogram", "est_period", "save_pgData"]


def __intercept(y, x1, y1, x2, y2):
    return (y-y1)*(x2-x1)/(y2-y1)+x1


def __round_up(x):
    sd = np.floor(np.log10(x))
    x /= 10**sd
    x = np.ceil(x)*10**sd
    return np.around(x, int(np.ceil(-np.log10(x))))


def periodogram(
        times, mags, errors, min_expected=0.01, max_expected=1, precision=None,
        plot=True
        ):
    if precision is None:
        precision = np.min(mags[1:] - mags[:-1])
    pRange = np.arange(min_expected, max_expected, precision)
    freq = 1/pRange
    print(times.shape, mags.shape, errors.shape)
    ls_power = lsp(times, mags, errors).power(freq)
    if plot:
        plt.figure()
        plt.title('Lomb-Scargle periodogram')
        plt.xlabel('Period')
        plt.ylabel('Lomb-Scargle power')
        plt.plot(pRange, ls_power)
    return pRange, ls_power


def est_period(pRange, power, n_estimates=1, rnd=True):
    indices = find_peaks(power, distance=20)[0]
    fRange = 1/pRange
    peaks = np.array([power[i] for i in indices])
    relevant_indices = np.array(
            [indices[i] for i in np.argsort(peaks)[-n_estimates:]]
            )
    relevant_pPeaks = np.array([pRange[i] for i in relevant_indices])
    errors = np.empty_like(relevant_pPeaks)
    j = 0
    for i in relevant_indices:
        print(
                "Analyzing peak no. {} ({:.2f},{:.2f})".format(
                        j+1, pRange[i], power[i]
                        )
                )
        pPeak = pRange[i]
        half = power[i]*0.5

        left_index = np.nonzero(half > power[:i])[0][-1]
        right_index = np.nonzero(half > power[i:])[0][0] + i

        lx1 = fRange[left_index + 1]
        lx2 = fRange[left_index]
        ly1 = power[left_index + 1]
        ly2 = power[left_index]
        left_error_freq = __intercept(half, lx1, ly1, lx2, ly2)
        print("\tLEF_POS:", left_error_freq)
        left_error_freq -= fRange[i]
        print("\tLEF:", left_error_freq)

        rx1 = fRange[right_index - 1]
        rx2 = fRange[right_index]
        ry1 = power[right_index - 1]
        ry2 = power[right_index]
        right_error_freq = __intercept(half, rx1, ry1, rx2, ry2)
        print("\tREF_POS:", right_error_freq)
        right_error_freq -= fRange[i]
        right_error_freq *= -1
        print("\tREF:", right_error_freq)

        print(
                "\tFreq error ratio {}:".format(j+1),
                left_error_freq/right_error_freq
                )

        left_rError = left_error_freq/fRange[i]
        right_rError = right_error_freq/fRange[i]
        print("\tRE:", left_rError, "\b,", right_rError)
        mean_rError = (left_rError + right_rError)/2
        error = mean_rError * pPeak
        if rnd:
            error = __round_up(error)
            pPeak = np.around(pPeak, int(np.ceil(-np.log10(error))))
        errors[j] = error
        relevant_pPeaks[j] = pPeak
        print(
                "Period candidate: {} ± {}".format(
                        relevant_pPeaks[j], errors[j]
                )
        )
        j += 1
    return relevant_pPeaks, errors


def save_pgData(path, pRange, power, desc="\b"):
    print("Saving periodogram data...")
    n = 1
    data = np.transpose([pRange, power])
    try:
        np.savetxt(
                path + "/periodogram_data_{}.csv".format(desc), data,
                delimiter=','
                )
    except(OSError):
        error = True
        while error is True:
            try:
                np.savetxt(
                        path + "/periodogram_data_{}_{}.csv".format(desc, n),
                        data, delimiter=','
                        )
                error = False
            except OSError:
                n += 1
        print(
                "File of the same name already exists, file written to",
                path + "/periodogram_data_{}_{}.csv".format(desc, n)
                )
