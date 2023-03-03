"""
Does the entire photometry process, from DSLR image processing to photometry
to period analysis.
"""
from argparse import ArgumentParser
from dslrpp import sort, get_offsets, lightcurve
from dslrpp.analysis import save_lcData, periodogram, est_period
from dslrpp.analysis.period import save_pgData


def data_from_file(file):
    lines = file.readlines()
    N_STARS = len(lines)
    if N_STARS < 2:
        raise ValueError('Not enough data provided! Did you provide'
                         ' reference star coordinates?')
    numbers = lines[0].split(',')
    if len(numbers) != 2:
        raise ValueError('Too many or not enough numbers on line 1!')
    var_coords = [int(number) for number in numbers]
    ref_data = []
    for i in range(1, N_STARS):
        numbers = lines[i].split(',')
        if len(numbers) != 3:
            raise ValueError(
                f'Too many or not enough numbers on line {i + 1}!'
                )
        ref_data.append([
            int(numbers[0]), int(numbers[1]), float(numbers[2])
        ])
    return N_STARS, var_coords, ref_data


def data_from_cli():
    N_STARS = 0

    var_coords = ()
    valid_input = False
    while not valid_input:
        print(
            "Enter coordinates of variable star separated by a space:",
            end=' '
        )
        numbers = input().split()
        try:
            assert len(numbers) == 2
            x = int(numbers[0])
            y = int(numbers[1])
        except ValueError:
            print("Coordinates must be integers!")
            continue
        except AssertionError:
            print("There must be two coordinates!")
            continue
        var_coords = (x, y)
        valid_input = True

    valid_input = False
    while not valid_input:
        print("Enter number of reference stars:", end=' ')
        try:
            N_STARS = int(input()) + 1
        except TypeError:
            print("Input must be an integer!")
            continue
        valid_input = True

    ref_data = []
    for i in range(N_STARS - 1):
        x = 0
        y = 0
        m = 0
        valid_input = False
        while not valid_input:
            print(
                f"Enter coordinates of reference star {i + 1} separated by"
                " a space:", end=" "
            )
            numbers = input().split()
            try:
                assert len(numbers) == 2
                x = int(numbers[0])
                y = int(numbers[1])

            except ValueError:
                print("Coordinates must be integers!")
                continue
            except AssertionError:
                print("There must be two coordinates!")
                continue
            valid_input = True

        valid_input = False
        while not valid_input:
            print(f"Enter magnitude of reference star {i + 1}:", end=" ")
            try:
                m = float(input())
            except ValueError:
                print("Magnitude must be a number!")
                continue
            valid_input = True
        ref_data.append([x, y, m])

    return N_STARS, var_coords, ref_data


parser = ArgumentParser(
                    description='A pipeline for lightcurve analysis of '
                    'DSLR RAW images')


parser.add_argument('path',
                    help='path where data is stored')
# parser.add_argument('-v', '--variable-coords', nargs=2, type=int,
                    # required=True,
                    # help='pixel coordinates (x, y) of variable star',
                    # dest='variable_coords')
# parser.add_argument('-c', '--ref-count', type=int, default=1, required=True,
                    # choices=itertools.count(1),
                    # help='number of reference stars', dest='ref_count')
# parser.parse_known_args()

# try:
    # refcount = parser.ref_count
# except AttributeError:
    # parser.parse_args('--help')

# parser.add_argument('-r', '--ref-data', nargs=refcount*3, type=int,
                    # help='pixel coordinates and magnitude(s) (x, y, m) of '
                    # 'reference star(s)', dest='ref_data')

parser.add_argument('-f', '--file', type=str,
                    help='file to read the data from')

# parser.add_argument('variable_coords', nargs=2, type=int)
# parser.add_argument('ref_data', nargs='+', type=[int, int, float])

binning = parser.add_argument_group()
binning.add_argument('-x', '--bin-x', type=int,
                     help='binning over the x axis', dest='bin_x')
binning.add_argument('-y', '--bin-y', type=int,
                     help='binning over the y axis'
                     ' (same as x if not provided)', dest='bin_y')

cols = parser.add_argument_group()
cols.add_argument('-R', '--use-red', action='store_true',
                  help='process red pixels', dest='use_red')
cols.add_argument('-G', '--use-green', action='store_true',
                  help='process green pixels', dest='use_green')
cols.add_argument('-B', '--use-blue', action='store_true',
                  help='process blue pixels', dest='use_blue')

pg_params = parser.add_argument_group()
pg_params.add_argument('-m', '--periodogram-min', type=float, default=0.02,
                       help='the minimum value in days for the periodogram',
                       dest='periodogram_min')
pg_params.add_argument('-M', '--periodogram-max', type=float, default=10,
                       help='the maximum value in days for the periodogram',
                       dest='periodogram_max')
pg_params.add_argument('-p', '--periodogram-precision', type=float,
                       default=0.01,
                       help='periodogram precision in days',
                       dest='periodogram_precision')
args = parser.parse_args()

PATH = args.path
if PATH.endswith('/'):
    PATH = PATH[:-1]

N_STARS = 0
var_coords = ()
ref_data = []

if args.file:
    file = open(args.file, 'r')
    N_STARS, var_coords, ref_data = data_from_file(file)
else:
    N_STARS, var_coords, ref_data = data_from_cli()

red = args.use_red
green = args.use_green
blue = args.use_blue
binX = args.bin_x
binY = args.bin_y
pMin = args.periodogram_min
pMax = args.periodogram_max
pP = args.periodogram_precision

if not (red or green or blue):
    print("No color specified! Specify at least one of the options:")
    print("-R, --use-red")
    print("-G, --use-green")
    print("-B, --use-blue")
    exit()

imagesR, imagesG, imagesB = sort(PATH, red, green, blue, binX, binY)

if red:
    imagesR[0].add_star(*var_coords, name="Var")
    for i in range(N_STARS-1):
        imagesR[0].add_star(
                *ref_data[i], name="Ref{}".format(i+1)
                )
    get_offsets(*imagesR, global_offset=False, gauss=True)
    times, mags, errs = lightcurve(*imagesR)
    save_lcData(PATH, times, mags, errs, desc='R')
    pRange, power = periodogram(times, mags, errs, pMin, pMax, pP)
    save_pgData(PATH, pRange, power, desc='R')
    est_period(pRange, power, n_estimates=2)

if green:
    imagesG[0].add_star(*var_coords, name="Var")
    for i in range(N_STARS-1):
        imagesG[0].add_star(
                *ref_data[i], name="Ref{}".format(i+1)
                )
    print("Getting offsets...")
    get_offsets(*imagesG, global_offset=False, gauss=True)
    times, mags, errs = lightcurve(*imagesG)
    save_lcData(PATH, times, mags, errs, desc='G')
    pRange, power = periodogram(times, mags, errs, pMin, pMax, pP, plot=True)
    save_pgData(PATH, pRange, power, desc='G')
    est_period(pRange, power, n_estimates=2)

if blue:
    imagesB[0].add_star(*var_coords, name="Var")
    for i in range(N_STARS-1):
        imagesR[0].add_star(
                *ref_data[i], name="Ref{}".format(i+1)
                )
    get_offsets(*imagesB, global_offset=False, gauss=True)
    times, mags, errs = lightcurve(*imagesB)
    save_lcData(PATH, times, mags, errs, desc='B')
    pRange, power = periodogram(times, mags, errs, pMin, pMax, pP)
    save_pgData(PATH, pRange, power, desc='B')
    est_period(pRange, power, n_estimates=2)
