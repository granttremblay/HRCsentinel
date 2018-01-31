#!/usr/bin/env python

from __future__ import print_function, division

import os
import sys

import time
import datetime as dt

from astropy.io import ascii
from astropy.table import Table
from astropy.table import vstack

import numpy as np

from scipy.signal import argrelmax

import matplotlib.pyplot as plt
from matplotlib.dates import epoch2num

import numpy as np
from scipy import stats



def styleplots():
    """
    Make plots pretty and labels clear.
    """
    plt.style.use('ggplot')

    labelsizes = 15

    plt.rcParams['font.size'] = labelsizes
    plt.rcParams['axes.titlesize'] = 12
    plt.rcParams['axes.labelsize'] = labelsizes
    plt.rcParams['xtick.labelsize'] = labelsizes
    plt.rcParams['ytick.labelsize'] = labelsizes


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

def quickplot(x, save=False, filename=None):
    """
    A quicklook function to only plot an MSID vs its index (e.g., for get dates, etc)
    """
    fig, ax = plt.subplots(figsize=(12, 8))

    ax.plot(x, marker='o', markersize=1, lw=0, rasterized=True)
    ax.set_ylabel('Telemetry Value')
    ax.set_xlabel('Index of Telemetry Datapoint')

    plt.show()

    if save is True:
        if filename is not None:
            fig.savefig(filename, dpi=400)
        else:
            print("Specify a filename (i.e. 'figure.pdf').")


def convert_orbit_time(rawtimes):
    """
    The orbit table gives times in the format: 2000:003:15:27:47.271, i.e.
    YYYY:DOY:HH:MM:SS.sss, so you need to convert these into a matplotlib date.
    """

    # Using %S.%f at the end converts to microseconds. I tested this
    # and it's correct.

    orbittime = []

    for i in range(len(rawtimes)):
        orbittime.append(dt.datetime.strptime(
            rawtimes[i], "%Y:%j:%H:%M:%S.%f"))

    return orbittime


def convert_goes_time(rawtable):
    '''
    Convert GOES ascii data time columns into datetime objects.
    '''

    length = len(rawtable['col1'])
    goestimes = []

    for i in range(length):
        year = rawtable['col1'][i]
        month = rawtable['col2'][i]
        day = rawtable['col3'][i]
        daysecond = rawtable['col6'][i]

        struc_time = time.gmtime(int(daysecond))

        hour = struc_time.tm_hour
        minute = struc_time.tm_min
        second = struc_time.tm_sec

        goesdate = dt.datetime(year=year, month=month,
                               day=day, hour=hour,
                               minute=minute, second=second)

        goestimes.append(goesdate)

    print("GOES time data converted to datetime objects.")

    return goestimes



def estimate_HRC_shieldrates(master_table):
    '''
    Makes two estimates of the HRC shield rate, according
    to J. Chappell's formulae (which are known to work very well).
    '''

    p4 = master_table['col9']  # Protons from 15-40 MeV in #/cm2-s-sr-MeV
    p5 = master_table['col10']  # 38-82 MeV
    p6 = master_table['col11']  # 84-200 MeV

    try:
        h = p4 / p5
    except ZeroDivisionError:
        h = np.NaN

    np.seterr(divide='ignore', invalid='ignore')

    # This is largely pulled out of you-know-where.
    hrc_est_rate1 = (6000 * p4 + 270000 * p5 + 100000 * p6)
    hrc_est_rate2 = ((-h * 200 * p4) + (h * 9000 * p5) +
                     (h * 11000 * p6) + hrc_est_rate1) / 1.7

    # Mask bad values with NaNs.
    hrc_est_rate1[hrc_est_rate1 < 100] = np.nan
    hrc_est_rate2[hrc_est_rate2 < 100] = np.nan

    print("HRC Shield Rates Estimated from GOES Data.")

    return hrc_est_rate1, hrc_est_rate2



