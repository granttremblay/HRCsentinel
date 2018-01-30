#!/proj/sot/ska/bin/python

'''Fetch mission events from the KADI Database and push them 
to Grant Tremblay's MSID Cloud on symmetry.cfa.harvard.edu


I run this with a cron job every day at 1am, from a machine 
on the HEAD network. 

This script accompanies fetch_msids.py, also run via a cron job.  
'''

from __future__ import print_function

import os
import glob
import sys
import time
import datetime

print("======= Querying KADI Database =======")

try:
    from kadi import events
except:
    print("This script can only be run from a machine on the CfA HEAD Network")
    sys.exit()


def fetch_mission_events(events_to_query):

    for item in events_to_query:
        
        event = getattr(events, "{}".format(item)) # This just calls events.eclipses, events.rad_zones, etc. 
        table = event.table
        table.write("{}_table.csv".format(item), format="csv")
        print("{} [DONE]".format(item))
        os.system("scp -q {}_table.csv grant@symmetry.cfa.harvard.edu:/Users/grant/Dropbox/HRCOps/MSIDCloud/".format(item))
        os.remove("{}_table.csv".format(item))
    print("Push to MSID Cloud [DONE]")
    print("Clean up [DONE]")


def main():

    # Time the execution of this script
    start_time = time.time()

    # The Cron daemon emails me with the command-line output. Make that useful.
    today = datetime.date.today()
    print("=======================================")
    print(today.strftime("Updating Mission Events for %d %b %Y"))
    print("=======================================")
 
    # set the working directory.
    working_dir = "/home/tremblay/MSIDs"
    os.chdir(working_dir)

    # Pick the events you want
    events = ["orbits", "dsn_comms", "dwells", "eclipses", "rad_zones", "safe_suns", "scs107s", "major_events"]

    fetch_mission_events(events)

    runtime = round(((time.time() - start_time)), 0)
    print("=======================================")
    print("  Refresh completed in {} seconds".format(runtime))
    print("=======================================")

if __name__ == '__main__':
    main()
