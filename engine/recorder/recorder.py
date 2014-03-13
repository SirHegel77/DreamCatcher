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
from shared import RingBuffer
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
        config = read_config()
        minimu_command = config.get('minimu', 'command').split()
        logger.info("Recording gyro...")
        window_length = config.getint('recorder', 'window_length')
        increment = config.getint('recorder', 'window_increment')
        window = RingBuffer(window_length)
        timestamps = np.zeros(increment, dtype='f')
        data = np.zeros(increment, dtype='f')
        i = 0
        with Process(minimu_command) as p:
            for line in p:
                if self._should_stop:
                    break
                if i < increment:
                    values = line.split()
                    t = long(values[0])
                    w = float(values[10])
                    timestamps[i] = t
                    data[i] = w
                    i+=1
                else:
                    logger.info("Analyzing...")
                    window.extend(data)
                    dt = np.abs(np.average(np.gradient(timestamps))) / 1000
                    spec = np.fft.fft(data)
                    freqs = np.fft.fftfreq(window_length, dt)
                    i = 0
                    
#                timestamp = long(values[0])
#                if start == None:
#                    start = timestamp
#                if self._should_stop or timestamp - start > time:
#                    logger.info("Finished recording gyro")
#                    break
#                x, y, z = [float(s) for s in values[7:10]]
#                data.append([x,y,z])
                #math.sqrt(gyro[0]**2 + gyro[1]**2 + gyro[2]**2))
#                t.append(timestamp)
#        return np.array(t), np.array(data)


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
            with open(self.motion_filename, "w") as f:
                pass
            self.record_gyro()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt")
        except:
            logger.error("Unhandled exception: %s", sys.exc_info()[1])
        finally:
            config.set('recorder', 'current_session',str(0))
            save_config(config)
        logger.info("Finished recording")

