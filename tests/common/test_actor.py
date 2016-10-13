import pytest

from migrationmonitor.common import actor


class TestBaseActor(object):

    def test_run_on_success(self, mocker):
        base_actor = actor.BaseActor()
        base_actor._on_receive = mocker.stub()
        mocker.spy(base_actor.message_box, 'get')
        mocker.spy(base_actor.message_box, 'task_done')

        fake_item = mocker.stub()
        base_actor.tell(fake_item)
        base_actor.tell(actor.POISON_PILL)
        base_actor.run()

        assert base_actor.message_box.get.call_count == 2
        assert base_actor._on_receive.call_count == 1
        base_actor._on_receive.assert_called_once_with(fake_item)
        assert base_actor.message_box.task_done.call_count == 1

    def test_run_on_fail(self, mocker):
        base_actor = actor.BaseActor()
        base_actor._on_receive = mocker.stub()
        mocker.spy(base_actor.message_box, 'get')
        mocker.spy(base_actor.message_box, 'task_done')

        base_actor.tell(actor.POISON_PILL)
        base_actor.run()

        assert base_actor.message_box.get.call_count == 1
        assert base_actor._on_receive.call_count == 0
        assert base_actor.message_box.task_done.call_count == 0

    def test_tell_on_success(self, mocker):
        fake_message_box = mocker.stub()
        fake_message_box.put = mocker.stub()
        mocked_queue = mocker.patch('six.moves.queue.Queue')
        mocked_queue.return_value = fake_message_box

        fake_item = mocker.stub()
        base_actor = actor.BaseActor()
        base_actor.tell(fake_item)

        base_actor.message_box.put.assert_called_once_with(fake_item)

    def test_stop_on_success(self, mocker):
        fake_message_box = mocker.stub()
        fake_message_box.put = mocker.stub()
        mocked_queue = mocker.patch('six.moves.queue.Queue')
        mocked_queue.return_value = fake_message_box

        base_actor = actor.BaseActor()
        base_actor.stop()

        base_actor.message_box.put.assert_called_once_with(actor.POISON_PILL)

    def test_on_receive_raise_exception(self, mocker):
        base_actor = actor.BaseActor()
        with pytest.raises(NotImplementedError):
            base_actor._on_receive(mocker.stub())


def test_defer_on_success(mocker):
    mockedTimer = mocker.patch('threading.Timer')
    fake_fn = mocker.stub()
    seconds = 999

    actor.defer(fake_fn, seconds)

    mockedTimer.assert_called_once_with(seconds, fake_fn)
    mockedTimer.return_value.start.assert_called_once_with()
