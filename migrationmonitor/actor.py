from Queue import Queue
import threading

POISON_PILL = object()


class BaseActor(threading.Thread):

    def __init__(self):
        super(BaseActor, self).__init__()
        self.daemon = True
        self.q = Queue()

    def tell(self, item):
        self.q.put(item)

    def run(self):
        while True:
            item = self.q.get()
            if item is POISON_PILL:
                break

            try:
                self._on_receive(item)
            finally:
                self.q.task_done()

    def _on_receive(self, item):
        raise NotImplemented()

    def stop(self):
        self.q.put(POISON_PILL)
