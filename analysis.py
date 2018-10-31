from glob import glob
from datetime import datetime, timedelta
import pandas as pd
from matplotlib import pyplot as plt
import sys
import parse

display_plots = len(sys.argv) > 1 # any command line args result in plots

# Input
filepaths = glob('./SatelliteData/satellite*.csv')
dfs  = {} # Dictionary to hold dataframes
for path in filepaths:
    print('Reading %s' % path) 
    sat = path[25:-4] # pull out the HWID
    dfs[sat] = parse.filterOutliers(parse.readFile(path))

# Time Series
for sat in sorted(dfs.keys()):
    parse.plotTime(dfs[sat], sat)
    plt.savefig('./Images/TimeSeries_Sat%s.png' % sat)
    if display_plots:
        plt.show()
    else:
        plt.clf()

## Satellite B Anomaly
parse.plotTime(dfs['B'].query("(timestamp > datetime(2016,8,19,20)) and (timestamp < datetime(2016,8,20,20))"), 'B')
plt.savefig('./Images/TimeSeries_SatB_Anomaly.png')
if display_plots:
    plt.show()
else:
    plt.clf()
## Single Cycle
ax = dfs['A'].head(75).plot(x='timestamp', 
    y=['batt.temp.bus1', 'batt.temp.bus2', 'batt.temp.bus3', 'batt.temp.bus4'], 
    title='Single Thermal Cycle, Satellite A (2017-07-17)')
ax.axhline(y=5, color='k', linestyle=':')
ax.axhline(y=10,color='k', linestyle=':')
ax.axhline(y=0, color='k')
ax.set_ylabel('Temprature (C)');
plt.savefig('./Images/TimeSeries_SatA_SingleCycle.png')
if display_plots:
    plt.show()
else:
    plt.clf()

# Temperature Distribution
for sat in sorted(dfs.keys()):
    parse.plotDist(dfs[sat], sat)
    plt.savefig('./Images/Hist_Sat%s.png' % sat)
    if display_plots:
        plt.show()
    else:
        plt.clf()

# Experiment Partioning
print('Partioning')
activeA = dfs['A'].query("timestamp >= datetime.fromisoformat('2016-07-20T23:09:46')")
inactiveA = dfs['A'].query("timestamp < datetime.fromisoformat('2016-07-20T23:09:46')")
activeB = dfs['B'].query("timestamp >= datetime.fromisoformat('2016-07-21T02:34:52')")
# Uncomment to filter out anomalous Sat. B operation
#activeB = activeB.query("(timestamp < datetime(2016,8,19,23)) or (timestamp > datetime(2016,8,20,14))")
inactiveB = dfs['B'].query("timestamp < datetime.fromisoformat('2016-07-21T02:34:52')")
active = pd.concat([activeA, activeB], keys=['A', 'B'])
inactive = pd.concat([inactiveA, inactiveB, dfs['C']], keys=['A', 'B', 'C'])
## Active
print('Consolidating')
active_reduced = parse.reduce(active)
parse.plotReduced(active_reduced, 'High Threshold Test')
plt.savefig('./Images/Hist_Reduced_Active.png')
plt.figure(1)
plt.savefig('./Images/TimeSeries_Reduced_Active.png')
if display_plots:
    plt.show()
else:
    plt.clf()

## Inactive
inactive_reduced = parse.reduce(inactive)
parse.plotReduced(inactive_reduced, 'Low Threshold Baseline')
plt.savefig('./Images/Hist_Reduced_Inactive.png')
plt.figure(1)
plt.savefig('./Images/TimeSeries_Reduced_Inactive.png')
if display_plots:
    plt.show()
else:
    plt.clf()
## Comparision
print('\nResults:')
count_act_below   = len(active_reduced.query("satA < 0 or satB < 0"))
count_act_total   = len(active_reduced)
act_percent = 100 * count_act_below / float(count_act_total)
print('Count Active <= 0C: \t%d(/%d, %.2f%%)' % (count_act_below, count_act_total, act_percent))
count_inact_below   = len(inactive_reduced.query("satA < 0 or satB < 0 or satC < 0"))
count_inact_total   = len(inactive_reduced)
inact_percent = 100 * count_inact_below / float(count_inact_total)
print('Count Inactive <= 0C: \t%d(/%d, %.2f%%)' % (count_inact_below, count_inact_total, inact_percent))
decrease = 100 * (act_percent - inact_percent) / inact_percent
print('Effect of threshold change: %.2f%%' % decrease)
## Time below 0C
active_freezetime = timedelta()
active_tottime = timedelta()
active_count = 0
for sat in ['A', 'B']:
    count, freezetime = parse.countCycles(active.loc[sat], 0, 0)
    active_count += count
    active_freezetime += freezetime
    active_tottime += active.loc[sat].iloc[-1]['timestamp'] - active.loc[sat].iloc[0]['timestamp']
print('Time Below Freezing (High Thresholds):\n\t%d excursions,\n\t%.2f battery hours(/%.2f total battery hours, %.2f%%),\n\tavg. excursion %.0f minutes' \
     % (active_count, active_freezetime.total_seconds()/float(60*60), \
        4*active_tottime.total_seconds()/float(60*60), 100*active_freezetime/(4*active_tottime), \
        active_freezetime.total_seconds()/(60*active_count)))
inactive_freezetime = timedelta()
inactive_tottime = timedelta()
inactive_count = 0
for sat in ['A', 'B', 'C']:
    count, freezetime = parse.countCycles(inactive.loc[sat], 0, 0)
    inactive_count += count
    inactive_freezetime += freezetime
    inactive_tottime += inactive.loc[sat].iloc[-1]['timestamp'] - inactive.loc[sat].iloc[0]['timestamp']
print('Time Below Freezing (Low Thresholds):\n\t%d excursions,\n\t%.2f battery hours(/%.2f total battery hours, %.2f%%),\n\tavg. excursion %.0f minutes' \
     % (inactive_count, inactive_freezetime.total_seconds()/float(60*60), \
        4*inactive_tottime.total_seconds()/float(60*60), 100*inactive_freezetime/(4*inactive_tottime), \
        inactive_freezetime.total_seconds()/(60*inactive_count)))
## Time w/ heater on
active_ontime = timedelta()
active_time = timedelta()
active_count = 0
for sat in ['A', 'B']:
    count, ontime = parse.countCycles(active.loc[sat], 11, 16)
    active_count += count
    active_ontime += ontime
    active_time += active.loc[sat].iloc[-1]['timestamp'] - active.loc[sat].iloc[0]['timestamp']
print('Patch Heater (High Thresholds):\n\t%d cycles over %s\n\t%.2f cycles per heater per day,\n\tapprox. %.2f%% duty cycle, or %.2f hours per heater per day' \
        % (active_count, str(active_time), \
           24*60*60*active_count/(4*active_time.total_seconds()), \
           100*active_ontime/(4*active_time), 24*active_ontime/(4*active_time)))
inactive_ontime = timedelta()
inactive_time = timedelta()
inactive_count = 0
for sat in ['A', 'B', 'C']:
    count, ontime = parse.countCycles(inactive.loc[sat], 5, 10)
    inactive_count += count
    inactive_ontime += ontime
    inactive_time += inactive.loc[sat].iloc[-1]['timestamp'] - inactive.loc[sat].iloc[0]['timestamp']
print('Patch Heater (Low Thresholds):\n\t%d cycles over %s\n\t%.2f cycles per heater per day,\n\tapprox. %.2f%% duty cycle, or %.2f hours per heater per day' \
        % (inactive_count, str(inactive_time), \
           24*60*60*inactive_count/(4*inactive_time.total_seconds()), \
           100*inactive_ontime/(4*inactive_time), 24*inactive_ontime/(4*inactive_time)))
