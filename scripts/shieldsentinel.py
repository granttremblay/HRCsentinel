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
except ImportError:
	raise ImportError("hrcsentinel required. Download here: https://github.com/granttremblay/HRCsentinel")


import imageio

def generate_scs107_plots():

    # Ensure that the home directory is found regardless of platform,
    # e.g. /Users/grant vs /home/grant
    # script_location = os.getcwd()

    home_directory = os.path.expanduser("~")
    figure_save_directory = home_directory + "/Dropbox/HRCOps/ShieldCloud/scs107_plots/new/"

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
    every_day = times[1::288] # every 228 steps = 1 day in 5 minute increments

    data = {"times": times,
            "values": values,
            "goestimes": goestimes,
            "goesrates": goesrates,
            "orbit": orbit,
            "scs107times": scs107times}


    ylims = (100, 70000)

    # SCS 107 times are already in no. of days since 1 AD
    daypad = 2 # days on either side of SCS 107 excecution to plot

    # for day in every_day:

    #     # Give the PDF a useful title & filename with the SCS 107 execution date
    #     filename_with_date = num2date(day).strftime('%Y-%m-%d_daystep') + ".png"
    #     title = num2date(day).strftime('%Y')

    #     # Plot +/- daypad around each SCS 107 execution time
    #     scs107_xlims = (num2date(day-daypad), num2date(day+daypad))

    #     # Make the plots. This will take a while!
    #     shieldsentinel_plotter(data,
    #                            xlims=scs107_xlims,
    #                            ylims=ylims,
    #                            log=False,
    #                            markersize=2.0,
    #                            title=title,
    #                            showfig=False,
    #                            savefig=True,
    #                            showlegend=False,
    #                            dpi=150,
    #                            filename=figure_save_directory + filename_with_date)


    for shutdown in scs107times:

        # Give the PDF a useful title & filename with the SCS 107 execution date
        filename_with_date = num2date(shutdown).strftime('%Y-%m-%d_scs107') + ".pdf"
        title = num2date(shutdown).strftime('SCS 107 on %Y-%m-%d')

        # Plot +/- daypad around each SCS 107 execution time
        scs107_xlims = (num2date(shutdown-daypad), num2date(shutdown+daypad))

        # Make the plots. This will take a while!
        shieldsentinel_plotter(data,
                               xlims=scs107_xlims,
                               ylims=ylims,
                               log=False,
                               markersize=2.0,
                               title=title,
                               showfig=False,
                               savefig=True,
                               filename=figure_save_directory + filename_with_date)


def shieldsentinel_plotter(data, xlims=None, ylims=None, log=False, title=None, markersize=1.0, showlegend=True,
             rasterized=True, dpi=300, showfig=True, savefig=False, filename="NAME_ME.pdf"):


    # Unpack the data. Yes I know this is redundant but I'm lazy.

    times = data["times"]
    values = data["values"]
    goestimes = data["goestimes"]
    goesrates = data["goesrates"]
    orbit = data["orbit"]
    scs107times = data["scs107times"]


    # make plots pretty
    hrc.styleplots()

    goescolor = list(plt.rcParams['axes.prop_cycle'])[1]['color']
    shieldcolor = list(plt.rcParams['axes.prop_cycle'])[0]['color']
    scs107color = list(plt.rcParams['axes.prop_cycle'])[2]['color']
    thresholdcolor = list(plt.rcParams['axes.prop_cycle'])[3]['color']

    ########### THE PLOT GOES HERE ###############

    fig, ax = plt.subplots(figsize=(16,8))

    # Plot SCS 107s as vertical lines marking start times
    for scs107 in scs107times:
        plt.axvline(scs107, linestyle='dashed', lw=2.0, color=scs107color, alpha=1.0, rasterized=rasterized)
    # Double plot the Spetembrer Event lines
    plt.axvline(scs107times[-1], linestyle='dashed', lw=2.0, color=scs107color, alpha=1.0, label="SCS 107 Execution", rasterized=rasterized)
    # Plot horizontal line showing the SCS 107 threshold for the HRC Shield
    plt.axhline(y=65535, color=thresholdcolor, alpha=1.0, label="SCS 107 Threshold (65,535 cps)", rasterized=rasterized)

    # Plot Radzone Passages, only make a label once .
    for i, (entry, exit) in enumerate(zip(orbit["Radzone Entry"], orbit["Radzone Exit"])):
        plt.axvspan(entry, exit, alpha=0.4, color='gray', label="Radzone Passage" if i == 0 else "", rasterized=rasterized)

    # Plot the GOES/HRC Estimated rate
    ax.plot_date(goestimes, goesrates, '-', lw=1.0, label="GOES Estimate", color=goescolor, rasterized=rasterized)

    ax.plot_date(times, values, markersize=markersize, color=shieldcolor,
                 label="HRC Shield Rate (2SHEV1RT)", rasterized=rasterized)


    if log is True:
        ax.set_yscale('log')

    if title is not None:
        ax.set_title(title)

    if xlims is not None:
        ax.set_xlim(xlims[0], xlims[1])

    if ylims is not None:
        ax.set_ylim(ylims[0], ylims[1])

    ax.set_ylabel(r'Counts s$^{-1}$')
    ax.set_xlabel('Date')

    if showlegend is True:
        ax.legend()

    #ax.set_xlim(dt.datetime(2017,9,3),dt.datetime(2017,9,21))

    if savefig is True:
        print("Saving figure to {}.".format(filename))
        fig.savefig(filename, dpi=dpi)

    if showfig is True:
        plt.show()

    # Close the plot so you don't eat too much memory when making 100 of these.
    plt.close()


if __name__ == '__main__':
    start_time = time.time()
    generate_scs107_plots()
    runtime = round((time.time() - start_time), 3)
    print("Finished in {} minutes.".format(round(runtime/60, 3)))
