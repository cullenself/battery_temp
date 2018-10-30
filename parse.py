import pandas
from datetime import datetime
from statistics import median

# Histogram Bins
BINS = list(range(-30,51,5)) # set up bins for histogram
BINS[6] = 0.01 # adjust slightly so that temperature at exactly 0 show below rather than above (i.e. [-5,0.01) rather than [-5,0))
# Outlier Filtering
INNER_BOUND = 15 # max acceptable difference between bus temps for a single epoch
OUTER_BOUND = 5  # max acceptable change for a single bus between epochs

def readFile(filename):
    df = pandas.read_csv(filename)
    df['timestamp'] = [datetime.utcfromtimestamp(time/float(1000)) for time in df['timestamp']]
    # Do some filtering of outliers (temp > 50, could also check that pack is not similar to others) #TODO: clarify valid ranges
    prev_temp = [None] * 4
    for i, row in df.iterrows():
        if (row['sc.bootcount'] > 0): 
            prev_temp = [None] * 4 # reset temperatures
            continue # no temp readings so skip row
        else:
            curr_temp = [row['batt.temp.bus1'], row['batt.temp.bus2'], row['batt.temp.bus3'], row['batt.temp.bus4']]
            curr_temp_median = median(curr_temp)
            for v in [max(curr_temp), min(curr_temp)]:
                if (abs(v - curr_temp_median) > INNER_BOUND):
                    bus_num = curr_temp.index(v) + 1 
                    df.at[i, 'batt.temp.bus%d' % bus_num] = None
                    curr_temp[bus_num-1] = None

            for bus_num in [1, 2, 3, 4]:
                if ((prev_temp[bus_num-1]) and (curr_temp[bus_num-1])): # Can Compare
                    if (abs(prev_temp[bus_num-1] - curr_temp[bus_num-1]) > OUTER_BOUND):
                        df.at[i, 'batt.temp.bus%d' % bus_num] = None # mark data as invalid
                        curr_temp[bus_num-1] = None
            prev_temp = curr_temp
    return df

def plotTime(df, sat):
    axs = df.plot(x='timestamp', y=['batt.temp.bus1', 'batt.temp.bus2', 'batt.temp.bus3', 'batt.temp.bus4'], kind='line', subplots=True, figsize=(12,12), style='.', title='Battery Pack Temperature vs Time, Satellite %s' % sat, legend=True)
    for ax in axs:
        ax.set_xlabel('Date')
        ax.set_ylabel('Temperature (C)')
        ax.axhline(y=0, color='k')

def plotDist(df, sat):
    axs = df.plot(y=['batt.temp.bus1', 'batt.temp.bus2', 'batt.temp.bus3', 'batt.temp.bus4'], kind='hist', xlim=(-30,50), bins=BINS, subplots=True, sharex=False, figsize=(8,8), title='Battery Pack Temperature Distribution, Satellite %s' % sat, legend=True)
    for ax in axs:
        ax.set_xlabel('Temperature (C)')
    #TODO: better ylabels

def plotReduce(df, label):
    temps = []
    for row in df.itertuples():
        for i in range(2, 5+1): 
            if row[i]:
                temps.append((row.timestamp, row[i]))
    df = pandas.DataFrame(temps, columns=['timestamp', 'batt.temp'])
    ax = df.plot(x='timestamp', y='batt.temp', kind='line', style='.', legend=False, title='Battery Pack Temperature vs Time (%s)' % label)
    ax.set_ylabel('Temperature (C)')
    ax.set_xlabel('Date')
    ax.axhline(y=0, color='k')

    ax = df.plot(y='batt.temp', kind='hist', xlim=(-30,50), bins=BINS, density=True, title='Battery Pack Temperature Distribution (%s)' % label, legend=False)
    ax.set_ylabel('Frequency (%)')
    ax.set_xlabel('Temperature (C)')
    return df
