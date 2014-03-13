import sys, getopt
import subprocess
from datetime import datetime
from plotter import plot, plot_fft, plot_histogram
import logging
from shared import read_config
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
        conf = read_config()
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
