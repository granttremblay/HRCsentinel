#!/usr/bin/env python

"""
generate_msid_plots.py: Plot all MSIDs in MSIDcloud, save them as PNGs.
"""

from __future__ import division, print_function

import os
import sys
import glob

import time
import datetime as dt

from astropy.io import ascii
from astropy.table import Table
from astropy.table import vstack

import numpy as np

import matplotlib.pyplot as plt
from matplotlib.dates import epoch2num

import numpy as np

from hrcsentinel import hrccore as hrc
from hrcsentinel import hrcplotters as hrcplot


def main():

    script_location = os.getcwd()
    homedirectory = os.path.expanduser("~")

    msidcloud_directory = homedirectory + "/Dropbox/HRCOps/MSIDCloud/"

    #print("Making sure you're in {}".format(goes_data_directory))
    os.chdir(msidcloud_directory)

    msidlist = glob.glob("*lifetime.csv")

    hrcplot.styleplots()

    for msid in msidlist:
        msidName, values, times = parse_msid(msid)
        plotit(msidName, values, times)

    # Return to the starting directory
    os.chdir(script_location)


def parse_msid(msid):

    # Make a string of just the MSID name. Use split to separate on underscores
    msidName = msid.split("_")[0]
    print("Plotting {}.".format(msidName))

    data = ascii.read(msid, format="fast_csv")

    # Simple check to see if this data is binned or full resolution
    if 'midvals' in data.colnames:
        values = data['midvals']
    else:
        values = data['vals']

    times = hrc.convert_chandra_time(data['times'])

    return msidName, values, times


def plotit(msidName, values, times):
    # Make a simple plot, save it rastered.

    # Check that the plots subdirectory exists. If not, create it.
    plot_dir = "plots/"
    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)
        print("Plot subdirectory 'plots/' not found. Creating it.")

    fig, ax = plt.subplots(figsize=(12, 8))

    ax.plot_date(times, values, markersize=1.0, label=msidName)

    ax.legend()

    fig.savefig(plot_dir + msidName + '.png', dpi=300)

    # Always close your plots so you don't needlessly consume too much memory
    plt.close()



if __name__ == '__main__':
    start_time = time.time()

    main()

    runtime = round((time.time() - start_time), 3)
    print("Finished in {} seconds".format(runtime))
