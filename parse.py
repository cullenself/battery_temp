from datetime import datetime, timedelta
from statistics import median
import pandas

# Histogram Bins
BINS = list(range(-30, 51, 5)) # set up bins for histogram
BINS[6] = 0.01 # adjust slightly so that temperature at exactly 0 show below rather than above (i.e. [-5,0.01) rather than [-5,0))
# Outlier Filtering
INNER_BOUND = 15 # max acceptable difference between bus temps for a single epoch
OUTER_BOUND = 5  # max acceptable change for a single bus between epochs

# Create Pandas DataFrame from CSV data
def readFile(filename):
    df = pandas.read_csv(filename)
    df['timestamp'] = [datetime.utcfromtimestamp(time/float(1000)) for time in df['timestamp']]
    return df

# Filter outliers from data (jumps in temp between readings, bus doesn't agree with other temps)
def filterOutliers(df, IB=INNER_BOUND, OB=OUTER_BOUND):
    prev_temp = [None] * 4
    for i, row in df.iterrows():
        if row['sc.bootcount'] > 0:
            prev_temp = [None] * 4 # reset temperatures
            continue # no temp readings so skip row
        else:
            # Check for self-consistency
            curr_temp = [row['batt.temp.bus1'], row['batt.temp.bus2'], row['batt.temp.bus3'], row['batt.temp.bus4']]
            curr_temp_median = median(curr_temp)
            for v in [max(curr_temp), min(curr_temp)]:
                if abs(v - curr_temp_median) > IB:
                    bus_num = curr_temp.index(v) + 1
                    df.at[i, 'batt.temp.bus%d' % bus_num] = None
                    curr_temp[bus_num-1] = None

            # Check for jumps between readings
            for bus_num in [1, 2, 3, 4]:
                if ((prev_temp[bus_num-1]) and (curr_temp[bus_num-1])): # Can Compare
                    if abs(prev_temp[bus_num-1] - curr_temp[bus_num-1]) > OB:
                        df.at[i, 'batt.temp.bus%d' % bus_num] = None # mark data as invalid
                        curr_temp[bus_num-1] = None
            prev_temp = curr_temp
    return df

# Create a time series plot for each bus on a single satellite
def plotTime(df, sat):
    axs = df.plot(x='timestamp',
                  y=['batt.temp.bus1', 'batt.temp.bus2', 'batt.temp.bus3', 'batt.temp.bus4'],
                  kind='line', subplots=True, figsize=(12, 12), style='.',
                  title='Battery Pack Temperature vs Time, Satellite %s' % sat, legend=True)
    for ax in axs:
        ax.set_xlabel('Date')
        ax.set_ylabel('Temperature (C)')
        ax.axhline(y=0, color='k')

# Create a histogram for all readings from a single satellite
def plotDist(df, sat):
    ax = df.plot(y=['batt.temp.bus1', 'batt.temp.bus2', 'batt.temp.bus3', 'batt.temp.bus4'],
                 kind='hist', xlim=(-30, 50), bins=BINS, stacked=True, figsize=(8, 8),
                 title='Battery Pack Temperature Distribution, Satellite %s' % sat, legend=True)
    ax.set_xlabel('Temperature (C)')

def reduce(df):
    col = 'batt.temp.bus%d'
    temps = []
    for i, row in df.iterrows():
        for bus_num in [1, 2, 3, 4]: 
            temps.append({'timestamp': row['timestamp'], 'sat%s' % i[0]: row[col % bus_num]})
    df = pandas.DataFrame(temps)
    return df.dropna(thresh=2) # drop if both rows are NaN

# Plot time series and histogram of reduced data
def plotReduced(df, label):
    sats = list(df.columns) # e.g. ['timestamp', 'satA', 'satB', ('satC', maybe) ]
    sats.remove('timestamp')

    # Time series
    ax = df.plot(x='timestamp', y=sats, kind='line', style='.', alpha=0.5,
                 title='Battery Pack Temperature vs Time (%s)' % label, legend=True)
    ax.set_ylabel('Temperature (C)')
    ax.set_xlabel('Date')
    ax.axhline(y=0, color='k')
    # Histogram
    ax = df.plot(y=sats, kind='hist', xlim=(-30, 50), bins=BINS, density=True,
                 title='Battery Pack Temperature Distribution (%s)' % label, legend=True)
    ax.set_ylabel('Frequency (%)')
    ax.set_xlabel('Temperature (C)')

# Count transitions (either heater on/off events, or dropping below/above 0C)
def countCycles(df, low_thresh, high_thresh):
    col = 'batt.temp.bus%d'
    heater = [False] * 4 # True => Heater On, False => Heater Off
    count = 0
    tot_time_on = timedelta()
    time_on = [None] * 4
    for _, row in df.iterrows():
        if row['sc.bootcount'] > 0: # Reboot event resets flags, and saves current times
            for bus in [1, 2, 3, 4]:
                if heater[bus-1]:
                    heater[bus-1] = False
                    tot_time_on += row['timestamp'] - time_on[bus-1]
            continue
        for bus in [1, 2, 3, 4]:
            if heater[bus-1]: # if active
                if row[col % bus] > high_thresh: # and exit active range
                    heater[bus-1] = False # set unactive
                    tot_time_on += row['timestamp'] - time_on[bus-1] # store active time
            if not heater[bus-1]: # if not active
                if row[col % bus] < low_thresh: # and enter active range
                    heater[bus-1] = True # set active
                    time_on[bus-1] = row['timestamp'] # store turn on time
                    count += 1 # bump counter
    return count, tot_time_on
