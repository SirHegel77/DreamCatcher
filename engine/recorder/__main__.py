import logging
import sys
import getopt
from recorder import Recorder
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
    def help():
        print "Usage: recorder -o <outputfile>"

    try:
        opts, args = getopt.getopt(argv, "ho:", ["output="])
    except getopt.GetoptError:
        help()
        sys.exit(2)
    if len(opts)==0:
        help()
    else:
        for opt, arg in opts:
            if opt == '-h':
                help()
            elif opt in ("-o", "--output"):
                record(arg)
            else:
                help()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')

    main(sys.argv[1:])

