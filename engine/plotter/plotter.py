import os
from datetime import datetime
from shared import read_config
import numpy as np
import matplotlib 
import matplotlib.pyplot as plt 
import logging
logger = logging.getLogger(__name__)
from shared import smooth
from multiprocessing import Process
from Queue import Queue
from shared import QueueWorker
from time import sleep
from shared import peakdet
from shared import RingBuffer

def fft(w, dt):
        avg = np.average(w)
        w = w - avg
        spec = np.fft.fft(w)
        spec = spec[0:len(spec)/2]
        freqs = np.fft.fftfreq(w.shape[-1], dt)
        freqs = freqs[0:len(freqs)/2]
        ps = np.abs(spec)**2
        wl = 5
        ps = smooth(ps, window_len = wl*2+1)
        ps = ps[wl:len(ps)-wl]     
        return (freqs, ps)

def prepare_plot_for_fft(session_dir, image_dir, timestamp):
    conf = read_config()
    datafilename = os.path.join(session_dir, '{0}.data'.format(timestamp))
    t, power, level = read_input_file(datafilename)
    dates = matplotlib.dates.date2num(t)
   
    logging.info("Plotting...")
    
    fig, (ax1, ax2) = plt.subplots(2, sharex=False)
    
    ax1.set_ylim([5, 7])
    ax1.axhline(y=conf.getfloat('recorder', 'power_min'), color='b')
    ax1.axhline(y=conf.getfloat('recorder', 'power_max'), color='r')
    ax1.plot_date(dates, np.array(power), 'k.')
    ax1.set_title('Signal power')

    logger.info("Drawing markers...")
    markerfilename = os.path.join(session_dir, '{0}.markers'.format(timestamp))
    markers = read_marker_file(markerfilename)
    for timestamp, color, comment in markers:
        t = datetime.fromtimestamp(long(timestamp))
        logger.info("Drawing marker at %s", timestamp)
        ax1.axvline(x=t, color=color)
    
    return fig, (ax1, ax2)


def plot_fft(session_dir, image_dir, timestamp1, timestamp2, close_fig=True):
    fig, (ax1, ax2) = prepare_plot_for_fft(session_dir, image_dir, timestamp1)
    fig.tight_layout()
    t = datetime.fromtimestamp(long(timestamp2))
    ax1.axvline(x=t, color='g')    
    
    inputfilename = os.path.join(session_dir, timestamp1, '{0}.npz'.format(timestamp2))
    outputfilename = os.path.join(image_dir, timestamp1, '{0}.png'.format(timestamp2))
    print "Plotting ", timestamp2
    logger.info("Reading input file...")
    npz = np.load(inputfilename)
        
    logger.info("Plotting...")
    major = matplotlib.ticker.MultipleLocator(0.5)
    minor = matplotlib.ticker.MultipleLocator(0.1)
    
    (freqs, psx) = fft(npz['wx'], npz['dt'])
    (freqs, psy) = fft(npz['wy'], npz['dt'])
    ps = (psx+psy)/2
    ax2.plot(freqs, ps)
    ax2.set_xlim([0,10])
    ax2.set_ylim([0,1000000])
    ax2.xaxis.set_major_locator(major)
    ax2.xaxis.set_minor_locator(minor)
    

    breath = []
    hb = []
    peak_limit = 150000
    max, min = peakdet(ps, peak_limit, freqs)
    max = np.array(max)
    if len(max)>0:
        ax2.scatter(max[:,0], max[:,1], color='red')
        previous_value = None
        first_harmonic = 2
        for peak in max:            
            found = False
            if previous_value != None:
                for i in xrange(first_harmonic, 5):
                    value = peak[0] * 60.0 / i
                    if abs(previous_value-value)< 2.6: # 2.6 /min ero edelliseen
                        found = True
                        previous_value = value
                        message =  "Harmonic peak {0}: {1:.2f}".format(i, value)
                        break
            if found == False:
                
                if peak[0] < 0.666: # 40/min
                    print "Breath peak: ", peak[0]
                    limit = 15
                else:
                    print "HB peak: ", peak[0]
                    limit = 110
                    
                for i in xrange(1,5):
                    value = peak[0] * 60.0 / i
                    first_harmonic = i+1
                    if value < limit:
                        break
                if i>1:
                    message =  "Harmonic peak {0:.2f}".format(value)            
                else:
                    message =  "Initial peak {0:.2f}".format(value)            
                previous_value = value
            if value < 30:
                breath.append(value)
            else:
                hb.append(value)
            ax2.annotate(message, xy=(peak[0], peak[1]))
    if len(breath)>0:
        breath = np.average(np.array(breath))
    else:
        breath = 0
    
    if len(hb)>0:
        hb = np.average(np.array(hb))
    else:
        hb = 0
        
    msg = "Breath: {0:.2f} Hb: {1:.2f}".format(breath, hb)
     
    ax2.set_title(msg)
     
    logger.info("Saving image...")
    plt.savefig(outputfilename)
    if close_fig:
        plt.close(fig)

def read_input_file(filename):
    logging.info("Reading data file %s", filename)
    t = []
    power = []
    level = []
    breath = []
    hb = []
    with open(filename, "r") as f:
        for line in f:
            values = line.split(";")
            t.append(datetime.fromtimestamp(long(values[0])))
            power.append(float(values[1]))
            level.append(float(values[2]))
            breath.append(float(values[3]))
            hb.append(float(values[4]))
    logger.info("Finished reading data file.")
    return [t, power, level, breath, hb]

def read_marker_file(filename):
    logging.info("Reading marker file %s", filename)
    with open(filename, "r") as f:
        markers = []
        for line in f:
            markers.append(line.split(";"))
    logging.info("Read %s markers.", len(markers))
    return markers


def process_timestamp(session_dir, image_dir, timestamp1, timestamp2):
    p = Process(target=plot_fft, args=(session_dir, image_dir, timestamp1, timestamp2))
    p.start()
    p.join()


def plot_all(session_dir, image_dir, timestamp):
    print "Plotting timestamp", timestamp
    if os.path.isdir(os.path.join(image_dir, timestamp)) == False:
        os.makedirs(os.path.join(image_dir, timestamp))
    datafilename = os.path.join(session_dir, '{0}.data'.format(timestamp))
    q = Queue()
    workers = []
    for i in range(8):
        w = QueueWorker(process_timestamp, queue = q)
        workers.append(w)
        w.start()
    conf = read_config()
    power_min = conf.getfloat('recorder', 'power_min')
    power_max = conf.getfloat('recorder', 'power_max')
    with open(datafilename, "r") as f:
        for line in f:
            values = line.split(";")
            power = float(values[1])
            level = float(values[2])
            if level > 0 or power < power_min or power > power_max:
                print "Ignoring ", values[0], "Power:", power
                continue
            outputfilename = os.path.join(image_dir, '{0}.png'.format(values[0]))
            if os.path.isfile(outputfilename):
                print "Ignoring ", values[0]
            else:
                logger.info("Plotting timestamp %s", values[0])
                q.put((session_dir, image_dir, timestamp, values[0]))
    
    print "Finished plotting timestamp", timestamp       
    for i in range(8):
        q.put(None)
                
    while not q.empty():
        sleep(0.01)

    
def analyze_breath_and_hb(freqs, ps):    
    breath = []
    hb = []
    peak_limit = 150000
    max, min = peakdet(ps, peak_limit, freqs)
    max = np.array(max)
    if len(max)>0:
        previous_value = None
        first_harmonic = 2
        for peak in max:            
            found = False
            if previous_value != None:
                for i in xrange(first_harmonic, 5):
                    value = peak[0] * 60.0 / i
                    if abs(previous_value-value)< 2.6: # 2.6 /min ero edelliseen
                        found = True
                        previous_value = value
                        break
                    
            if found == False:
                if peak[0] < 0.666: # 40/min
                    limit = 15
                else:
                    limit = 110
                    
                for i in xrange(1,5):
                    value = peak[0] * 60.0 / i
                    first_harmonic = i+1
                    if value < limit:
                        break          
                    
                previous_value = value
            if value < 30:
                breath.append(value)
            else:
                hb.append(value)
                
    if len(breath)>0:
        breath = np.average(np.array(breath))
    else:
        breath = 0
    
    if len(hb)>0:
        hb = np.average(np.array(hb))
    else:
        hb = 0
        
    return (breath, hb)
   
def reanalyze(session_dir, timestamp):
    datafilename = os.path.join(session_dir, '{0}.data'.format(timestamp))
    outputfilename = os.path.join(session_dir, '{0}.fixed.data'.format(timestamp))
    backupfilename = os.path.join(session_dir, '{0}.old.data'.format(timestamp))
    conf = read_config()
    rb = RingBuffer(25)
    with open(datafilename, "r") as f:
        with open(outputfilename, 'w') as f2:
            for line in f:
                values = line.split(";")
                print "Reanalyzing timestamp", values[0]
                inputfilename = os.path.join(session_dir, timestamp, '{0}.npz'.format(values[0]))
                npz = np.load(inputfilename)
                x = npz['x']
                y = npz['y']
                dt = npz['dt']
                (freqs, ps) = fft(x, dt)
                px = np.sum(ps)
                (freqs, ps) = fft(y, dt)
                py = np.sum(ps)
                p =np.log10(np.add(px, py) / 2)
                if p > conf.getfloat('recorder', 'power_max'):
                    value = np.ones(1)
                elif p < conf.getfloat('recorder', 'power_min'):
                    value = np.ones(1)
                else:
                    value = np.ones(1) * -1
                rb.extend(value)
                
                (freqs, psx) = fft(npz['wx'], dt)        
                (freqs, psy) = fft(npz['wy'], dt)
                ps = (psx+psy)/2
                (breath, hb) = analyze_breath_and_hb(freqs, ps)
                power = np.average(rb.get())
                f2.write(';'.join((str(x) for x in [values[0], p, power, breath, hb])) + '\n')
    
    if os.path.isfile(backupfilename):
        os.remove(backupfilename)
    os.rename(datafilename, backupfilename)
    os.rename(outputfilename, datafilename)

    
def plot(session_dir, image_dir, timestamp):
    conf = read_config()
    datafilename = os.path.join(session_dir, '{0}.data'.format(timestamp))
    t, power, level, breath, hb = read_input_file(datafilename)
    dates = matplotlib.dates.date2num(t)
   
    logging.info("Plotting...")
    
    fig, (ax1, ax2, ax3) = plt.subplots(3, sharex=True)
      
    header = "Session recorded {0} {1}-{2}".format(
        t[0].strftime('%a %d.%m.%Y'),
        t[0].strftime('%H:%M:%S'),
        t[-1].strftime('%H:%M:%S'))
        
    fig.suptitle(header)
    fig.autofmt_xdate()
    ax1.set_title('Signal power')        
    ax1.set_ylim([5, 7])
    ax1.axhline(y=conf.getfloat('recorder', 'power_min'), color='b')
    ax1.axhline(y=conf.getfloat('recorder', 'power_max'), color='r')
    ax2.set_title('Estimated sleep level')
    ax2.axhline(y=0, color='k')

    ax1.plot_date(dates, np.array(power), 'k.')
    ax2.plot_date(dates, np.array(level) , 'r.')
    ax3.set_title('Breath & HB')
    ax3.plot_date(dates, np.array(breath) , 'b.')
    ax3.set_ylim([0, 20])
    for tl in ax3.get_yticklabels():
        tl.set_color('b')
    ax4 = ax3.twinx()
    ax4.plot_date(dates, np.array(hb) , 'r.')
    ax4.set_ylim([50, 120])
    for tl in ax4.get_yticklabels():
        tl.set_color('r')
    logger.info("Drawing markers...")
    markerfilename = os.path.join(session_dir, '{0}.markers'.format(timestamp))
    markers = read_marker_file(markerfilename)
    for timestamp, color, comment in markers:
        t = datetime.fromtimestamp(long(timestamp))
        logger.info("Drawing marker at %s", timestamp)
        ax1.axvline(x=t, color=color)
        ax2.axvline(x=t, color=color)
        ax3.axvline(x=t, color=color)

    outputfilename = os.path.join(image_dir, '{0}.png'.format(timestamp))
    logging.info("Saving output file %s", outputfilename)
    plt.savefig(outputfilename)
    logging.info("Finished plotting")

if __name__=='__main__':
    logging.basicConfig(level=logging.INFO,
                format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                datefmt='%m-%d %H:%M')
    reanalyze("D:\Temp\dreams",  "1396138643")
    plot("D:\Temp\dreams", "D:\Temp\Images", "1396138643")
    #plot_fft("D:\Temp\dreams", "D:\Temp\Images", "1396041013", "1396053925", close_fig=False)
    #plot_all("D:\Temp\dreams", "D:\Temp\Images", "1396041013")
    #plot_all("D:\Temp\dreams", "D:\Temp\Images", "1396106889")
    
#    dreams = ["1395611012",
#              "1395691934",
#              "1395778998",
#              "1395869854",
#              "1395953904",
#              "1396020765",
#              "1396041013"]
#    for dream in dreams:
#        plot_all("D:\Temp\dreams", "D:\Temp\Images", dream)
    
    
