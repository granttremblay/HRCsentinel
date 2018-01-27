#!/usr/bin/env python

'''
goes2hrc.py: Convert recent GOES pchan 5min data to estimated HRC Shield Rates
'''

import os
import sys
import glob

try:
    # python 2.x
    import urllib
    from urllib import urlretrieve
except ImportError:
    # python 3.x
    import urllib
    from urllib.request import urlretrieve

import time
import datetime as dt

from astropy.io import ascii
from astropy.table import Table
from astropy.table import vstack
from astropy.table import hstack

import numpy as np
np.seterr(divide='ignore', invalid='ignore')

from scipy import stats


def main():
    '''
    Read, Parse, and Convert the GOES Archive to HRC Estimated rates.
    Write the final table object to a .csv file.
    '''

    # Ensure that the home directory is found regardless of platform,
    # e.g. /Users/grant vs /home/grant
    script_location = os.getcwd()
    homedirectory = os.path.expanduser("~")

    shieldcloud_directory = homedirectory + "/Dropbox/HRCOps/ShieldCloud/"
    goes_data_directory = shieldcloud_directory + "goes_5min_data/"

    #print("Making sure you're in {}".format(goes_data_directory))
    os.chdir(goes_data_directory)

    found_goes_data = glob.glob("*_Gp_pchan_5m.txt")

    if len(found_goes_data) < 950:
        download_all_goes_data()
    else:
        download_latest_goes_data()

    final_table = process_goes_archive(goes_data_directory)
    final_csv = shieldcloud_directory + "HRC_GOES_estrates.csv"

    os.chdir(shieldcloud_directory)
    ascii.write(final_table, final_csv,
                format='csv', fast_writer=True, overwrite=True)

    os.chdir(script_location)

def download_all_goes_data():
    '''
    Run the shell script for now. MAKE THIS PYTHON LATER!
    '''
    os.system('sh refresh_goes_5min_data.sh')


def download_latest_goes_data():
    '''
    If most GOES data IS found, fetch today's GOES 5min data from NOAA.gov
    '''

    # Print today's date in a way matching the NOAA filenames, e.g. 20170525
    prefix = dt.datetime.today().strftime('%Y%m%d')
    latest_data_filename = prefix + "_Gp_pchan_5m.txt"

    noaa_server = "ftp://anonymous:test@ftp.swpc.noaa.gov/pub/lists/pchan/"

    ftp_url = noaa_server + latest_data_filename

    try:
        urlretrieve(ftp_url, latest_data_filename)
        print("Fetching latest GOES data.".format(latest_data_filename))
    except urllib.error.URLError:
        print("Downloaded GOES data is up-to-date")


def process_goes_archive(goes_data_directory):

    # The GOES data directory has some shell scripts and a README, you don't want to stack those obvi.
    files_to_read = glob.glob(goes_data_directory + "*Gp*pchan*txt")

    # The list won't be alphanumeric. Fix that.
    allfiles = sorted(files_to_read)

    stacked_goes_tables = stack_goes_tables(allfiles)

    goestimes = convert_goes_time(stacked_goes_tables)

    hrc_est_rate1, hrc_est_rate2 = estimate_HRC_shieldrates(
        stacked_goes_tables)

    final_table = Table([goestimes, hrc_est_rate1, hrc_est_rate2], names=(
        "Times", "HRC_Rate1", "HRC_Rate2"))

    print("GOES data parsed and converted to HRC rate estimates.")

    return final_table


def stack_goes_tables(allfiles):
    '''
    Vertically stack the Goes astropy table objects
    '''

    alltables = []

    for i, item in enumerate(allfiles):
        percent_finished = round((i / len(allfiles)) * 100)
        print("Parsing GOES Table {} of {} ({}% Finished)".format(
            i + 1, len(allfiles), percent_finished), end="\r")
        table = ascii.read(item, data_start=2)
        alltables.append(table)

    stacked_goes_tables = vstack(alltables)

    return stacked_goes_tables


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


if __name__ == '__main__':
    start_time = time.time()

    main()

    runtime = round((time.time() - start_time), 3)
    print("Finished in {} seconds.".format(runtime))
