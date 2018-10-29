import pandas
from datetime import datetime

def readFile(filename):
    df = pandas.read_csv(filename)
    df['timestamp'] = [datetime.utcfromtimestamp(time/float(1000)) for time in df['timestamp']]
    # Do some filtering of outliers (temp > 50, could also check that pack is not similar to others) #TODO: clarify valid ranges
    for num in ['1','2','3','4']:
        df[df['batt.temp.bus%s' % num] > 50] = None
        df[df['batt.temp.bus%s' % num] < -50] = None
    return df

def plotTime(df, sat):
    plots = df.plot(x='timestamp', y=['batt.temp.bus1', 'batt.temp.bus2', 'batt.temp.bus3', 'batt.temp.bus4'], kind='line', subplots=True, figsize=(8,8), style='.', title='Battery Pack Temperature vs Time, Satellite %s' % sat, legend=True)
    for plot in plots:
        plot.set_xlabel('Date')
        plot.set_ylabel('Temperature (C)')
        plot.axhline(y=0)
    # depending on what I'm trying to show, I might set ylim=[-10,270] (or [-10,50] and ignore the outliers) to emphasize the relative temperature differences

def plotDist(df, sat):
    bins = list(range(-30,51,5)) # set up bins for histogram
    bins[6] = 0.01 # adjust slightly so that temperature at exactly 0 show below rather than above (i.e. [-5,0.01) rather than [-5,0))
    plots = df.plot(y=['batt.temp.bus1', 'batt.temp.bus2', 'batt.temp.bus3', 'batt.temp.bus4'], kind='hist', xlim=(-30,50), bins=bins, subplots=True, sharex=False, figsize=(8,8), title='Battery Pack Temperature Distribution, Satellite %s' % sat, legend=True)
    for plot in plots:
        plot.set_xlabel('Temperature (C)')
    #TODO: better ylabels

def plotReduce(df, label):
    temps = []
    for row in df.itertuples():
        for i in range(2, 5+1): 
            if row[i]:
                temps.append((row.timestamp, row[i]))
    plot = pandas.DataFrame(temps, columns=['timestamp', 'batt.temp']).plot(x='timestamp', y='batt.temp', kind='line', style='.', legend=False, title='Battery Pack Temperature vs Time (%s)' % label)
    plot.set_ylabel('Temperature (C)')
    plot.set_xlabel('Date')
    #TODO: format better
