from time import sleep


try:
    xrange
except NameError:
    xrange = range


def retry(max_tries, delay=1, delay_mult=2,
          exceptions=(Exception,), hook=None):
    """
    Naive implementation of retry function
    docorator with exception hook.
    """
    def _dec(func):
        def _fn(self, *args, **kwargs):
            _delay = delay

            tries = reversed(xrange(max_tries))
            for tries_remaining in tries:
                try:
                    if self is None:
                        return func(*args, **kwargs)
                    else:
                        return func(self, *args, **kwargs)
                except exceptions as ex:
                    if tries_remaining > 0:
                        if hook is not None:
                            if self is None:
                                hook(tries_remaining, ex, _delay)
                            else:
                                hook(self, tries_remaining, ex, _delay)

                        sleep(_delay)
                        _delay = _delay * delay_mult
                    else:
                        raise
                else:
                    break
        return _fn
    return _dec
