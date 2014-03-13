import sys, getopt
import subprocess
import os
from datetime import datetime
from shared import read_config
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

def plot_fft(session_dir, image_dir, timestamp):
    import_pyplot()
    inputfilename = os.path.join(session_dir, '{0}.npz'.format(timestamp))
    outputfilename = os.path.join(image_dir, '{0}.png'.format(timestamp))

    logger.info("Reading input file...")
    npz = np.load(inputfilename)
    t = npz['t']
    dt = np.average(np.gradient(t)) / 1000.0
    data = npz['data']
    x = data[:,0]
    y = data[:,1]
    z = data[:,2]
    w = np.sqrt(x*x+y*y+z*z)
    w = w - np.average(w)
    abs = np.abs(w)
    avg = np.mean(abs)
    std = np.std(w)

    starttime = datetime.fromtimestamp(long(timestamp))
    duration = (t[-1]-t[0]) / 1000
    endtime = datetime.fromtimestamp(long(timestamp) + duration)
    header = "Session recorded {0} {1}-{2}".format(
        starttime.strftime('%a %d.%m.%Y'),
        starttime.strftime('%H:%M:%S'),
        endtime.strftime('%H:%M:%S'))

    window_len = 101
    snip = (window_len-1)/2
    window = 'hanning'

    x = smooth(x,window_len=window_len, window=window)
    y = smooth(y,window_len=window_len, window=window)
    z = smooth(z,window_len=window_len, window=window)
    ws = smooth(w,window_len=window_len, window=window)
    x = x[snip:len(x)-snip]
    y = y[snip:len(y)-snip]
    z = z[snip:len(z)-snip]
    ws = ws[snip:len(ws)-snip]
    wd = np.gradient(ws)

    #wsub = w - ws
    #window_len = 51
    #snip = (window_len-1)/2
    #wsub = smooth(wsub,window_len=window_len, window=window)
    #wsub = wsub[snip:len(wsub)-snip]

    spec = np.fft.fft(ws)
    ps = np.abs(spec)**2
    freq = np.fft.fftfreq(t.shape[-1], dt)
    #ps = ps[0:len(ps)/2]
    #freq = freq[0:len(freq)/2]

    index = np.argmax(ps)
    pow = ps[index]
    if pow > 200000:
        f = np.abs(freq[index] * 60)
    else:
        f = None

    logger.info("Plotting...")
    major = matplotlib.ticker.MultipleLocator(0.5)
    minor = matplotlib.ticker.MultipleLocator(0.1)
    fig, (ax1, ax2) = plt.subplots(2)
    fig.suptitle(header)
    ax1.plot(t, ws)
    ax1.set_ylim([-5,5])
    ax2.plot(freq, ps)
    ax2.set_xlim([0,1])
    ax2.set_ylim([0,1000000])
    ax2.xaxis.set_major_locator(major)
    ax2.xaxis.set_minor_locator(minor)
    ax2.axvline(x=np.abs(freq[index]), color='b')
    ax2.text(0.5, 300000, 
        "Breath freq {0}\nAvg {1}\nStd {2}"
        .format(f, avg, std))
    logger.info("Saving image...")
    plt.savefig(outputfilename)
    

def plot_histogram(session_dir, image_dir, timestamp):
    import_pyplot()
    outputfilename = os.path.join(image_dir, '{0}.hist.png'.format(timestamp))
    datafilename = os.path.join(session_dir, '{0}.data'.format(timestamp))
    logging.info("Reading input file %s", datafilename)
    with open(datafilename, "r") as f:
        t = []
        dt = []
        std = []
        for line in f:
            values = line.split(";")
            t.append(datetime.fromtimestamp(long(values[0])))
            dt.append(float(values[2]))
            std.append([float(values[i]) for i in [5,8,11]])
    std = np.array(std)
    std = np.array([np.sqrt(row.dot(row)) for row in std])
    starttime = datetime.fromtimestamp(long(timestamp))
    endtime = datetime.fromtimestamp(long(values[0])) #Last row recorded
    header = "Session recorded {0} {1}-{2}".format(
        starttime.strftime('%a %d.%m.%Y'),
        starttime.strftime('%H:%I'),
        endtime.strftime('%H:%I'))

    n, bins, patches = plt.hist(std, 10)
    print "n: ", n
    print "bins: ", bins
    print "patches", patches
 
    logging.info("Saving output file %s", outputfilename)
    plt.savefig(outputfilename)
    logging.info("Finished plotting")

def get_bands():
    prefs = read_config()
    b = prefs.get('recorder', 'bands').split(';')
    m = prefs.get('recorder', 'multipliers').split(';')
    b = [float(x) for x in b]
    m = [float(x) for x in m]
    b.append(10000.0)
    return [[b[i], b[i+1]-(b[i+1]-b[i])/2, m[i]] for i in range(len(b)-1)]


def read_input_file(filename):
    logging.info("Reading data file %s", filename)
    t = []
    n = []
    dt = []
    avg = []
    std = []
    breath = []
    with open(filename, "r") as f:
        for line in f:
            values = line.split(";")
            t.append(datetime.fromtimestamp(long(values[0])))
            n.append(int(values[1]))
            dt.append(float(values[2]))
            avg.append(float(values[3]))
            std.append(float(values[4]))
            breath.append(float(values[5]))
    logger.info("Finished reading data file.")
    return [t, n, dt, avg, std, breath]

def read_marker_file(filename):
    logging.info("Reading marker file %s", filename)
    with open(filename, "r") as f:
        markers = []
        for line in f:
            markers.append(line.split(";"))
    logging.info("Read %s markers.", len(markers))
    return markers
    
def plot(session_dir, image_dir, timestamp, plot_axes=False, smooth_data=False):
    import_pyplot()
    outputfilename = os.path.join(image_dir, '{0}.png'.format(timestamp))
    datafilename = os.path.join(session_dir, '{0}.data'.format(timestamp))
    markerfilename = os.path.join(session_dir, '{0}.markers'.format(timestamp))
    motionfilename = os.path.join(session_dir, '{0}.motion'.format(timestamp))

    t, n, dt, avg, std, breath = read_input_file(datafilename)
  
    header = "Session recorded {0} {1}-{2}".format(
        t[0].strftime('%a %d.%m.%Y'),
        t[0].strftime('%H:%M:%S'),
        t[-1].strftime('%H:%M:%S'))
      
    markers = read_marker_file(markerfilename)
    motion = None
    if os.path.exists(motionfilename):
        motion = read_marker_file(motionfilename)

    logging.info("Plotting...")
    dates = matplotlib.dates.date2num(t)
    fig, (ax1, ax2, ax3) = plt.subplots(3, sharex=True)
    fig.suptitle(header)
    ax1.set_title('Average')
    ax2.set_title('Std. Dev.')
    ax3.set_title('Breath rate')
    #ax1.set_ylim([0,40.0])
    #ax2.set_ylim([0,25.0])
    #ax3.set_ylim([0,3.0])
    
#    logger.info("Calculating error...")
#    errors = []
#    bands = get_bands()
#    for value in std:
#        for band, limit, multiplier in bands:
#            if value < limit:
#                err = (value - band) * multiplier
#                errors.append(err)
#                break

    #errors = smooth(np.array(errors))
    #errors = errors[5:len(errors)-5]

#    logger.info("n1=%s, n2=%s", len(std), len(errors))

    if smooth_data:
        logging.info("Smoothing data...")
        avg = smooth(np.array(avg))
        pow = smooth(np.array(pow))
        std = smooth(np.array(std))
        avg = avg[5:len(avg)-5]
        pow = pow[5:len(pow)-5]
        std = std[5:len(std)-5]

    ax1.plot_date(dates, avg, 'k.')
    ax2.plot_date(dates, std, 'k.')
    ax3.plot_date(dates, breath, 'r.')

    plt.gcf().autofmt_xdate()

    logger.info("Drawing markers...")

    for timestamp, color in markers:
        t = datetime.fromtimestamp(long(timestamp))
        logger.info("Drawing marker at %s", timestamp)
        ax1.axvline(x=t, color='k')
        ax2.axvline(x=t, color='k')
        ax3.axvline(x=t, color='k')

    if motion:
        for index, value in enumerate(avg):
            if value > 25:
                t = dates[index]
                ax1.axvline(x=t, color='b')
                ax2.axvline(x=t, color='b')
                ax3.axvline(x=t, color='b')

        for timestamp, data in motion:
            t = datetime.fromtimestamp(long(timestamp))
            logger.info("Drawing motion marker at %s", timestamp)
            ax1.axvline(x=t, color='y')
            ax2.axvline(x=t, color='y')
            #ax3.axvline(x=t, color='k')


    logging.info("Saving output file %s", outputfilename)
    fig.savefig(outputfilename)      
    logging.info("Finished plotting")


