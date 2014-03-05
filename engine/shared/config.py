import ConfigParser
import logging
logger = logging.getLogger(__name__)
CONFIG_FILE_PATH = '/opt/dreamcatcher/conf/dreamcatcher.conf'


def read_config():
    logger.info("Reading configuration.")
    config = ConfigParser.SafeConfigParser()
    config.read(CONFIG_FILE_PATH)
    return config

def save_config(config):
    logger.info("Saving configuration.")
    with open(CONFIG_FILE_PATH, 'w') as f:
        config.write(f)
