#!/usr/bin/env python

'''
goes2hrc.py: Convert recent GOES pchan 5min data to estimated HRC Shield Rates
'''

import os
import sys
# import glob

import time
import datetime as dt

from astropy.io import ascii

import matplotlib.pyplot as plt
from matplotlib.dates import num2date

import numpy as np
# np.seterr(divide='ignore', invalid='ignore')

try:
    from hrcsentinel import hrccore as hrc
    from hrcsentinel import hrcplotters as hrcplot
	# I still need to better understand this: https://stackoverflow.com/questions/16981921/relative-imports-in-python-3/28154841
except ImportError:
	raise ImportError("HRCsentinel required. Download here: https://github.com/granttremblay/HRCsentinel")


def generate_scs107_plots():

    # Ensure that the home directory is found regardless of platform,
    # e.g. /Users/grant vs /home/grant
    # script_location = os.getcwd()

    home_directory = os.path.expanduser("~")
    figure_save_directory = home_directory + "/Dropbox/HRCOps/ShieldCloud/scs107_plots/nolog/"

    if not os.path.exists(figure_save_directory):
        print("Created {}".format(figure_save_directory))
        os.makedirs(figure_save_directory)

    msid_directory = home_directory + "/Dropbox/HRCOps/MSIDCloud/"
    goes_directory = home_directory + "/Dropbox/HRCOps/ShieldCloud/"

    times, values = hrc.parse_generic_msid(msid_directory + "2SHEV1RT_5min_lifetime.csv", "midvals")

    # mask zero values
    values[values == 0] = np.nan

    goestimes, goesrates = hrc.parse_goes(goes_directory + "HRC_GOES_estrates.csv")
    orbit = hrc.parse_orbits(msid_directory + "orbits_table.csv")
    scs107times = hrc.parse_scs107s(msid_directory + "scs107s_table.csv")

    data = {"times": times,
            "values": values,
            "goestimes": goestimes,
            "goesrates": goesrates,
            "orbit": orbit,
            "scs107times": scs107times}


    ylims = (100, 100000)

    # SCS 107 times are already in no. of days since 1 AD
    daypad = 2 # days on either side of SCS 107 excecution to plot

    for shutdown in scs107times:

        # Give the PDF a useful title & filename with the SCS 107 execution date
        filename_with_date = num2date(shutdown).strftime('%Y-%m-%d_scs107') + ".pdf"
        title = num2date(shutdown).strftime('SCS 107 on %Y-%m-%d')

        # Plot +/- daypad around each SCS 107 execution time
        scs107_xlims = (num2date(shutdown-daypad), num2date(shutdown+daypad))

        # Make the plots. This will take a while!
        hrcplot.shieldsentinel_plotter(data,
                                       xlims=scs107_xlims,
                                       ylims=ylims,
                                       log=False,
                                       markersize=2.0,
                                       title=title,
                                       showfig=False,
                                       savefig=True,
                                       filename=figure_save_directory + filename_with_date)


if __name__ == '__main__':
    start_time = time.time()
    generate_scs107_plots()
    runtime = round((time.time() - start_time), 3)
    print("Finished in {} minutes.".format(runtime/60))
