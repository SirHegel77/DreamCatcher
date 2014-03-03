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

logger = logging.getLogger(__name__)

class DreamCatcher(object):
    def __init__(self):
        config = read_config()
        self._path = os.path.abspath(
            config.get('directories', 'sessions'))
        self._recorder = None
        self.create_menu()

    def create_menu(self):
        m = LcdMenu()
        self._menu = m
        self._root_item = m.add_item("DreamCatcher", 
            self.record_marker)

        self._toggle_item = self._root_item.add_item(
            "Start\nRecording", self.toggle_recording)

        self._file_item = m.add_item(
            "File", activated=self.update_file_menu)

        m.add_item("Exit", self.stop)
        m.add_item("Shut down", self.shut_down)
 
    def delete_file(self, filename):
        def delete():
            logger.info("Deleting %s", filename)
        return delete

    def plot_file(self, timestamp):
        def plot():
            logger.info("Plotting %s", timestamp)
            config = read_config()
            self.menu.message = "Plotting..."
            plotter.plot(self._path, timestamp,
                os.path.join(
                os.path.abspath(config.get('directories', 'images')),
                '{0}.png'.format(timestamp)))
            self.menu.current_item = self._root_item
        return plot

    def update_file_menu(self):
        del self._file_item.items[:]

        files = os.listdir(self._path)
        files.sort(key=lambda x: os.path.getmtime(os.path.join(self._path, x)))
        for name in reversed(files):
            if '.data' in name:
                timestamp = name.split('.')[0]
                format = "%d.%m.%Y\n%H:%M"
                date = datetime.fromtimestamp(float(timestamp))
                item = self._file_item.add_item(date.strftime(format))
                item.add_item("Plot", self.plot_file(timestamp))
                item.add_item("Delete", self.delete_file(timestamp))

    def start_recording(self):
        if self._recorder == None:
            logger.info("Starting recorder...")
            self._recorder = Recorder(self._path)
            self._recorder.start()
            self.menu.current_item = self._root_item
            self._toggle_item.header = "Stop\nRecording"
            self._root_item.header = "DreamCatcher\nRecording..."
            self.menu.lcd.backlight(self.menu.lcd.RED)

    def stop_recording(self):
        if self._recorder != None:
            logger.info("Stopping recorder...")
            self._recorder.stop()
            self._recorder = None
            self.menu.current_item = self._root_item
            self._toggle_item.header = "Start\nRecording"
            self._root_item.header = "DreamCatcher"
            self.menu.lcd.backlight(self.menu.lcd.BLUE)

    def record_marker(self):
        if self._recorder != None:
            self.menu.lcd.backlight(self.menu.lcd.GREEN)
            self._recorder.record_marker()
            sleep(1.0)
            self.menu.lcd.backlight(self.menu.lcd.RED)

    def toggle_recording(self):
        if self._recorder == None:
            self.start_recording()
        else:
            self.stop_recording()

    @property
    def menu(self):
        return self._menu

    def run(self):
        logger.info("Starting DreamCatcher...")
        self._running = True
        self._menu.start()
        try:
            while self._running:
                sleep(0.5)
        except KeyboardInterrupt:
            pass

        self.stop_recording()

        logger.info("Stopping menu...")
        self._menu.stop()
        logger.info("DreamCatcher stopped.")

    def stop(self):
        logger.info("Stopping DreamCatcher...")
        self._running = False


    def shut_down(self):
        logger.info("Shutting down operating system.")
        self.stop_recording()
        self.menu.message = "Shutting\ndown!"
        os.system('sudo shutdown -h 00')
        self._running = False


