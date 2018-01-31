
#!/usr/bin/env python

'''
plots_for_paper.py: Create plots for Grant Tremblay's HRC Shield Memo
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

import hrccore as hrc


def main():

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

    times, values = parse_msid(msid_directory + "2SHEV1RT_5min_lifetime.csv", "midvals")

    # mask zero values
    values[values == 0] = np.nan

    goestimes, goesrates = parse_goes(goes_directory + "HRC_GOES_estrates.csv")
    orbit = parse_orbits(msid_directory + "orbits_table.csv")
    scs107times = parse_scs107s(msid_directory + "scs107s_table.csv")

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
        shieldsentinel_plotter(data,
                               xlims=scs107_xlims,
                               ylims=ylims,
                               log=False,
                               markersize=2.0,
                               title=title,
                               showfig=False,
                               savefig=True,
                               filename=figure_save_directory + filename_with_date)


def shieldsentinel_plotter(data, xlims=None, ylims=None, log=False, title=None, markersize=1.0,
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
        plt.axvline(scs107, linestyle='dashed', lw=2.0, color=scs107color, alpha=1.0)
    # Double plot the Spetembrer Event lines
    plt.axvline(scs107times[-1], linestyle='dashed', lw=2.0, color=scs107color, alpha=1.0, label="SCS 107 Execution")
    # Plot horizontal line showing the SCS 107 threshold for the HRC Shield
    plt.axhline(y=65535, color=thresholdcolor, alpha=1.0, label="SCS 107 Threshold (65,535 cps)")

    # Plot Radzone Passages, only make a label once .
    for i, (entry, exit) in enumerate(zip(orbit["Radzone Entry"], orbit["Radzone Exit"])):
        plt.axvspan(entry, exit, alpha=0.4, color='gray', label="Radzone Passage" if i == 0 else "")

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

    ax.legend()

    #ax.set_xlim(dt.datetime(2017,9,3),dt.datetime(2017,9,21))

    if savefig is True:
        print("Saving figure to {}.".format(filename))
        fig.savefig(filename, dpi=dpi, bbox_inches='tight')

    if showfig is True:
        plt.show()

    # Close the plot so you don't eat too much memory when making 100 of these.
    plt.close()

def parse_msid(msid, valtype):
    """
    Parse & convert the CSVs from MSIDCloud relevant to this study.
    """

    msid = ascii.read(msid, format="fast_csv")

    times = hrc.convert_chandra_time(msid["times"])
    values = msid[valtype]

    print("MSIDs parsed")
    return times, values



def parse_goes(goestable):
    """
    Parse my GOES estimated shieldrates table created by goes2hrc.py
    """

    goes = ascii.read(goestable, format="fast_csv")

    goestimes = hrc.convert_goes_time(goes["Times"])
    goesrates = goes['HRC_Rate2']

    print("GOES-to-HRC estimates parsed")

    return goestimes, goesrates


def parse_orbits(orbit_msid):

    # Make sure the .csv file exists before trying this:
    if os.path.isfile(orbit_msid):
        msid = ascii.read(orbit_msid, format="fast_csv")

        print("Spacecraft orbits parsed")
    else:
        print("MSID CSV file not present")
        sys.exit(1)

    # Available fields in Orbit table:
    # start,stop,tstart,tstop,dur,orbit_num,perigee,apogee,t_perigee,
    # start_radzone,stop_radzone,dt_start_radzone,dt_stop_radzone

    # Times are given like: 2000:003:15:27:47.271, so you need to convert
    # them into an mpl date.

    radzone_entry = hrc.convert_orbit_time(msid['start_radzone'])
    radzone_exit = hrc.convert_orbit_time(msid['stop_radzone'])

    orbit = {"Radzone Entry": radzone_entry,
             "Radzone Exit": radzone_exit}

    return orbit


def parse_scs107s(scs107s_table):
    """
    Parse SCS 107s
    """

    scs107s = ascii.read(scs107s_table)

    scs107times = hrc.convert_chandra_time(scs107s['tstart'])

    print("Found {} executions of SCS 107 over the mission lifetime".format(len(scs107times)))

    return scs107times


if __name__ == '__main__':
    start_time = time.time()
    main()
    runtime = round((time.time() - start_time), 3)
    print("Finished in {} minutes.".format(runtime/60))
