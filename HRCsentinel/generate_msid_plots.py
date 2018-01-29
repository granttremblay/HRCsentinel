#!/usr/bin/env python

"""
generate_msid_plots.py: Plot all MSIDs in MSIDcloud, save them as PNGs.
"""

__author__ = "Dr. Grant R. Tremblay"
__license__ = "MIT"

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

    times = convert_chandra_time(data['times'])

    return msidName, values, times


def convert_chandra_time(rawtimes):
    """
    Convert input CXC time (sec) to the time base required for the matplotlib
    plot_date function (days since start of the Year 1 A.D - yes, really).
    :param times: iterable list of times, in units of CXCsec (sec since 1998.0)
    :rtype: plot_date times (days since Year 1 A.D.)
    """

    # rawtimes is in units of CXC seconds, or seconds since 1998.0
    # Compute the Delta T between 1998.0 (CXC's Epoch) and 1970.0 (Unix Epoch)

    seconds_since_1998_0 = rawtimes[0]

    cxctime = dt.datetime(1998, 1, 1, 0, 0, 0)
    unixtime = dt.datetime(1970, 1, 1, 0, 0, 0)

    # Calculate the first offset from 1970.0, needed by matplotlib's plotdate
    # The below is equivalent (within a few tens of seconds) to the command
    # t0 = Chandra.Time.DateTime(times[0]).unix
    delta_time = (cxctime - unixtime).total_seconds() + seconds_since_1998_0

    plotdate_start = epoch2num(delta_time)

    # Now we use a relative offset from plotdate_start
    # the number 86,400 below is the number of seconds in a UTC day

    chandratime = (np.asarray(rawtimes) -
                   rawtimes[0]) / 86400. + plotdate_start

    return chandratime

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

def styleplots():
    plt.style.use('ggplot')

    labelsizes = 13

    plt.rcParams['font.size'] = labelsizes
    plt.rcParams['axes.titlesize'] = 12
    plt.rcParams['axes.labelsize'] = labelsizes
    plt.rcParams['xtick.labelsize'] = labelsizes
    plt.rcParams['ytick.labelsize'] = labelsizes

def main():

    styleplots()

    msidlist = glob.glob("*pastyear.csv")

    for msid in msidlist:
        msidName, values, times = parse_msid(msid)
        plotit(msidName, values, times)


if __name__ == '__main__':
    start_time = time.time()

    main()

    runtime = round((time.time() - start_time), 3)
    print("Finished in {} seconds".format(runtime))
