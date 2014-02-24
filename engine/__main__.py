import logging
import signal
from dreamcatcher import DreamCatcher
import sys

logger = logging.getLogger(__name__)


if __name__ == '__main__':   
    logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')
                    
    logger.info("Starting DreamCatcher...")

    dreamcatcher = DreamCatcher()

    def signal_handler(signal, frame):
        logger.info("SIGTERM received.")
        global dreamcatcher
        dreamcatcher.stop()

    signal.signal(signal.SIGTERM, signal_handler)

    try:
        dreamcatcher.run()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt.")
        dreamcatcher.stop()
    except:
        logger.error(sys.exc_info())

    logger.info("DreamCatcher stopped.")
