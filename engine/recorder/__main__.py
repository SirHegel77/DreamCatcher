import logging
import sys
import getopt
from recorder import Recorder
from shared import read_config
logger = logging.getLogger(__name__)

def record_motion(motion_data):
    config = read_config()
    r = Recorder(config.get('directories', 'sessions'))
    r.record_motion(motion_data)

def start_recording():
    try:
        config = read_config()
        r = Recorder(config.get('directories', 'sessions'))
        r._run()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt")
    except:
        logger.error(sys.exc_info()[1])
    logger.info("Finished recording.")

def main(argv):
    def help():
        print "Usage: recorder [-m <motion data>]"

    try:
        opts, args = getopt.getopt(argv, "hm:", ["motion="])
    except getopt.GetoptError:
        help()
        sys.exit(2)
    if len(opts)==0:
        start_recording()
    else:
        for opt, arg in opts:
            if opt == '-h':
                help()
            elif opt in ("-m", "--motion"):
                record_motion(arg)
            else:
                help()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')

    main(sys.argv[1:])

