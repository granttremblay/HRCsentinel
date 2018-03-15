#!/usr/local/bin/python
# -*- coding: utf-8 -*-

''' Fetch MSIDs from the SKA Archive and push them
to Grant Tremblay's MSID Cloud on symmetry.cfa.harvard.edu.

I run this with a cron job every day at 1am, from a machine
on the HEAD network.

Author: Dr. Grant R. Tremblay | Harvard-Smithsonian Center for Astrophysics
'''

from __future__ import print_function

import os
import sys
import time
import datetime
from zipfile import ZipFile


def fetch_msids(msidlist, sampling, timespan):
    '''Given a list of MSIDs, fetch each
    at a given sampling rate over a given timespan.
    '''

    # Set the path to the ska_fetch command line tool. No need to set environment!
    ska_fetch = "/proj/sot/ska/arch/x86_64-linux_CentOS-6/bin/ska_fetch"

    # You're only allowed to choose between these sampling & timespan options
    sampling_options = {"5min", "daily", "full"}
    timespan_options = {"lifetime", "pastyear"}

    if sampling not in sampling_options:
        sys.exit("Sampling can only be set to 'full', '5min', or 'daily'.")
    if timespan not in timespan_options:
        sys.exit("Timespan can only be set to 'lifetime' or 'pastyear'.")

    # Given that both options are properly set, create the appropriate flags

    if timespan == "lifetime":
        start = " --start=1999:204"
    elif timespan == "pastyear":
        start = " --start=2017:001"

    # Loop through the MSID list

    for msid in msidlist:
        sample_flag = " --sampling=" + sampling
        outfile_flag = " --outfile=" + msid + ".zip"
        start_flag = start
        csvname = msid + "_" + sampling + "_{}.csv".format(timespan)

        # Use ska_fetch to query the SKA archive for the given MSID, sampling, and timespan
        os.system(ska_fetch + " " + msid + sample_flag + outfile_flag + start_flag + " --quiet")

        # Unzip the output from ska_fetch to a csv file
        zip = ZipFile(msid + ".zip")
        zip.extractall()

        # Rename CSV file to include sampling and timespan
        os.rename(msid + ".csv", csvname)

        # Quietly SCP to my MSID cloud on Dropbox
        os.system("scp -q {} grant@symmetry.cfa.harvard.edu:/Users/grant/Dropbox/HRCOps/MSIDCloud/".format(csvname))

        # Remove the temporary files to keep things clean
        os.remove(msid + ".zip")
        os.remove(csvname)

        # Print a useful message
        print("{} | {} | {}".format(msid, sampling.upper(), timespan.upper()))


def main():

    # set the working directory.
    working_dir = "/home/tremblay/MSIDs"
    os.chdir(working_dir)

    # Time the execution of this script
    start_time = time.time()

    # The Cron daemon emails me with the command-line output. Make that useful.
    today = datetime.date.today()
    print("======= Querying SKA Archive ========")
    print("=====================================")
    print(today.strftime("Refreshing MSID Cloud for %d %b %Y"))
    print("=====================================")

    hrcmsids = ["2SHEV1RT",  # HRC AntiCo Shield Rates (1)
                "2TLEV1RT",  # HRC Detector Event Rates (c/s) (1)
                "2PRBSVL",   # Primary Bus Voltage (V)
        		"2PRBSCR",   # Primary Bus Current (amps)
                "2FE00ATM",  # Front-end Temperature (c)
        		"2LVPLATM",  # LVPS Plate Temperature (c)
        		"2IMHVATM",  # Imaging Det HVPS Temperature (c)
        		"2IMINATM",  # Imaging Det Temperature (c)
        		"2SPHVATM",  # Spectroscopy Det HVPS Temperature (c)
        		"2SPINATM",  # Spectroscopy Det Temperature (c)
        		"2PMT1T",    # PMT 1 EED Temperature (c)
        		"2PMT2T",    # PMT 2 EED Temperature (c)
        		"2DCENTRT",  # Outdet2 EED Temperature (c)
        		"2FHTRMZT",  # FEABox EED Temperature (c)
        		"2CHTRPZT",  # CEABox EED Temperature (c)
        		"2FRADPYT",  # +Y EED Temperature (c)
        		"2CEAHVPT",  # -Y EED Temperature (c)
        		"2CONDMXT",  # Conduit Temperature (c)
        		"2UVLSPXT",  # Snout Temperature (c)
        		"2CE00ATM",  # CEA Temperature 1 (c)
        		"2CE01ATM", # CEA Temperature 2 (c)
                "2FEPRATM", # FEA PreAmp (c)
                "2SMTRATM", # Selected Motor Temperature (c)
                "2DTSTATT" # OutDet1 Temperature (c)
        		]

    hrcmsids_fullres = ["2SHEV1RT", "2TLEV1RT", "2CE00ATM", "2CE01ATM", "2SPHVATM", "2IMHVATM", "2FE00ATM"]

    spacecraft_orbit_pseudomsids = ["Dist_SatEarth", # Chandra-Earth distance (from Earth Center) (m)
		                    "Point_SunCentAng" # Pointing-Solar angle (from center) (deg)
		                   ]

    #fetch_msids(hrcmsids_fullres, sampling="full", timespan="lifetime")
    fetch_msids(hrcmsids, sampling="daily", timespan="lifetime")
    fetch_msids(hrcmsids, sampling="5min", timespan="lifetime")
    fetch_msids(hrcmsids_fullres, sampling="full", timespan="pastyear")
    fetch_msids(spacecraft_orbit_pseudomsids, sampling="5min", timespan="lifetime")

    runtime = round(((time.time() - start_time)/60.0), 0)
    print("=====================================")
    print("  Refresh completed in {} minutes".format(runtime))
    print("=====================================")

if __name__ == '__main__':
    main()
