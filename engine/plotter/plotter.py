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

def fft(w):
        avg = np.average(w)
        w = w - avg
        spec = np.fft.fft(w)
        spec = spec[0:len(spec)/2]
        freqs = np.fft.fftfreq(w.shape[-1], 0.021)
        freqs = freqs[0:len(freqs)/2]
        ps = np.abs(spec)**2
        wl = 5
        ps = smooth(ps, window_len = wl*2+1)
        ps = ps[wl:len(ps)-wl]     
        return (freqs, ps)
        
def plot_fft(session_dir, image_dir, timestamp1, timestamp2):
    fig, (ax1, ax2, ax3) = plot(session_dir, image_dir, timestamp1)
    t = datetime.fromtimestamp(long(timestamp2))
    ax1.axvline(x=t, color='r')    
    
    inputfilename = os.path.join(session_dir, timestamp1, '{0}.npz'.format(timestamp2))
    outputfilename = os.path.join(image_dir, timestamp1, '{0}.png'.format(timestamp2))
    print "Plotting ", timestamp2
    logger.info("Reading input file...")
    npz = np.load(inputfilename)
    
    
    starttime = datetime.fromtimestamp(long(timestamp1))
    header = "Session recorded {0} {1}".format(
        starttime.strftime('%a %d.%m.%Y'),
        starttime.strftime('%H:%M:%S'))

#    index = np.argmax(ps)
#    pow = ps[index]
#    if pow > 200000:
#        f = np.abs(freqs[index] * 60)
#    else:
#        f = None

    logger.info("Plotting...")
    major = matplotlib.ticker.MultipleLocator(0.5)
    minor = matplotlib.ticker.MultipleLocator(0.1)
    
    fig.suptitle(header)
    #ax1.plot(t, w)
    #ax1.set_ylim([-15,15])
    (freqs, ps) = fft(npz['wx'])
    ax2.plot(freqs, ps)
    ax2.set_xlim([0,10])
    ax2.set_ylim([0,1000000])
    ax2.xaxis.set_major_locator(major)
    ax2.xaxis.set_minor_locator(minor)
    
    peak_multipliers = [(2.0, 1 * 60), (3.5, 0.5 * 60), (5.0, 0.25 * 60), (7.0, 0.2 * 60)]    
    
    peak_limit = 150000
    max, min = peakdet(ps, peak_limit, freqs)
    max = np.array(max)    
    ax2.scatter(max[:,0], max[:,1], color='red')
           
    if max[0][0] < 0.5:
        print "Est. X breath rate:", max[0][0] * 60       

    for peak in max:
        for index, (limit, multiplier) in enumerate(peak_multipliers):
            if peak[0] < limit:
                print "Peak {0}:".format(index), peak[0] * multiplier
                break
    
    (freqs, ps) = fft(npz['wy'])
    ax3.plot(freqs, ps)
    ax3.set_xlim([0,10])
    ax3.set_ylim([0,1000000])
    ax3.xaxis.set_major_locator(major)
    ax3.xaxis.set_minor_locator(minor)
    
    max, min = peakdet(ps, peak_limit, freqs)
    max = np.array(max)    
    ax3.scatter(max[:,0], max[:,1], color='red')
           
    if max[0][0] < 0.5:
        print "Est. Y breath rate:", max[0][0] * 60  
        
    logger.info("Saving image...")
    #plt.savefig(outputfilename)
    #plt.close(fig)

def read_input_file(filename):
    logging.info("Reading data file %s", filename)
    t = []
    power = []
    level = []
    with open(filename, "r") as f:
        for line in f:
            values = line.split(";")
            t.append(datetime.fromtimestamp(long(values[0])))
            power.append(float(values[1]))
            level.append(float(values[2]))
    logger.info("Finished reading data file.")
    return [t, power, level]

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
    if os.path.isdir(os.path.join(image_dir, timestamp)) == False:
        os.makedirs(os.path.join(image_dir, timestamp))
    datafilename = os.path.join(session_dir, '{0}.data'.format(timestamp))
    q = Queue()
    workers = []
    for i in range(8):
        w = QueueWorker(process_timestamp, queue = q)
        workers.append(w)
        w.start()
        
    with open(datafilename, "r") as f:
        for line in f:
            values = line.split(";")
            outputfilename = os.path.join(image_dir, '{0}.png'.format(values[0]))
            if os.path.isfile(outputfilename):
                print "Ignoring ", timestamp
            else:
                logger.info("Plotting timestamp %s", values[0])
                q.put((session_dir, image_dir, timestamp, values[0]))
    for i in range(8):
        q.put(None)
                
    while q.not_empty:
        sleep(0.01)
    
   
def reanalyze(session_dir, timestamp):
    datafilename = os.path.join(session_dir, '{0}.data'.format(timestamp))
    outputfilename = os.path.join(session_dir, '{0}.fixed.data'.format(timestamp))
    backupfilename = os.path.join(session_dir, '{0}.old.data'.format(timestamp))
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
                (freqs, ps) = fft(x)
                px = np.sum(ps)
                (freqs, ps) = fft(y)
                py = np.sum(ps)
                p =np.log10(np.add(px, py) / 2)
                if p > 5.8:
                    value = np.ones(1)
                elif p < 5.25:
                    value = np.ones(1)
                else:
                    value = np.ones(1) * -1
                rb.extend(value)
                
                power = np.average(rb.get())
                f2.write(';'.join((str(x) for x in [values[0], p, power])) + '\n')
    
    if os.path.isfile(backupfilename):
        os.remove(backupfilename)
    os.rename(datafilename, backupfilename)
    os.rename(outputfilename, datafilename)

    
def plot(session_dir, image_dir, timestamp):
    conf = read_config()
    datafilename = os.path.join(session_dir, '{0}.data'.format(timestamp))
    t, power, level = read_input_file(datafilename)
    dates = matplotlib.dates.date2num(t)
   
    logging.info("Plotting...")
    
    fig, (ax1, ax2) = plt.subplots(2, sharex=True)
      
    header = "Session recorded {0} {1}-{2}".format(
        t[0].strftime('%a %d.%m.%Y'),
        t[0].strftime('%H:%M:%S'),
        t[-1].strftime('%H:%M:%S'))
        
    fig.suptitle(header)
    fig.autofmt_xdate()
    ax1.set_title('Signal power')        
    ax1.set_ylim([5, 7])
    ax1.axhline(y=5.25, color='b')
    ax1.axhline(y=5.8, color='r')
    ax2.set_title('Estimated sleep level')
    ax2.axhline(y=0, color='k')

    ax1.plot_date(dates, np.array(power), 'k.')
    ax2.plot_date(dates, np.array(level) , 'r.')

    logger.info("Drawing markers...")
    markerfilename = os.path.join(session_dir, '{0}.markers'.format(timestamp))
    markers = read_marker_file(markerfilename)
    for timestamp, color, comment in markers:
        t = datetime.fromtimestamp(long(timestamp))
        logger.info("Drawing marker at %s", timestamp)
        ax1.axvline(x=t, color=color)
        ax2.axvline(x=t, color=color)


    outputfilename = os.path.join(image_dir, '{0}.png'.format(timestamp))
    logging.info("Saving output file %s", outputfilename)
    plt.savefig(outputfilename)
    logging.info("Finished plotting")

if __name__=='__main__':
    #reanalyze("D:\Temp\dreams",  "1396041013")
    plot("D:\Temp\dreams", "D:\Temp\Images", "1396041013")

