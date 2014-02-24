import sys, getopt
import subprocess
import os
from datetime import datetime
np = None
matplotlib = None
plt = None
import logging
logger = logging.getLogger(__name__)



def smooth(x,window_len=11,window='hanning'):
    """smooth the data using a window with requested size.
    
    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal 
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.
    
    input:
        x: the input signal 
        window_len: the dimension of the smoothing window; should be an odd integer
        window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
            flat window will produce a moving average smoothing.

    output:
        the smoothed signal
        
    example:

    t=linspace(-2,2,0.1)
    x=sin(t)+randn(len(t))*0.1
    y=smooth(x)
    
    see also: 
    
    numpy.hanning, numpy.hamming, numpy.bartlett, numpy.blackman, numpy.convolve
    scipy.signal.lfilter
 
    TODO: the window parameter could be the window itself if an array instead of a string
    NOTE: length(output) != length(input), to correct this: return y[(window_len/2-1):-(window_len/2)] instead of just y.
    """

    if x.ndim != 1:
        raise ValueError, "smooth only accepts 1 dimension arrays."

    if x.size < window_len:
        raise ValueError, "Input vector needs to be bigger than window size."


    if window_len<3:
        return x


    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"


    s=np.r_[x[window_len-1:0:-1],x,x[-1:-window_len:-1]]
    #print(len(s))
    if window == 'flat': #moving average
        w=np.ones(window_len,'d')
    else:
        w=eval('np.'+window+'(window_len)')

    y=np.convolve(w/w.sum(),s,mode='valid')
    return y

def import_pyplot():
    global np
    if np == None:
        logging.info("Importing numpy...")
        import numpy as np
    global matplotlib
    if matplotlib == None:
        logging.info("Importing matplotlib...")
        import matplotlib
        matplotlib.use('Agg')
    global plt
    if plt == None:
        logging.info("Importing pyplot...")
        import matplotlib.pyplot as plt

def plot_fft(directory, timestamp, outputfile):
    import_pyplot()
    logger.info(timestamp)
    filename = os.path.join(directory, '{0}.npz'.format(timestamp))
    data = np.load(filename)
    plt.plot(data['freqs'], data['fft'], 'x')
    plt.savefig(outputfile)


def plot(directory, timestamp, outputfile):
    datafilename = os.path.join(directory, '{0}.data'.format(timestamp))
    markerfilename = os.path.join(directory, '{0}.markers'.format(timestamp))
    logging.info("Reading input file %s", datafilename)
    with open(datafilename, "r") as f:
        t = []
        dt = []
        avg = []
        pow = []
        std = []
        for line in f:
            values = line.split(";")
            t.append(datetime.fromtimestamp(long(values[0])))
            dt.append(float(values[2]))
            avg.append(float(values[3]))
            pow.append(float(values[4]))
            std.append(float(values[5]))



    with open(markerfilename, "r") as f:
        markers = []
        for line in f:
            markers.append(line.split(";"))

    
    global plt
    if plt == None:
        logging.info("Importing pyplot...")
        import matplotlib.pyplot as plt

    std = smooth(np.array(std))
    pow = smooth(np.array(pow))
    avg = smooth(np.array(avg))
    std = std[5:len(std)-5]
    pow = pow[5:len(pow)-5]
    avg = avg[5:len(avg)-5]


    logging.info("Plotting...")
    dates = matplotlib.dates.date2num(t)
    fig, (ax1, ax2, ax3) = plt.subplots(3, sharex=True)

    ax1.plot_date(dates, std, 'b-')
    ax1.set_title('Std. dev.')
    ax1.set_ylim([0,20.0])
    ax2.plot_date(dates, pow, 'r-')
    ax2.set_title('Signal power')
    ax2.set_ylim([100,200.0])
    ax3.plot_date(dates, avg, 'g-')
    ax3.set_title('Mean')
    ax3.set_ylim([10,25.0])
    plt.gcf().autofmt_xdate()

    for timestamp, color in markers:
        t = datetime.fromtimestamp(long(timestamp))
        logger.info("Drawing marker at %s", timestamp)
        ax1.axvline(x=t, color='r')
        ax2.axvline(x=t, color='g')
        ax3.axvline(x=t, color='b')

    # ax.set_ylim(ymin=0, ymax=5000)
    logging.info("Saving output file %s", outputfile)
    fig.savefig(outputfile)      
    logging.info("Finished plotting")
