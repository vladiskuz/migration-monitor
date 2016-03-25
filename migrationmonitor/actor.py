from Queue import Queue
from threading import Thread

from logger import debug

THREAD_LIFE_TIMEOUT = 1000
POISON_PILL = object()


def actor(fn, timeout=THREAD_LIFE_TIMEOUT):
    q = Queue()

    def tell(item):
        q.put(item)

    def worker():
        while True:
            item = q.get()
            if item is POISON_PILL:
                debug("%s got poison pill, exiting." % (fn.__name__,))
                break

            fn(tell, item)
            q.task_done()

    t = Thread(target=worker, name=fn.__name__)
    t.daemon = True
    t.start()

    return tell
