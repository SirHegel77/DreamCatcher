import sys, getopt
import math
from datetime import datetime
import time
from shared import Worker
from shared import Process
from shared import smooth
import os
np = None
import logging
from shared import read_config, save_config
logger = logging.getLogger(__name__)

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

    @property
    def motion_filename(self):
        return os.path.join(self._directory,
            "{0}.motion".format(self._timestamp))


    def record_gyro(self):
        start = None
        data = []
        t = []
        config = read_config()
        minimu_command = config.get('minimu', 'command').split()
        time = config.getint('recorder', 'sampling_time')
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
                x, y, z = [float(s) for s in values[7:10]]
                data.append([x,y,z])
                #math.sqrt(gyro[0]**2 + gyro[1]**2 + gyro[2]**2))
                t.append(timestamp)
        return np.array(t), np.array(data)


    def calculate_dt(self, t):
        dts = [t[i+1]-t[i] for i in range(len(t)-1)]
        return np.average(np.array(dts)) 

    def record_marker(self):
        logger.info("Recording marker")
        timestamp = long(time.mktime(datetime.now().timetuple()))
        with open(self.marker_filename, "a") as f:
            f.write('{0};b\n'.format(timestamp))

    def record_motion(self, motion_data):
        logger.info("Recording motion data.")
        config = read_config()
        session = config.getint('recorder', 'current_session')
        if session == 0:
            logger.error("No active session.")
            return
        motion_filename = os.path.join(self._directory,
            "{0}.motion".format(session))
        timestamp = long(time.mktime(datetime.now().timetuple()))
        with open(motion_filename, "a") as f:
            f.write('{0};{1}\n'.format(timestamp, motion_data))        

    def _run(self):
        logger.info("Importing numpy...")
        global np
        import numpy as np
        logger.info("Recording to %s", self.data_filename)

        config = read_config()
        config.set('recorder', 'current_session', str(self._timestamp))
        save_config(config)
        try:
            with open(self.marker_filename, "w") as f:
                pass

            def avg(data, dt):
                abs = np.abs(data)
                avg = np.mean(abs)
                pow = np.sum(abs * dt) / 1000.0
                std = np.std(data)
                return [avg, pow, std]

            while True:
                timestamp = long(time.mktime(datetime.now().timetuple()))
                t, data = self.record_gyro()
                if self._should_stop:
                    break
                dt = np.average(np.gradient(t)) / 1000.0

                filename = os.path.join(self._directory, 
                    "{0}.npz".format(timestamp))

                np.savez(filename, t=t, data=data)
                logger.info("Saved data to %s", filename)
                #    fft = fft, freqs = freqs)
                x = data[:,0]
                y = data[:,1]
                z = data[:,2]
                w = np.sqrt(x*x+y*y+z*z)
                w = w - np.average(w)
                abs = np.abs(w)
                avg = np.mean(abs)
                std = np.std(w)
                logger.info("Smoothing data...")
                window_len = 101
                snip = (window_len-1)/2
                window = 'hanning'
                ws = smooth(w,window_len=window_len, window=window)
                ws = ws[snip:len(ws)-snip]
                logger.info("Performing FFT...")
                spec = np.fft.fft(ws)
                ps = np.abs(spec)**2
                freq = np.fft.fftfreq(len(t), dt)
                index = np.argmax(ps)
                pow = ps[index]
                if pow > 200000:
                    f = np.abs(freq[index] * 60)
                    logger.info("Detected breating frequency %s", f)
                else:
                    f = 0

                row = [timestamp, len(data), dt, avg, std, f]  
                line = ';'.join((str(x) for x in row))
                #logger.info("Recorded: %s", line)
                with open(self.data_filename, "a") as f:
                    f.write(line + '\n')

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt")
        except:
            logger.error("Unhandled exception: %s", sys.exc_info()[1])
        finally:
            config.set('recorder', 'current_session',str(0))
            save_config(config)
        logger.info("Finished recording")

