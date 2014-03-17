import threading
import logging
from Queue import Queue
logger = logging.getLogger(__name__)

class QueueWorker(threading.Thread):
    def __init__(self, process_args, queue = Queue(0)):
        super(QueueWorker, self).__init__()
        self._queue = queue
        self._process_args = process_args

    @property
    def queue(self):
        return self._queue

    def enqueue(self, *args):
        self._queue.put(args)

    def stop(self):
        self._queue.put(None)

    def run(self):
        logger.info("Starting queue worker...")
        while True:
            args = self._queue.get()
            if args == None:
                break
            self._process_args(*args)
        logger.info("Stopped queue worker.")

