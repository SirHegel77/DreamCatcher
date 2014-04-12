import logging
from time import sleep
import sys
from menu import LcdMenu, MenuItem
from datetime import datetime
import time
import os
from recorder import Recorder
import plotter
import signal
from shared import read_config
from shared import ifconfig
from glob import iglob
from shared import Fan

logger = logging.getLogger(__name__)

class DreamCatcher(object):
    def __init__(self):
        config = read_config()
        self._path = os.path.abspath(
            config.get('directories', 'sessions'))
        self._recorder = None
        self._display_index = 0 # Text to show in root menu
        self._fan = Fan()
        self.create_menu()

    def create_menu(self):
        """ Create LCD menu. """
        m = LcdMenu()
        self._menu = m

        self._root_item = m.add_item("DreamCatcher", 
            self.record_marker)

        self._toggle_item = self._root_item.add_item(
            "Start\nRecording", self.toggle_recording)

        self._file_item = m.add_item(
            "File", activated=self.update_file_menu)

        self._network_item = m.add_item(
            "Network", activated=self.update_network_menu)

        m.add_item("Exit", self.stop)
        m.add_item("Shut down", self.shut_down)

    def update_root_menuitem(self):
        if self._recorder == None:
            return 

        def pow():
            return "Sig. Pow.\n{0:.2f}".format(
                self._recorder.signal_power)

        def level():
            return "Sleep Lvl.\n{0:.2f}".format(
                self._recorder.sleep_level)

        def hb():
            return "Est. Hb.\n{0:.2f}".format(
                self._recorder.hb)

        def breath():
            return "Est. Breath.\n{0:.2f}".format(
                self._recorder.breath)

        def be_clever():
            config = read_config()
            min = config.getfloat('recorder', 'power_min')
            pow = self._recorder.signal_power
            if pow < min:
                return "Thinking:\nNot in bed."
            else:
                level = self._recorder.sleep_level
                if level > 0:
                    return "Thinking:\nAwake."
                elif level > -0.5:
                    return "Thinking:\nLight sleep."
                else:
                    return "Thinking:\nSleeping."

        func = [pow, level, hb, breath, be_clever][self._display_index]
        self._root_item.header = func()
        self._display_index += 1
        if self._display_index > 4 :
            self._display_index = 0
        
 
    def delete_file(self, filename):
        """ Delete selected recording session. """
        def delete():
            logger.info("Deleting %s", filename)
        return delete

    def plot_file(self, timestamp):
        """ Plot selected recording session. """
        def plot():
            logger.info("Plotting %s", timestamp)
            config = read_config()
            self.menu.message = "Plotting..."
            plotter.plot(
                config.get('directories', 'sessions'),
                config.get('directories', 'images'),
                timestamp)
            self.menu.current_item = self._root_item
        return plot

    def update_network_menu(self):
        del self._network_item.items[:]
        for device, ip in ifconfig().items():
            self._network_item.add_item(
                '\n'.join([device, ip])) 

    def update_file_menu(self):
        """ Update file menu sub-items when file menu is activated. """
        del self._file_item.items[:]
        datafiles = iglob(self._path + '/*.data')
        for path, name in (os.path.split(f) for f in datafiles):
            timestamp = name.split('.')[0]
            format = "%d.%m.%Y\n%H:%M"
            date = datetime.fromtimestamp(float(timestamp))
            item = self._file_item.add_item(date.strftime(format))
            item.add_item("Plot", self.plot_file(timestamp))
            item.add_item("Delete", self.delete_file(timestamp))

    def start_recording(self):
        """ Start recording data. """
        if self._recorder == None:
            logger.info("Starting recorder...")
            self._restarts = 0
            self._recorder = Recorder(self._path)
            self._recorder.start()
            self.menu.current_item = self._root_item
            self._toggle_item.header = "Stop\nRecording"
            self._root_item.header = "DreamCatcher\nRecording..."
            self.menu.lcd.backlight(self.menu.lcd.RED)

    def stop_recording(self):
        """ Stop recording data. """
        if self._recorder != None:
            logger.info("Stopping recorder...")
            self._recorder.stop()
            self._recorder = None
            self.menu.current_item = self._root_item
            self._toggle_item.header = "Start\nRecording"
            self._root_item.header = "DreamCatcher"
            self.menu.lcd.backlight(self.menu.lcd.BLUE)

    def record_marker(self):
        """ Record marker. """
        if self._recorder != None:
            self.menu.lcd.backlight(self.menu.lcd.GREEN)
            self._recorder.record_marker()
            sleep(1.0)
            self.menu.lcd.backlight(self.menu.lcd.RED)

    def verify_recorder(self):
        """ Verify worker is running """
        if self._recorder != None:
            if self._recorder.is_running == False:
                self._recorder.start()
                self._restarts += 1
                self._menu.message(
                    "Restarted\n{0} restarts".format(
                    self._restarts))

    def toggle_recording(self):
        """ Start or stop recording. """
        if self._recorder == None:
            self.start_recording()
        else:
            self.stop_recording()

    @property
    def menu(self):
        """ Return LCD menu instance."""
        return self._menu

    def run(self):
        """ Start main loop. """
        logger.info("Starting DreamCatcher...")
        self._running = True
        self._menu.start()
        self._fan.start()
        try:
            t = 0
            while self._running:
                self.verify_recorder()
                if t > 3:
                    self.update_root_menuitem()
                    t = 0
                else:
                    t += 1
                sleep(0.5)
        except KeyboardInterrupt:
            pass

        self.stop_recording()
        logger.info("Stopping menu...")
        self._menu.stop()
        self._fan.stop()
        logger.info("DreamCatcher stopped.")

    def stop(self):
        """ Stop DreamCatcher. """
        logger.info("Stopping DreamCatcher...")
        self._running = False

    def shut_down(self):
        """ Shut down operating system... """
        logger.info("Shutting down operating system.")
        self.stop_recording()
        self.menu.message = "Shutting\ndown!"
        os.system('sudo shutdown -h 00')
        self._running = False


