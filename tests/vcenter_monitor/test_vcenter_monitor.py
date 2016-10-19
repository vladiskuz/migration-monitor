from datetime import timedelta
import ssl
import time

from migrationmonitor.common import actor
from migrationmonitor.common import logger
from migrationmonitor.vcenter_monitor import monitor


def test_is_migration_event_on_success(mocker):
    class StubClassA(object):
        pass

    class StubClassB(object):
        pass

    class StubClassC(object):
        pass

    mocker.patch(
        'pyVmomi.vim.event.VmMigratedEvent',
        new=StubClassA)
    mocker.patch(
        'pyVmomi.vim.event.VmBeingHotMigratedEvent',
        new=StubClassB)

    event_a = StubClassA()
    event_b = StubClassB()
    event_c = StubClassC()

    assert monitor._is_migration_event(event_a)
    assert monitor._is_migration_event(event_b)
    assert not monitor._is_migration_event(event_c)


def test_create_vcenter_connection_on_success(mocker):
    fake_context = mocker.stub()

    create_default_context = mocker.patch.object(ssl, 'create_default_context')
    CERT_NONE = mocker.patch.object(ssl, 'CERT_NONE')
    create_default_context.return_value = fake_context

    log_debug = mocker.patch.object(logger, 'debug')
    fake_settings = mocker.patch('migrationmonitor.settings')
    fake_settings.VCENTER = {
        "HOST": "fake_host",
        "USERNAME": "fake_user_name",
        "PASSWORD": "fake_password"}

    SmartConnect = mocker.patch('pyVim.connect.SmartConnect')

    connection = monitor._create_vcenter_connection()

    assert connection == SmartConnect.return_value
    create_default_context.assert_called_once_with()
    assert not fake_context.check_hostname
    assert fake_context.verify_mode == CERT_NONE
    log_debug.assert_called_once_with(
        "Connecting to vCenter %s",
        fake_settings.VCENTER["HOST"])
    SmartConnect.assert_called_once_with(
        host=fake_settings.VCENTER["HOST"],
        user=fake_settings.VCENTER["USERNAME"],
        pwd=fake_settings.VCENTER["PASSWORD"],
        sslContext=fake_context)


class TestVCenterMonitor(object):
    def test_start_on_success(self, mocker):
        fake_reporter = mocker.stub()
        fake_reporter.start = mocker.stub()

        Reporter = mocker.patch(
            'migrationmonitor.common.reporter.Reporter')
        Reporter.return_value = fake_reporter

        _create_vcenter_connection = mocker.patch.object(
            monitor, '_create_vcenter_connection')

        start = mocker.patch.object(actor.BaseActor, 'start')

        vcenter_monitor = monitor.VCenterMonitor()
        vcenter_monitor.tell = mocker.stub()
        vcenter_monitor.start()

        fake_reporter.start.assert_called_once_with()
        _create_vcenter_connection.assert_called_once_with()
        start.assert_called_once_with()
        vcenter_monitor.tell.assert_called_once_with("start")

    def test_stop_on_success(self, mocker):
        fake_reporter = mocker.stub()
        fake_reporter.stop = mocker.stub()

        Reporter = mocker.patch(
            'migrationmonitor.common.reporter.Reporter')
        Reporter.return_value = fake_reporter

        Disconnect = mocker.patch('pyVim.connect.Disconnect')

        stop = mocker.patch.object(actor.BaseActor, 'stop')

        vcenter_monitor = monitor.VCenterMonitor()
        vcenter_monitor.stop()

        fake_reporter.stop.assert_called_once_with()
        Disconnect.assert_called_once_with(vcenter_monitor.vc_connect)
        stop.assert_called_once_with()

    def test_on_receive_on_success(self, mocker):
        fake_reporter = mocker.stub()
        fake_reporter.tell = mocker.stub()

        Reporter = mocker.patch(
            'migrationmonitor.common.reporter.Reporter')
        Reporter.return_value = fake_reporter

        fake_settings = mocker.patch('migrationmonitor.settings')
        fake_settings.MEASUREMENT = {"EVENTS_MEASUREMENT": "fake_measurement"}
        fake_settings.VCENTER = {
            "POLL_FREQ": "fake_poll", "EVENTS_BUFFER_LENGTH": 1000}

        event1 = self._create_event(mocker)
        event2 = self._create_event(mocker)
        event3 = self._create_event(mocker)
        events = [event1, event2, event3]

        args1_event1 = self._create_args(mocker, event1, fake_settings)
        args2_event2 = self._create_args(mocker, event2, fake_settings)

        _fetch_vcenter_events = mocker.patch.object(
            monitor.VCenterMonitor, '_fetch_vcenter_events')
        _fetch_vcenter_events.return_value = events

        log_debug = mocker.patch.object(logger, 'debug')
        time_sleep = mocker.patch.object(time, 'sleep')
        tell = mocker.patch.object(actor.BaseActor, 'tell')

        expected_args_log_debug = [
            mocker.call('Got %s events from vCenter.', len(events)),
            mocker.call(
                "%s %s %s", event1.createdTime, type(event1).__name__, event1),
            mocker.call(
                "%s %s %s", event2.createdTime, type(event2).__name__, event2),
            mocker.call('Event: %s already reported.', event3.key)]

        expected_args_tell = [
                mocker.call(args1_event1), mocker.call(args2_event2)]

        vcenter_monitor = monitor.VCenterMonitor()
        vcenter_monitor.reported_event_ids.append(event3.key)
        vcenter_monitor._on_receive(mocker.stub())

        _fetch_vcenter_events.assert_called_once_with()
        assert log_debug.call_args_list == expected_args_log_debug
        for event in events:
            assert event.key in vcenter_monitor.reported_event_ids
        assert fake_reporter.tell.call_args_list == expected_args_tell

        time_sleep.assert_called_once_with(fake_settings.VCENTER["POLL_FREQ"])
        tell.assert_called_once_with("continue")

    def _create_event(self, mocker):
        event = mocker.stub()
        event.key = mocker.stub()
        event.vm = mocker.stub()
        event.vm.name = mocker.stub()
        event.vm.vm = mocker.stub()
        event.createdTime = mocker.stub()

        return event

    def _create_args(self, mocker, event, fake_settings):
        tags = {
            "vm_name": event.vm.name,
            "vm_id": event.vm.vm}
        values = {"value": 1}
        args = {
            "tags": tags,
            "values": values,
            "measurement": fake_settings.MEASUREMENT["EVENTS_MEASUREMENT"],
            "datetime": event.createdTime}

        return args

    def test_reconnect_on_success(self, mocker):
        mocker.patch('migrationmonitor.common.reporter.Reporter')

        log_error = mocker.patch.object(logger, 'error')
        _create_vcenter_connection = mocker.patch.object(
            monitor, '_create_vcenter_connection')

        ex = mocker.stub()

        vcenter_monitor = monitor.VCenterMonitor()
        vcenter_monitor._reconnect(
            mocker.stub(), ex, mocker.stub())

        log_error.assert_called_once_with("Caught %s", ex)
        _create_vcenter_connection.assert_called_once_with()
        assert vcenter_monitor.vc_connect == \
            _create_vcenter_connection.return_value

    def test_fetch_vcenter_events_on_success(self, mocker):
        mocker.patch('migrationmonitor.common.reporter.Reporter')

        fake_settings = mocker.patch('migrationmonitor.settings')
        fake_settings.VCENTER = {
            "EVENTS_BUFFER_LENGTH": 1000,
            "EVENTS_HISTORY_WINDOW_LOWER_BOUND": timedelta(minutes=7),
            "EVENTS_HISTORY_WINDOW_UPPER_BOUND": timedelta(minutes=1),
            "EVENTS_BATCH_SIZE": 100}

        event_filter_spec = mocker.stub()
        event_filter_spec.time = mocker.stub()
        EventFilterSpec = mocker.patch('pyVmomi.vim.event.EventFilterSpec')
        EventFilterSpec.return_value = event_filter_spec
        ByEntity = mocker.patch('pyVmomi.vim.event.EventFilterSpec.ByEntity')
        _is_migration_event = mocker.patch.object(
            monitor, '_is_migration_event')
        _is_migration_event.return_value = True

        recurcion_optional_all = mocker.patch(
            'pyVmomi.vim.event.EventFilterSpec.RecursionOption.all')

        ByTime = mocker.patch('pyVmomi.vim.event.EventFilterSpec.ByTime')

        vcenter_monitor = monitor.VCenterMonitor()

        vcenter_monitor.vc_connect = mocker.stub()
        vcenter_monitor.vc_connect.content = mocker.stub()
        vcenter_monitor.vc_connect.content.rootFolder = mocker.stub()

        vcenter_monitor.vc_connect.content.eventManager = mocker.stub()
        event_manager = vcenter_monitor.vc_connect.content.eventManager
        event_manager.CreateCollectorForEvents = mocker.stub()

        event_collector = event_manager.CreateCollectorForEvents.return_value
        event_collector.SetCollectorPageSize = mocker.stub()
        event_collector.ResetCollector = mocker.stub()
        event_collector.ReadPreviousEvents = mocker.stub()
        event_collector.ReadPreviousEvents.return_value = []
        fake_events = ['foo', 'bar']
        event_collector.latestPage = fake_events

        test_result = vcenter_monitor._fetch_vcenter_events()

        EventFilterSpec.assert_called_once_with()
        ByEntity.assert_called_once_with()
        assert ByEntity.return_value.entity == \
            vcenter_monitor.vc_connect.content.rootFolder
        assert ByEntity.return_value.recursion == recurcion_optional_all
        assert EventFilterSpec.return_value.entity == ByEntity.return_value
        ByTime.assert_called_once_with()
        assert event_filter_spec.time == ByTime.return_value
        event_manager.CreateCollectorForEvents.assert_called_once_with(
            EventFilterSpec.return_value)
        event_collector.SetCollectorPageSize.assert_called_once_with(
            fake_settings.VCENTER["EVENTS_BATCH_SIZE"])
        event_collector.ResetCollector.assert_called_once_with()
        event_collector.ReadPreviousEvents.assert_called_once_with(
            fake_settings.VCENTER["EVENTS_BATCH_SIZE"])
        assert test_result == fake_events
