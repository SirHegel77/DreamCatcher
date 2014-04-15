
import sys
from datetime import datetime
import time
from shared import Worker, QueueWorker
from shared import Process
from shared import smooth
from shared import peakdet
import os
np = None
import logging
from shared import read_config, save_config
from shared import RingBuffer
logger = logging.getLogger(__name__)


class Recorder(Worker):
    STATE_NOT_IN_BED = 0
    STATE_AWAKE = 1
    STATE_LIGHT_SLEEP = 2
    STATE_DEEP_SLEEP = 3

    def __init__(self, directory):
        super(Recorder, self).__init__()
        self._worker = QueueWorker(self.analyze)
        self._directory = directory
        self._timestamp = long(time.mktime(datetime.now().timetuple()))
        self._npzdir = os.path.join(self._directory, str(self._timestamp))
        self._signal_power = 0.0
        self._sleep_level = 0.0
        self._breath = 0.0
        self._hb = 0.0

    @property
    def status_filename(self):
        return os.path.join(self._directory, 
            "current_status.data".format(self._timestamp))
    

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

    @property
    def signal_power(self):
        return self._signal_power

    @property
    def sleep_level(self):
        return self._sleep_level

    @property
    def breath(self):
        return self._breath

    @property
    def hb(self):
        return self._hb

    @property
    def state(self):
        config = read_config()
        min = config.getfloat('recorder', 'power_min')
        pow = self.signal_power
        if pow < min:
            return Recorder.STATE_NOT_IN_BED
        else:
            level = self.sleep_level
            if level > 0:
                return Recorder.STATE_AWAKE
            elif level > -0.5:
                return Recorder.STATE_LIGHT_SLEEP
            else:
                return Recorder.STATE_DEEP_SLEEP


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

    def analyze_breath_and_hb(self, freqs, ps):    
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
                        if abs(previous_value-value)< 2.6:
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

    def analyze(self, timestamps, x, wx, y, wy):
        timestamp = long(time.mktime(datetime.now().timetuple()))
        dt = np.abs(np.average(np.gradient(timestamps))) / 1000
        (freqs, psx) = self.fft(x, dt)        
        (freqs, psy) = self.fft(y, dt)
        px = np.sum(psx) / psx.shape[-1]
        py = np.sum(psy) / psy.shape[-1]
        signal_power = np.log10((px + py) / 2)
        

        mask_limit = 13.0
        mx = np.ma.masked_outside(wx - np.mean(wx), -mask_limit, mask_limit)    
        my = np.ma.masked_outside(wy - np.mean(wy), -mask_limit, mask_limit)
        mask = np.logical_or(mx.mask, my.mask)
        mx = np.ma.array(mx, mask=mask).compressed()    
        my = np.ma.array(my, mask=mask).compressed()
        
        if mx.shape[-1] > 20 and my.shape[-1] > 20:
            (freqs, psx) = self.fft(mx, dt)        
            (freqs, psy) = self.fft(my, dt)
            ps = (psx+psy)/2
            (breath, hb) = self.analyze_breath_and_hb(freqs, ps)
        else:
            logger.info("Skipping breath analysis")
            breath = 0
            hb = 0

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
        self._signal_power = signal_power
        self._hb = hb
        self._breath = breath
        state = self.state
        row = [timestamp, signal_power, sleep_level, delta, breath, hb, state] 
        logger.info("Analyzed %s", row)

        with open(self.data_filename, "a") as f:
            f.write(';'.join((str(x) for x in row)) + '\n')

        with open(self.status_filename, "w") as f:
            f.write(';'.join((str(x) for x in row)) + '\n')

        if self._config.getboolean('recorder', 'emulate') == False:
            if os.path.exists(self._npzdir) == False:
                os.makedirs(self._npzdir)
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
        self._config.set('recorder', 'is_recording', str(True))
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
            self._config.set('recorder', 'is_recording', str(False))
            save_config(self._config)
            os.remove(self.status_filename)
        logger.info("Finished recording")

