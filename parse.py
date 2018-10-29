import pandas
from datetime import datetime

# Histogram Bins
BINS = list(range(-30,51,5)) # set up bins for histogram
BINS[6] = 0.01 # adjust slightly so that temperature at exactly 0 show below rather than above (i.e. [-5,0.01) rather than [-5,0))

def readFile(filename):
    df = pandas.read_csv(filename)
    df['timestamp'] = [datetime.utcfromtimestamp(time/float(1000)) for time in df['timestamp']]
    # Do some filtering of outliers (temp > 50, could also check that pack is not similar to others) #TODO: clarify valid ranges
    for num in ['1','2','3','4']:
        df[df['batt.temp.bus%s' % num] > 50] = None
        df[df['batt.temp.bus%s' % num] < -50] = None
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
