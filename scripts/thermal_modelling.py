#!/usr/bin/env python

'''
thermal_modelling.py: Create plots of all relevant HRC temperature msids
for Henry Berger's thermal model of the instrument.
'''

import os
# import sys
# # import glob
#
# import time
# import datetime as dt
#
# from astropy.io import ascii
#
import matplotlib.pyplot as plt
from matplotlib.dates import num2date

import numpy as np
# np.seterr(divide='ignore', invalid='ignore')

try:
    from hrcsentinel import hrccore as hrc
except ImportError:
    raise ImportError(
        "hrcsentinel required. Download here: \
		https://github.com/granttremblay/HRCsentinel")

home_directory = os.path.expanduser("~")
msid_directory = home_directory + "/Dropbox/HRCOps/MSIDCloud/"

msids = [
    "2FE00ATM",  # Front-end Temperature (c)
    "2LVPLATM",  # LVPS Plate Temperature (c)
    "2IMHVATM",  # Imaging Det HVPS Temperature (c)
    "2IMINATM",  # Imaging Det Temperature (c)
    "2SPHVATM",  # Spectroscopy Det HVPS Temperature (c)
    "2SPINATM",  # Spectroscopy Det Temperature (c)
    "2PMT1T"  ,  # PMT 1 EED Temperature (c)
    "2PMT2T"  ,  # PMT 2 EED Temperature (c)
    "2DCENTRT",  # Outdet2 EED Temperature (c)
    "2FHTRMZT",  # FEABox EED Temperature (c)
    "2CHTRPZT",  # CEABox EED Temperature (c)
    "2FRADPYT",  # +Y EED Temperature (c)
    "2CEAHVPT",  # -Y EED Temperature (c)
    "2CONDMXT",  # Conduit Temperature (c)
    "2UVLSPXT",  # Snout Temperature (c)
    "2CE00ATM",  # CEA Temperature 1 (c)
    "2CE01ATM",  # CEA Temperature 2 (c)
    "2FEPRATM",  # FEA PreAmp (c)
    "2SMTRATM",  # Selected Motor Temperature (c)
    "2DTSTATT"  # OutDet1 Temperature (c)
]


data = {}  # Instantiate an empty dictionary for all of our data

for msidname in msids:
    print("Reading DAILY MIDVALS for {}".format(msidname))
    times, values = hrc.parse_generic_msid(
        msid_directory + "{}".format(msidname) + "_daily_lifetime.csv", "midvals")
    data["{}_times".format(msidname)] = times
    data["{}_values".format(msidname)] = values

    dayslice = 30


    print("Average Temperature for {} is {} C over past {} days ({} years)".format(msidname, np.mean(values[-dayslice:]), dayslice, dayslice / 365))

hrc.styleplots()

fig, ax = plt.subplots(figsize=(16, 8))

for msidname in msids:
    ax.plot_date(data["{}_times".format(msidname)],
                 data["{}_values".format(msidname)], 'o', alpha=0.8, markersize=1.0, label='{}'.format(msidname))
    ax.set_ylabel('Temperature (C)')
    ax.set_xlabel('Date')
    ax.set_ylim(10, 40)

    ax.legend()
    #ax.set_ylim(10, 40)

plt.show()
