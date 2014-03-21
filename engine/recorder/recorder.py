import sys, getopt
import math
from datetime import datetime
import time
from shared import Worker, QueueWorker
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
        self._worker = QueueWorker(self.analyze)
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


    def analyze_axis(self, data, window, dt, breath_power):
        mean = np.mean(np.abs(data))
        std = np.std(data)
        logger.info("Mean: %s, std: %s, dt: %s", mean, std, dt)
        window = window - np.average(window)
        spec = np.fft.fft(window)
        freqs = np.fft.fftfreq(window.shape[-1], dt)
        ps = np.abs(spec)**2
        index = np.argmax(ps)
        pow = ps[index]
        if pow > breath_power: 
            f = np.abs(freqs[index] * 60)
        else:
            f = 0
        logger.info("Max power: %s, freq: %s", pow, f)
        return [mean, std, f]

    def analyze(self, timestamps, x, wx, y, wy):
        config = read_config()
        breath_power = config.get('recorder', 'breath_power') 

        timestamp = long(time.mktime(datetime.now().timetuple()))
        dt = np.abs(np.average(np.gradient(timestamps))) / 1000
       
        row = [timestamp] 
        row += self.analyze_axis(x, wx, dt, breath_power)
        row += self.analyze_axis(y, wy, dt, breath_power) 

        with open(self.data_filename, "a") as f:
            f.write(';'.join((str(x) for x in row)) + '\n')
        filename = os.path.join(self._directory, 
                    "{0}.npz".format(timestamp))
        np.savez(filename, dt = dt, timestamps = timestamps, 
            x = x, y = y, wx = wx, wy = wy)

    def emulate(self, conifg):
        pass

    def record_gyro(self, config):
        minimu_command = config.get('minimu', 'command').split()
        with Process(minimu_command) as p:
            for line in p:
                if self._should_stop:
                    break
                values = line.split()
                t = long(values[0])
                x = float(values[7])
                y = float(values[8])
                yield [t, x, y]

    def record(self):
        config = read_config()
        if config.getboolean('recorder', 'emulate'):
            recorder = self.emulate
        else:
            recorder = self.record_gyro

        logger.info("Recording gyro...")
        window_length = config.getint('recorder', 'window_length')
        increment = config.getint('recorder', 'window_increment')
        wx = RingBuffer(window_length)
        wy = RingBuffer(window_length)
        timestamps = np.zeros(increment, dtype='f')
        x = np.zeros(increment, dtype='f')
        y = np.zeros(increment, dtype='f')
        mean_x = config.getfloat('recorder', 'mean_x')
        mean_y = config.getfloat('recorder', 'mean_y')
        i = 0
        for t, rx, ry in recorder(config):
            if self._should_stop:
                break
            x[i] = rx
            y[i] = ry
            timestamps[i] = t
            i+=1
            if i>=increment:
                wx.extend(x)
                wy.extend(y)
                self._worker.enqueue(
                    np.copy(timestamps), 
                    np.copy(x), wx.get(),
                    np.copy(y), wy.get())
                i = 0

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
            self._worker.start()
            with open(self.marker_filename, "w") as f:
                pass
            with open(self.motion_filename, "w") as f:
                pass
            self.record()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt")
        finally:
            self._worker.stop()
            config.set('recorder', 'current_session',str(0))
            save_config(config)
        logger.info("Finished recording")

