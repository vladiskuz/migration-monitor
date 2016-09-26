from Queue import Queue
import threading

POISON_PILL = object()


class BaseActor(threading.Thread):
    """Actor base class. Implements send/receive logic via threads.
    """
    def __init__(self):
        super(BaseActor, self).__init__()
        self.daemon = True
        self.message_box = Queue()


    def tell(self, item):
        """Send a message to the actor.
        """
        self.message_box.put(item)


    def run(self):
        while True:
            item = self.message_box.get()
            if item is POISON_PILL:
                break

            try:
                self._on_receive(item)
            finally:
                self.message_box.task_done()

    def _on_receive(self, item):
        raise NotImplementedError()


    def stop(self):
        """Stops the actor.
        """
        self.message_box.put(POISON_PILL)


def defer(fn, seconds):
    """Runs fn after predefined number of seconds.
    """
    threading.Timer(seconds, fn).start()
