import sys
import time
import random

try:
    from functools import lru_cache
except:
    from functools32 import lru_cache

from collections import deque


MAXNUM = sys.maxsize
MAXLEN = 1000
RNG = random.SystemRandom()

def impl_via_deque(deq):
    def _fn():
        cur = RNG.randint(0, MAXNUM)
        not_in_cache = True
        for elem in deq:
            if cur == elem:
                not_in_cache = False

        if not_in_cache:
            # assume that we do some side effects here
            deq.append(cur)

    return _fn


def test_deque(benchmark):
    deq = deque(maxlen=MAXLEN)
    sut = impl_via_deque(deq)
    benchmark(sut)


def impl_via_lru():
    @lru_cache(maxsize=MAXLEN)
    def add_random_number(num):
        # assume that we do some side effects here
        return num

    def _fn():
        cur = RNG.randint(0, MAXNUM)
        add_random_number(cur)

    return _fn


def test_lru(benchmark):
    sut = impl_via_lru()
    benchmark(sut)
