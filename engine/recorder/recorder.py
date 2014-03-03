import sys, getopt
import math
import subprocess
from datetime import datetime
import time
from shared import Worker
import os
import ConfigParser
np = None
import logging
logger = logging.getLogger(__name__)
CONFIG_FILE_PATH='/opt/dreamcatcher/conf/dreamcatcher.conf'

class Process(object):
    def __init__(self, command):
        super(Process, self).__init__()
        self._command = command
        self._process = None
        self._refs = 0

    def __iter__(self):
        return self


    def __enter__(self):
        if self._refs == 0:
            logger.info("Starting process %s", self._command)
            self._process = subprocess.Popen(self._command,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self._refs += 1
        return self

    def __exit__(self, type, value, traceback):
        self._refs -= 1
        if self._refs == 0:
            logger.info("Terminating process")
            self._process.terminate()
            self._process.stdout.close()


    def next(self):
        if self._process.poll() != None:
            raise StopIteration
        return self._process.stdout.readline()    

class Recorder(Worker):
    def __init__(self, directory):
        super(Recorder, self).__init__()
        self._directory = directory
        self._timestamp = long(time.mktime(datetime.now().timetuple()))

    @property
    def data_filename(self):
        return os.path.join(self._directory, 
            "{0}.data".format(self._timestamp))

    @property
    def marker_filename(self):
        return os.path.join(self._directory,
            "{0}.markers".format(self._timestamp))

    def record_gyro(self, time):
        start = None
        data = []
        t = []
        parser = ConfigParser.SafeConfigParser()
        parser.read(CONFIG_FILE_PATH)
        minimu_command = parser.get('minimu', 'command').split()
        logger.info("Recording gyro...")
        with Process(minimu_command) as p:
            for line in p:
                if self._should_stop:
                    break
                values = line.split()
                timestamp = long(values[0])
                if start == None:
                    start = timestamp
                if self._should_stop or timestamp - start > time:
                    logger.info("Finished recording gyro")
                    break
                gyro = [float(s) for s in values[7:10]]
                data.append(math.sqrt(gyro[0]**2 + gyro[1]**2 + gyro[2]**2))
                t.append(timestamp)
        return t, data


    def calculate_dt(self, t):
        dts = [t[i+1]-t[i] for i in range(len(t)-1)]
        return np.average(np.array(dts)) 

    def record_marker(self):
        logger.info("Recording marker")
        timestamp = long(time.mktime(datetime.now().timetuple()))
        with open(self.marker_filename, "a") as f:
            f.write('{0};b\n'.format(timestamp))

    def _run(self):
        logger.info("Importing numpy...")
        global np
        import numpy as np
        logger.info("Recording to %s", self.data_filename)

        try:
            with open(self.marker_filename, "w") as f:
                pass
            while True:
                timestamp = long(time.mktime(datetime.now().timetuple()))
                t, data = self.record_gyro(20000)
                if self._should_stop:
                    break
                dt = self.calculate_dt(t)

                logger.info("Performing FFT...")

                #n = len(data)
                #k = np.arange(n)
                #T = n * dt / 1000
                #frq = k / T
                #freqs = frq[range(n/2)]
                fft = np.abs(np.fft.fft(data))
                freqs = np.fft.fftfreq(fft.size, dt/1000)
                fft = fft[0:len(fft)/2]
                freqs = freqs[0:len(freqs)/2]
            
                filename = os.path.join(self._directory, 
                    "{0}.npz".format(timestamp))

                np.savez(filename,
                    fft = fft, freqs = freqs)
 
                avg = np.mean(data)
                pow = np.sum(data * dt) / 1000.0
                std = np.std(data)
                line = "{0};{1};{2};{3};{4};{5}".format(
                    timestamp, len(t), dt, avg, pow, std)
                logger.info("Recorded: %s", line)
                with open(self.data_filename, "a") as f:
                    f.write(line + '\n')

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt")
        except:
            logger.error("Unhandled exception: %s", sys.exc_info()[1])
        logger.info("Finished recording")

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
    if window == 'flat': #moving average
        w=np.ones(window_len,'d')
    else:
        w=eval('np.'+window+'(window_len)')

    y=np.convolve(w/w.sum(),s,mode='valid')
    return y
