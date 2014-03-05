import subprocess
import logging
logger = logging.getLogger(__name__)

class Process(object):
    """
    Helper class for reading process output as iterable.
    """
    def __init__(self, command):
        super(Process, self).__init__()
        self._command = command
        self._process = None
        self._refs = 0

    def __iter__(self):
        return self

    def __enter__(self):
        if self._refs == 0:
            logger.info("Starting process %s", self._command)
            self._process = subprocess.Popen(self._command,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self._refs += 1
        return self

    def __exit__(self, type, value, traceback):
        self._refs -= 1
        if self._refs == 0:
            logger.info("Terminating process")
            self._process.terminate()
            self._process.stdout.close()


    def next(self):
        if self._process.poll() != None:
            raise StopIteration
        return self._process.stdout.readline()

