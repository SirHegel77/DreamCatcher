import logging
import sys
import getopt
from recorder import Recorder
from shared import read_config
logger = logging.getLogger(__name__)

def record(filename):
    try:
        r = Recorder(filename)
        r._run()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt")
    except:
        logger.error(sys.exc_info()[1])
    logger.info("Finished logging.")

def main(argv):
    config = read_config()
    record(config.get('directories', 'sessions'))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')

    main(sys.argv[1:])

