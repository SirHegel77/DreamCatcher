import sys, getopt
import subprocess
from datetime import datetime
from plotter import plot, plot_fft
import logging
import ConfigParser
CONFIG_FILE_PATH = '/opt/dreamcatcher/conf/dreamcatcher.conf'
logger = logging.getLogger(__name__)

def main(argv):
    def help():
        print "Usage: plotter -t <timestamp>"
    timestamp = ''
    try:
        opts, args = getopt.getopt(argv, "ht:", ["timestamp="])
    except getopt.GetoptError:
        help()
        sys.exit(2)
    if len(opts)==0:
        help()
    else:
        for opt, arg in opts:
            if opt == '-h':
                help()
                sys.exit()
            elif opt in ("-t", "--timestamp"):
                timestamp = arg
            else:            
                help()
                sys.exit()
        conf = ConfigParser.SafeConfigParser()
        conf.read(CONFIG_FILE_PATH)
        logger.info("Plotting timestamp {0}".format(timestamp))
        plot(
            conf.get('directories', 'sessions'), 
            conf.get('directories', 'images'), 
            timestamp)
        logger.info("Finished plotting.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        datefmt='%m-%d %H:%M')
    main(sys.argv[1:])
