'''
TIME CONVERTERS
'''

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


'''
ARCHIVE & MSID PARSERS
'''

def parse_goes_archive(goes_data_directory):

    # The GOES data directory has some shell scripts and a README, you don't want to stack those obvi. 
    files_to_read = glob.glob(goes_data_directory + "*Gp*pchan*txt")

    allfiles = sorted(files_to_read)  # The list won't be alphanumeric. Fix that.

    master_table = stack_goes_tables(allfiles)
    
    goestimes = convert_goes_time(master_table)
    
    estrates = estimate_HRC_shieldrates(master_table)

    GOESrates = {"GOES Times": goestimes,
                 "GOES HRC Estimate 1": estrates["HRC Est. Rate 1"],
                 "GOES HRC Estimate 2": estrates["HRC Est. Rate 2"]}

    print("GOES data parsed and converted.")

    return GOESrates


def parse_orbits(spacecraft_event_directory, spacecraft_event_filename):

    # Make sure the .csv file exists before trying this:
    if os.path.isfile(spacecraft_event_directory + spacecraft_event_filename):
        msid = ascii.read(spacecraft_event_directory +
                          spacecraft_event_filename)

        print("Spacecraft orbits parsed")
    else:
        print("MSID CSV file not present")
        sys.exit(1)

    # Available fields in Orbit table:
    # start,stop,tstart,tstop,dur,orbit_num,perigee,apogee,t_perigee,
    # start_radzone,stop_radzone,dt_start_radzone,dt_stop_radzone

    # Times are given like: 2000:003:15:27:47.271, so you need to convert
    # them into an mpl date.

    radzone_entry = convert_orbit_time(msid['start_radzone'])
    radzone_exit = convert_orbit_time(msid['stop_radzone'])

    orbit = {"Radzone Entry": radzone_entry,
             "Radzone Exit": radzone_exit}

    return orbit

