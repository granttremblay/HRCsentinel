import os

import datetime as dt

from astropy.io import fits
from astropy.io import ascii
from astropy.table import Table

import matplotlib.pyplot as plt
from matplotlib import dates

import numpy as np
from scipy.interpolate import spline

from hrcsentinel import hrccore as hrc


print("Forecasting HRC Thermals based upon latest trends")

# Establish location of MSIDs, fetched by HRCsentinel, as well as the directory you'd like to save figures in.

showfigs = False

home_directory = os.path.expanduser("~")
msid_directory = home_directory + "/Dropbox/HRCOps/MSIDCloud/"

figure_save_directory = home_directory + "/Dropbox/HRCOps/ThermalForecasts/"

# Thermistor MSIDs we care about:


print("Updated plots and tables will be written to {}".format(figure_save_directory))

msids = [
    "2FE00ATM",  # Front-end Temperature (c)
    "2LVPLATM",  # LVPS Plate Temperature (c)
    "2IMHVATM",  # Imaging Det HVPS Temperature (c)
    "2IMINATM",  # Imaging Det Temperature (c)
    "2SPHVATM",  # Spectroscopy Det HVPS Temperature (c)
    "2SPINATM",  # Spectroscopy Det Temperature (c)
    "2PMT1T",  # PMT 1 EED Temperature (c)
    "2PMT2T",  # PMT 2 EED Temperature (c)
    "2DCENTRT",  # Outdet2 EED Temperature (c)
    "2FHTRMZT",  # FEABox EED Temperature (c)
    "2CHTRPZT",  # CEABox EED Temperature (c)
    "2FRADPYT",  # +Y EED Temperature (c)
    "2CEAHVPT",  # -Y EED Temperature (c)
    "2CONDMXT",  # Conduit Temperature (c)
    "2UVLSPXT",  # Snout Temperature (c)
    #"2CE00ATM",  # CEA Temperature 1 (c) THESE HAVE FEWER POINTS AS THEY WERE RECENTLY ADDED BY TOM
    #"2CE01ATM",  # CEA Temperature 2 (c) THESE HAVE FEWER POINTS AS THEY WERE RECENTLY ADDED BY TOM
    "2FEPRATM",  # FEA PreAmp (c)
    # "2SMTRATM",  # Selected Motor Temperature (c) THIS IS ALWAYS 5 DEGREES THROUGHOUT ENTIRE MISSION
    "2DTSTATT"   # OutDet1 Temperature (c)
]

data = {}

valtype = "means"

print("Reading MSIDs from MSIDCloud")
for msidname in msids:
    #print("Reading DAILY {} for {}".format(valtype.upper(), msidname))
    times, values = hrc.parse_generic_msid(
        msid_directory + "{}".format(msidname) + "_daily_lifetime.csv", valtype)
    data["{}_times".format(msidname)] = times
    data["{}_values".format(msidname)] = values


# You can compute 30 day means and write it to a sortable table like this:

# In[7]:


ave_table = Table()

all_names = []
all_means = []
all_stds = []


for msidname in msids:
    daybin = 100  # number of days over which to average the daily averages
    mean = np.mean(data["{}_values".format(msidname)][-daybin:]).round(2)
    std = np.std(data["{}_values".format(msidname)][-daybin:]).round(2)

    all_names.append(msidname)
    all_means.append(mean)
    all_stds.append(std)

ave_table["MSIDName"] = all_names
ave_table["Average".format(daybin)] = all_means
ave_table["STD"] = all_stds


# In[8]:


ave_table.show_in_notebook


# Sort the table in ascending order by Average temperature, so that we can make a pretty sequential plot later

# In[9]:


ave_table.sort("Average")
ave_table


# Now create a REORDERED list of MSID names, ordered by increasing average temperature, in order to make pretty sequential color cycles

# In[10]:


ordered_msidlist = ave_table["MSIDName"]


# We can plot all MSIDs together, like this:

# In[11]:


figure_savename = figure_save_directory + "all_msids_figure.pdf"
# Make this True to ensure the file size is small. Otherwise you're plotting thousands of vector points.
rasterized = True

fig, ax = plt.subplots(figsize=(12, 8))

n_lines = len(ordered_msidlist)
color_idx = np.linspace(0, 1, n_lines)


for i, msidname in zip(color_idx, ordered_msidlist):
    ax.plot_date(data["{}_times".format(msidname)],
                 data["{}_values".format(msidname)], '.', alpha=1.0, markersize=2.5, label='{}'.format(msidname), color=plt.cm.RdBu_r(i), rasterized=rasterized)
    ax.set_ylabel('Temperature (C)')
    ax.set_xlabel('Date')
    ax.set_ylim(0, 40)

    ax.set_title("HRC Thermistor Temperatures over Mission Lifetime")
    # ax.legend()
    #ax.set_ylim(10, 40)


ax.legend(loc=2, prop={'size': 13})

if showfigs is True:
    plt.show()

fig.savefig(figure_savename, dpi=300)


# We can also easily take a yearly (i.e. 365 day window) moving average to smooth this out. This is effectively an efficient convolution.

# In[12]:


window = 365  # days, i.e. a year


# In[13]:


def compute_yearly_average(values, window):

    array = values

    cumulative_sum, moving_aves = [0], []

    for i, x in enumerate(array, 1):
        cumulative_sum.append(cumulative_sum[i - 1] + x)
        if i >= window:
            moving_ave = (cumulative_sum[i] -
                          cumulative_sum[i - window]) / window
            # can do stuff with moving_ave here
            moving_aves.append(moving_ave)

    # This does not preserve array size, reducing its length by N-1 values.
    # We can be lazy and simply pad it to ensure it has the same value

    #np.pad(moving_aves, values, mode='constant', constant_values=(np.nan,))

    return moving_aves


# Run this function in a loop to compute and plot all moving averages

# In[14]:


all_trends = {}

for msidname in msids:
    moving_aves = compute_yearly_average(
        data["{}_values".format(msidname)], window)
    all_trends["{}_trend".format(msidname)] = moving_aves


# This, of course, does not preserve array size - it cuts off the first 364 datapoints if your window is 365 days

# In[15]:


len(data["2UVLSPXT_times"]) - len(all_trends["2UVLSPXT_trend"])


# But we can be super lazy and just fix this on-the-fly, e.g.

# In[16]:


time_corrector = window - 1


# In[17]:


len(data["2UVLSPXT_times"][time_corrector:]) - \
    len(all_trends["2UVLSPXT_trend"])


# Good!

# In[18]:


figure_savename = figure_save_directory + "trend_plus_realdata_comparison.pdf"
# Make this True to ensure the file size is small. Otherwise you're plotting thousands of vector points.
rasterized = True

hrc.styleplots()
fig, ax = plt.subplots(figsize=(12, 8))

ax.plot_date(data["2SPHVATM_times"], data["2SPHVATM_values"],
             '.', markersize=2, color='gray', rasterized=rasterized)
ax.plot_date(data["2SPHVATM_times"][time_corrector:],
             all_trends["2SPHVATM_trend"], '-', lw=3, rasterized=rasterized)

ax.set_ylabel("Temperature (C)")
ax.set_xlabel("Date")

ax.set_title("Only the first year of data is cut off. No big deal!")

if showfigs is True:
    plt.show()

fig.savefig(figure_savename, dpi=300)


# In[19]:


figure_savename = figure_save_directory + "all_trends_lifetime.pdf"
# Make this True to ensure the file size is small. Otherwise you're plotting thousands of vector points.
rasterized = True

hrc.styleplots()
fig, ax = plt.subplots(figsize=(12, 8))

n_lines = len(msids)
color_idx = np.linspace(0, 1, n_lines)

names = ave_table['MSIDName']


for i, msidname in zip(color_idx, names):
    #ax.plot(all_trends["{}_trend".format(msidname)], lw=3.0, label=msidname, color=plt.cm.coolwarm(i))
    ax.plot_date(data["{}_times".format(msidname)][364:], all_trends["{}_trend".format(
        msidname)], '-', label='{}'.format(msidname), lw=3.0, color=plt.cm.RdBu_r(i), rasterized=rasterized)


ax.legend(loc=0, prop={'size': 13})

ax.set_title("Moving Average HRC Thermistor Temperatures over Mission Lifetime")
ax.set_ylabel("Temperature (C)")
ax.set_xlabel("Date")

if showfigs is True:
    plt.show()

fig.savefig(figure_savename, dpi=300)


# The slope has clearly been pretty constant (and roughly the same for all thermistors!) over the past twoish years, i.e. Oct. 2015 - now:

# In[20]:


figure_savename = figure_save_directory + "all_trends_recent.pdf"
# Make this True to ensure the file size is small. Otherwise you're plotting thousands of vector points.
rasterized = True

hrc.styleplots()
fig, ax = plt.subplots(figsize=(12, 8))

n_lines = len(msids)
color_idx = np.linspace(0, 1, n_lines)

names = ave_table['MSIDName']


for i, msidname in zip(color_idx, names):
    #ax.plot(all_trends["{}_trend".format(msidname)], lw=3.0, label=msidname, color=plt.cm.coolwarm(i))
    ax.plot_date(data["{}_times".format(msidname)][time_corrector:], all_trends["{}_trend".format(
        msidname)], '-', label='{}'.format(msidname), lw=3.0, color=plt.cm.RdBu_r(i), rasterized=rasterized)


ax.legend(prop={'size': 13})

ax.set_title("Moving Average HRC Thermistor Temperatures over Past Few Years")
ax.set_ylabel("Temperature (C)")
ax.set_xlabel("Date")

# By eye, this is roughly the time of the slope change
inflection = dt.date(2014, 11, 15)

ax.set_xlim(dt.date(2014, 1, 1), dt.date(2018, 4, 1))
ax.set_ylim(10, 35)

ax.axvline(inflection, color='gray')

if showfigs is True:
    plt.show()

fig.savefig(figure_savename, dpi=300)


# `inflection` is the datetime of the vertical line above. Lets find the nearest index that corresponds to that date, so that we can compute clean slopes starting at that index, toward the end of each trend array.

# In[21]:


def find_index_at_date(array, value):
    '''
    Given an input array, find the index of the item in that array closest to the given value
    '''
    index = (np.abs(array - value)).argmin()
    return index


# In[22]:


start_index = find_index_at_date(
    data["2UVLSPXT_times"][time_corrector:], dates.date2num(inflection))
start_index


# Now we can calculate the slopes of every thermistor over this time interval. We can easily do this with `numpy.polyfit()`.

# In[23]:


def fit_slope(x, y):
    coeffs = np.polyfit(x, y, deg=1)
    # for a deg=1 (linear) polynomial, m, b = coeffs[0], coeffs[1] in y = mx + b

    return coeffs


# Check that it works.

# In[24]:


fit_slope(data["2UVLSPXT_times"][time_corrector:][start_index:],
          all_trends["2UVLSPXT_trend"][start_index:])


# Compute coefficients for all MSIDs:

# In[25]:


all_coeffs = {}  # instantiate an emtpy dictionary to hold these

print("Calculating coefficients for every MSID")
for msidname in names:
    coeffs = fit_slope(data["{}_times".format(msidname)][time_corrector:]
                       [start_index:], all_trends["{}_trend".format(msidname)][start_index:])
    # print("Slope and Intercept for {} are {}, adding to all_coeffs dictionary.".format(
    #     msidname, coeffs))
    all_coeffs["{}".format(msidname)] = coeffs


# In[26]:


years_to_forecast = 10
daypad = years_to_forecast * 365
future_timerange = np.arange(dates.date2num(
    inflection), dates.date2num(inflection) + daypad, 10)


# In[27]:


figure_savename = figure_save_directory + "slope_plot.pdf"
# Make this True to ensure the file size is small. Otherwise you're plotting thousands of vector points.
rasterized = True

hrc.styleplots()
fig, ax = plt.subplots(figsize=(12, 8))

n_lines = len(msids)
color_idx = np.linspace(0, 1, n_lines)

names = ave_table['MSIDName']


for i, msidname in zip(color_idx, names):
    ax.plot(future_timerange, all_coeffs["{}".format(
        msidname)][0] * future_timerange + all_coeffs["{}".format(msidname)][1], '-', color='gray')
    ax.plot_date(data["{}_times".format(msidname)][364:][start_index:], all_trends["{}_trend".format(
        msidname)][start_index:], '-', lw=3.0, label='{}'.format(msidname), color=plt.cm.coolwarm(i), rasterized=rasterized)


ax.legend(prop={'size': 13})

ax.set_title("Moving Average HRC Thermistor Temperatures over Past Few Years")
ax.set_ylabel("Temperature (C)")
ax.set_xlabel("Date")

# By eye, this is roughly the time of the slope change
inflection = dt.date(2014, 11, 15)

ax.set_xlim(dt.date(2014, 1, 1), dt.date(2018, 4, 1))
ax.set_ylim(10, 35)

ax.axvline(inflection, color='gray')

if showfigs is True:
    plt.show()

fig.savefig(figure_savename, dpi=300)


# In[62]:


figure_savename = figure_save_directory + "all_trends_and_slopes_lifetime.pdf"
# Make this True to ensure the file size is small. Otherwise you're plotting thousands of vector points.
rasterized = True

hrc.styleplots()
fig, ax = plt.subplots(figsize=(12, 8))

n_lines = len(msids)
color_idx = np.linspace(0, 1, n_lines)

names = ave_table['MSIDName']


for i, msidname in zip(color_idx, names):
    ax.plot(future_timerange, all_coeffs["{}".format(
        msidname)][0] * future_timerange + all_coeffs["{}".format(msidname)][1], '-', color='gray')
    ax.plot(future_timerange, coeffs[0] *
            future_timerange + coeffs[1], color='gray')
    ax.plot_date(data["{}_times".format(msidname)][364:], all_trends["{}_trend".format(
        msidname)], '-', lw=3.0, label='{}'.format(msidname), color=plt.cm.RdBu_r(i), rasterized=rasterized)


ax.legend(loc=2, prop={'size': 13})

ax.set_title("Forecasted HRC Thermistor Temperatures if Current Slopes Hold")
ax.set_ylabel("Temperature (C)")
ax.set_xlabel("Date")

ax.axvline(inflection, color='gray')

if showfigs is True:
    plt.show()

fig.savefig(figure_savename, dpi=300)


print("All plots updated")

# #### Forecasts

# Finally, we can make some (very simple) projections, under the (almost assuredly incorrect) assumption that the current (i.e. ~2 year) slope holds for the next 10 years. This will very likely not be the case. But it's still a useful exercise, and probably not *too* far off. Ralph, Dan, and Paul will have good thoughts on this, too.

# In[57]:

print("Creating forecast table based upon latest slopes")

def forecast_future_temp(year, msidname, coeffs):

    # Find the index of the future timeline at given year
    timeline = np.arange(dates.date2num(dt.datetime(2016, 1, 1)),
                         dates.date2num(dt.datetime(2035, 1, 1)), 10)
    index = find_index_at_date(
        timeline, dates.date2num(dt.datetime(year, 1, 1)))

    # Forecast the temperature using the best-fit line
    future_temp = (coeffs[0] * timeline[index] + coeffs[1]).round(2)

    #print("{} in {} at {} degrees C.".format(msidname, year, future_temp))
    # print("{}".format(future_temp))
    return future_temp


# In[59]:


namecolumn = names
forecasts = {}

years_to_forecast = [2018, 2020, 2022, 2024, 2026, 2028, 2030]

for year in years_to_forecast:
    #     print("\nForecasting for {}".format(year))
    #     print("--------------------")

    templist = []
    for msidname in names:
        temp = forecast_future_temp(
            year, msidname, all_coeffs["{}".format(msidname)])
        templist.append(temp)
    forecasts["{}".format(year)] = templist


# Let's create a clean Astropy table of these forecasts for easier portability, etc.

# In[60]:


forecast_table = Table()

forecast_table["MSID Names"] = namecolumn
forecast_table["2018"] = forecasts["2018"]
forecast_table["2020"] = forecasts["2020"]
forecast_table["2022"] = forecasts["2022"]
forecast_table["2024"] = forecasts["2024"]
forecast_table["2026"] = forecasts["2026"]
forecast_table["2028"] = forecasts["2028"]
forecast_table["2030"] = forecasts["2030"]


# In[61]:


forecast_table


# Save this as FITS and ASCII tables.

# In[54]:


forecast_table_fits = fits.BinTableHDU(data=forecast_table)
forecast_table_fits.writeto(
    figure_save_directory + "forecast_table.fits", overwrite=True)

ascii.write(forecast_table, figure_save_directory +
            "forecast_table.txt", overwrite=True)

print("Done")
