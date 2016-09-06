from Queue import Queue
import threading

POISON_PILL = object()


class BaseActor(threading.Thread):

    def __init__(self):
        super(BaseActor, self).__init__()
        self.daemon = True
        self.q = Queue()

    def add_task_to_queue(self, item):
        self.q.put(item)

    def run(self):
        while True:
            item = self.q.get()
            if item is POISON_PILL:
                break

            try:
                self._run(item)
            finally:
                self.q.task_done()

    def _run(self, item):
        raise NotImplemented()

    def stop(self):
        self.q.put(POISON_PILL)
