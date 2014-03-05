from threading import Thread
from threading import Lock

class Worker(object):
    """
    Base class for threaded workers.
    """
    def __init__(self):
        super(Worker, self).__init__()
        self._thread = None
        self._should_stop = False
        self._lock = None

    @property
    def lock(self):
        return self._lock

    def start(self):
        """ Start the worker thread. """
        if self.is_running: 
            return
        self._should_stop = False
        self._thread = Thread(target = self.__run)
        self._thread.start()
          
    
    def __run(self):
        self._lock = Lock()
        try:
            self._lock.acquire()
            self._run()
        finally:
            self._lock.release()

    def stop(self):
        """ Stop the worker thread. """
        if self.is_running == False:
            return
        self._should_stop = True
        self._thread.join()
        self._thread = None

    @property
    def should_stop(self):
        return self._should_stop

    @should_stop.setter
    def should_stop(self, value):
        self._should_stop = value

    @property
    def is_running(self):
        """ Return True if worker is currently running. """
        if self._thread == None: return False
        if self._thread.is_alive(): return True
        return False

    def _run(self):
        """ 
        Worker method to be implemented by inherited class.
        Exit a.s.a.p. if _should_stop is set to True.
        """
        pass
