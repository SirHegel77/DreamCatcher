import sys, getopt
import subprocess
from datetime import datetime
from plotter import plot_fft
import logging

def main(argv):
    def help():
        print "Usage: plotter -b <basedir> -t <timestamp> -o <outputfile>"
    basedir = ''
    timestamp = ''
    outputfile = ''
    try:
        opts, args = getopt.getopt(argv, "hb:t:o:", ["basedir=", "timestamp=", "output="])
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
            elif opt in ("-b", "--basedir"):
                basedir = arg
            elif opt in ("-t", "--timestamp"):
                timestamp = arg
            elif opt in ("-o", "--output"):
                outputfile = arg
            else:            
                help()
                sys.exit()
        plot_fft(basedir, timestamp, outputfile)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        datefmt='%m-%d %H:%M')
    main(sys.argv[1:])
