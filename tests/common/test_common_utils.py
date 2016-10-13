from migrationmonitor.common.utils import retry

raised = False


def test_retry_decorator__can_be_applied_to_function():
    @retry(2)
    def fn(a, b):
        global raised
        if raised:
            raised = True
            raise Exception()

    fn(1, 1)


def test_retry_decorator__can_be_applied_to_class_method():
    class A(object):
        def __init__(self):
            self.raised = False

        def _h(self, t, e, d):
            assert self is not None

        @retry(2, hook=_h)
        def method(self):
            if not self.raised:
                self.raised = True
                raise Exception()

    A().method()
