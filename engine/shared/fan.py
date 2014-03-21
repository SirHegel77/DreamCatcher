from worker import Worker
from config import read_config
from time import sleep
import os
import logging
logger = logging.getLogger(__name__)

class Fan(Worker):
    def __init__(self):
        super(Fan, self).__init__()

    def read_temp(self):
        measure_temp = '/opt/vc/bin/vcgencmd measure_temp'
        value = os.popen(measure_temp).read()
        value = value.split('=')[1].split('\'')[0]
        return float(value)


    def _run(self):
        config = read_config()
        gpio_port = config.get('fan', 'gpio_port')
        fan_on_temp = config.getfloat('fan', 'fan_on_temp')
        fan_off_temp = config.getfloat('fan', 'fan_off_temp')
        gpio_admin = '/usr/local/bin/gpio-admin'
        gpio_path = '/sys/devices/virtual/gpio/gpio' + gpio_port
        fan_running = False
        try:
            logger.info("Exporting GPIO port...")
            os.popen('{0} export {1}'.format(
                gpio_admin, gpio_port))
            with open(os.path.join(gpio_path, 'direction'), 'w') as f:
                f.write('out')

            while self.should_stop == False:
                temp = self.read_temp()
                print temp
                if fan_running:
                    if temp < fan_off_temp:
                        print "Turning fan off."
                        logger.info("Turning fan off.")
                        fan_running = False
                        with open(os.path.join(gpio_path, 'value'), 'w') as f:
                            f.write('0')
                else:
                    if temp > fan_on_temp:
                        print "Turning fan on."
                        logger.info("Turning fan on.")
                        fan_running = True
                        with open(os.path.join(gpio_path, 'value'), 'w') as f:
                            f.write('1')
                sleep(10)
        finally:
            if fan_running:
                logger.info("Turning fan off.")
                with open(os.path.join(gpio_path, 'value'), 'w') as f:
                    f.write('0')

            logger.info("Unexporting GPIO port...")
            os.popen('{0} unexport {1}'.format(
                gpio_admin, gpio_port))
