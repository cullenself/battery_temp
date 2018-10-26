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
    df.plot(x='timestamp', y=['batt.temp.bus1', 'batt.temp.bus2', 'batt.temp.bus3', 'batt.temp.bus4'], kind='line', subplots=True, figsize=(8,8), style='.', title='Battery Pack Temperature vs Time, Satellite %s' % sat, legend=True)
    # depending on what I'm trying to show, I might set ylim=[-10,270] (or [-10,50] and ignore the outliers) to emphasize the relative temperature differences

def plotDist(df, sat):
    df.plot(y=['batt.temp.bus1', 'batt.temp.bus2', 'batt.temp.bus3', 'batt.temp.bus4'], kind='hist', xlim=(-30,50), subplots=True, figsize=(8,8), title='Battery Pack Temperature Distribution, Satellite %s' % sat, legend=True)
    #TODO: make smaller boxes, more ticks
