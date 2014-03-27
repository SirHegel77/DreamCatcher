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
        self._npzdir = os.path.join(self._directory, str(self._timestamp))
        if os.path.exists(self._npzdir) == False:
            os.makedirs(self._npzdir)

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


    def analyze_axis(self, data, window, dt):
        mean = np.mean(np.abs(data))
        std = np.std(data)
        logger.info("Mean: %s, std: %s, dt: %s", mean, std, dt)
        window = window - np.average(window)
        spec = np.fft.fft(window)
        freqs = np.fft.fftfreq(window.shape[-1], dt)
        ps = np.abs(spec)**2
        p = np.log10(np.sum(ps))

        return [mean, std, p]

    def fft(self, w, dt):
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


    def analyze(self, timestamps, x, wx, y, wy):
        timestamp = long(time.mktime(datetime.now().timetuple()))
        dt = np.abs(np.average(np.gradient(timestamps))) / 1000
        (freqs, ps) = self.fft(x, dt)
        px = np.sum(ps)
        (freqs, ps) = self.fft(y, dt)
        py = np.sum(ps)
        signal_power = np.log10((px + py) / 2)
 
        # Update sleep buffer
        power_min = self._config.getfloat('recorder', 'power_min')
        power_max = self._config.getfloat('recorder', 'power_max')
        delta_trigger = self._config.getfloat('recorder', 'delta_trigger')
        level_trigger = self._config.getfloat('recorder', 'level_trigger')
        if signal_power > power_max:
            value = np.ones(1, dtype='f')
        elif signal_power < power_min:
            value = np.ones(1, dtype='f')
        else:
            value = np.ones(1, dtype='f') * -1.0
        self._sleep_window.extend(value)
        sleep_level = np.average(
            self._sleep_window.get())
  
        delta = sleep_level - self._sleep_level 

        if delta > delta_trigger:
            if self._sleep_level < level_trigger:
                if sleep_level > level_trigger:
                    self.record_marker(color='r', 
                        comment='Sleep level trigger')

        self._sleep_level = sleep_level

        row = [timestamp, signal_power, sleep_level, delta] 
        logger.info("Analyzed %s", row)

        with open(self.data_filename, "a") as f:
            f.write(';'.join((str(x) for x in row)) + '\n')
        if self._config.getboolean('recorder', 'emulate') == False:
            filename = os.path.join(self._npzdir, 
                    "{0}.npz".format(timestamp))
            np.savez(filename, dt = dt, timestamps = timestamps, 
                x = x, y = y, wx = wx, wy = wy)

    def emulate(self):
        timestamp = self._config.get('recorder', 'emulator_timestamp')
        datafile = os.path.join(self._directory, timestamp + '.data')
        npzdir = os.path.join(self._directory, timestamp)
        with open(datafile, 'r') as f:
            for line in f:
                timestamp = line.split(';')[0]
                npzfile = os.path.join(npzdir, timestamp + '.npz')
                npz = np.load(npzfile)
                t = npz['timestamps']
                x = npz['x']
                y = npz['y']
                for i in xrange(len(t)):
                    yield [t[i], x[i], y[i]]
                

    def record_gyro(self):
        minimu_command = self._config.get('minimu', 'command').split()
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
        if self._config.getboolean('recorder', 'emulate'):
            recorder = self.emulate
        else:
            recorder = self.record_gyro
        logger.info("Recording gyro...")
        window_length = self._config.getint('recorder', 'window_length')
        increment = self._config.getint('recorder', 'window_increment')
        wx = RingBuffer(window_length)
        wy = RingBuffer(window_length)
	self._sleep_window = RingBuffer(
            self._config.getint('recorder', 'sleep_window_length'))
        self._sleep_level = 0.0
        timestamps = np.zeros(increment, dtype='f')
        x = np.zeros(increment, dtype='f')
        y = np.zeros(increment, dtype='f')
        i = 0
        for t, rx, ry in recorder():
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

    def record_marker(self, color='k', comment='Manually triggered'):
        logger.info("Recording marker, color = %s", color)
        timestamp = long(time.mktime(datetime.now().timetuple()))
        with open(self.marker_filename, "a") as f:
            f.write(';'.join([str(timestamp), color, comment]) + '\n')

    def record_motion(self, motion_data):
        logger.info("Recording motion data.")
        session = self._config.getint('recorder', 'current_session')
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

        self._config = read_config()
        self._config.set('recorder', 'current_session', str(self._timestamp))
        save_config(self._config)
        try:
            self._worker.start()
            with open(self.marker_filename, "w") as f:
                pass
            with open(self.motion_filename, "w") as f:
                pass
            self.record()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt")
        except:
            logger.error("Unhandled exception: %s", sys.exc_info()[1])
        finally:
            self._worker.stop()
            self._config.set('recorder', 'current_session',str(0))
            save_config(self._config)
        logger.info("Finished recording")

