"""
Does the entire photometry process, from DSLR image processing to photometry
to period analysis.
"""
import sys
import numpy as np
from dslrpp import sort, get_offsets, lightcurve
from dslrpp.analysis import save_lcData, periodogram, est_period
from dslrpp.analysis.period import save_pgData


def printHelpMsg():
    print(
            "Usage:",
            "pipeline.py x0 y0 (variable star coords)"
            "<x1> <y1> <m1> [x2] [y2] [m2]..."
            "(reference star coords) [optional args]",
            "Optional arguments:",
            "-b <x> [y] (binning)",
            "-c <r/g/b> (color(s) to use)",
            "-p <min> <max> [precision] (periodogram parameters)",
            sep='\n'
            )
    exit()


def checkIfInt(x):
    try:
        if float(x) != int(x):
            printHelpMsg()
    except ValueError:
        printHelpMsg()


def checkIfFloat(x):
    try:
        float(x)
    except ValueError:
        printHelpMsg()


if len(sys.argv) < 6:
    printHelpMsg()

PATH = sys.argv[1]

for i in range(1, 6):
    checkIfInt(sys.argv[i])
checkIfFloat(sys.argv[7])

var_coords = (int(sys.argv[2]), int(sys.argv[3]))
ref_coords = [(int(sys.argv[4]), int(sys.argv[5]))]
ref_mags = [int(sys.argv[6])]
N_STARS = len(ref_coords) + 1

if len(sys.argv) == 8:
    printHelpMsg()

red = False
green = True
blue = False
binX = None
binY = None
pMin = 0.01
pMax = 1
pP = None

if len(sys.argv) >= 9:
    i = 8
    while i <= len(sys.argv)+3:
        if sys.argv[i][0] == '-':
            break
        if sys.argv[i+1][0] == '-':
            printHelpMsg()
        if sys.argv[i+2][0] == '-':
            printHelpMsg()
        checkIfInt(sys.argv[i])
        checkIfInt(sys.argv[i+1])
        checkIfFloat(sys.argv[i+2])
        ref_coords.append((int(sys.argv[i]), int(sys.argv[i+1])))
        ref_mags.append(sys.argv[i+2])
        i += 3
    if i+1 == len(sys.argv):
        printHelpMsg()
    if i+2 <= len(sys.argv):
        for j in range(i, i+3):
            if sys.argv[i][0] != '-':
                printHelpMsg()
            i += 1
            if sys.argv[i][1] == 'b':
                checkIfInt(sys.argv[i+1])
                binX = sys.argv[i+1]
                binY = binX
                i += 1
                try:
                    if sys.argv[i+2][0] != '-':
                        checkIfInt(sys.argv[i+2])
                        binY = int(sys.argv[i+2])
                        i += 1
                except IndexError:
                    break
            elif sys.argv[i][1] == 'c':
                if len(sys.argv == i+1):
                    printHelpMsg()
                i += 1
                if 'r' in sys.argv[i+1]:
                    red = True
                else:
                    red = False
                if 'g' in sys.argv[i+1]:
                    green = True
                else:
                    green = False
                if 'b' in sys.argv[i+1]:
                    blue = True
                else:
                    blue = False
            elif sys.argv[i][1] == 'p':
                if len(sys.argv <= i+2):
                    printHelpMsg()
                i += 1
                for arg in sys.argv[i:i+2]:
                    checkIfFloat(arg)
                pMin = sys.argv[i]
                pMax = sys.argv[i+1]
                i += 2
                if len(sys.argv) == i:
                    break
                if sys.argv[i][0] == '-':
                    pass
                else:
                    checkIfFloat(sys.argv[i])
                    pP = sys.argv[i]
                    i += 1
            else:
                printHelpMsg()


imagesR, imagesG, imagesB = *sort(PATH, red, green, blue, binX, binY)

if imagesR.size != 0:
    imagesR[0].add_star(var_coords, name="Var")
    for i in range(N_STARS-1):
        imagesR[0].add_star(
                ref_coords[i], ref_mags[i], name="Ref{}".format(i+1)
                )
    get_offsets(imagesR, global_offset=False, gauss=True)
    times, mags, errs = lightcurve(imagesR)
    save_lcData(PATH, times, mags, errs, desc='R')
    pRange, power = periodogram(times, mags, errs, pMin, pMax, pP)
    save_pgData(PATH, pRange, power, desc='R')
    est_period(pRange, power, n_estimates=2)

if imagesG.size != 0:
    imagesG[0].add_star(var_coords, name="Var")
    for i in range(N_STARS-1):
        imagesG[0].add_star(
                ref_coords[i], ref_mags[i], name="Ref{}".format(i+1)
                )
    get_offsets(imagesG, global_offset=False, gauss=True)
    times, mags, errs = lightcurve(imagesG)
    save_lcData(PATH, times, mags, errs, desc='G')
    pRange, power = periodogram(times, mags, errs, pMin, pMax, pP)
    save_pgData(PATH, pRange, power, desc='G')
    est_period(pRange, power, n_estimates=2)

if imagesB.size != 0:
    imagesB[0].add_star(var_coords, name="Var")
    for i in range(N_STARS-1):
        imagesR[0].add_star(
                ref_coords[i], ref_mags[i], name="Ref{}".format(i+1)
                )
    get_offsets(imagesB, global_offset=False, gauss=True)
    times, mags, errs = lightcurve(imagesB)
    save_lcData(PATH, times, mags, errs, desc='B')
    pRange, power = periodogram(times, mags, errs, pMin, pMax, pP)
    save_pgData(PATH, pRange, power, desc='B')
    est_period(pRange, power, n_estimates=2)
