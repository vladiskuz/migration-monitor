from migrationmonitor.common import actor
from migrationmonitor.common import logger
from migrationmonitor.libvirt import monitor
from migrationmonitor.libvirt import utils


class TestLibvirtMonitor(object):

    def test_start_on_success(self, mocker):
        mocker.patch('migrationmonitor.common.db.InfluxDBActor')
        start_event_loop = mocker.patch.object(utils, 'start_event_loop')

        _start = mocker.patch.object(monitor.LibvirtMonitor, '_start')
        fake_settings = mocker.patch('migrationmonitor.settings')
        fake_settings.LIBVIRT = {'URI': ['URI1', 'URI2']}
        libvirt_monitor = monitor.LibvirtMonitor()
        libvirt_monitor.start()

        start_event_loop.assert_called_once_with()
        assert _start.call_count == 2
        expected_args_list = \
            [mocker.call(x) for x in fake_settings.LIBVIRT['URI']]
        assert _start.call_args_list == expected_args_list

    def test_underscore_start_on_success(self, mocker):
        fake_db_actor = mocker.stub()
        fake_db_actor.start = mocker.stub()
        InfluxDBActor = mocker.patch(
            'migrationmonitor.common.db.InfluxDBActor')
        InfluxDBActor.return_value = fake_db_actor

        fake_conn = mocker.stub()
        openReadOnly = mocker.patch('libvirt.openReadOnly')
        openReadOnly.return_value = fake_conn
        log_info = mocker.patch.object(logger, 'info')
        _register_libvirt_callbacks = mocker.patch.object(
            monitor.LibvirtMonitor,
            '_register_libvirt_callbacks')
        fake_doms_watcher = mocker.stub()
        fake_doms_watcher.start = mocker.stub()
        LibvirtDomainsWatcher = mocker.patch(
            'migrationmonitor.libvirt.watcher.LibvirtDomainsWatcher')
        LibvirtDomainsWatcher.return_value = fake_doms_watcher
        fake_uri = 'fake_uri'

        libvirt_monitor = monitor.LibvirtMonitor()
        libvirt_monitor._start(fake_uri)

        openReadOnly.assert_called_once_with(fake_uri)
        log_info.assert_called_once_with("Connecting to %s", fake_uri)
        assert fake_conn in libvirt_monitor.connections
        _register_libvirt_callbacks.assert_called_once_with(fake_conn)
        LibvirtDomainsWatcher.assert_called_once_with(
            fake_conn,
            libvirt_monitor.migration_monitors,
            fake_db_actor)
        fake_doms_watcher.start.assert_called_once_with()

    def test_register_libvirt_callbacks_on_success(self, mocker):
        mocker.patch('migrationmonitor.common.db.InfluxDBActor')
        fake_conn = mocker.stub()
        fake_conn.registerCloseCallback = mocker.stub()
        _conn_close_handler = mocker.patch.object(
            monitor.LibvirtMonitor,
            '_conn_close_handler')
        fake_conn.domainEventRegisterAny = mocker.stub()
        LIBVIRT_CONST = mocker.patch('libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE')
        _domain_event_handler = mocker.patch.object(
            monitor.LibvirtMonitor,
            '_domain_event_handler')
        fake_conn.setKeepAlive = mocker.stub()

        libvirt_monitor = monitor.LibvirtMonitor()
        libvirt_monitor._register_libvirt_callbacks(fake_conn)

        fake_conn.registerCloseCallback.assert_called_once_with(
            _conn_close_handler,
            None)
        fake_conn.domainEventRegisterAny.assert_called_once_with(
            None,
            LIBVIRT_CONST,
            _domain_event_handler,
            None)
        fake_conn.setKeepAlive.assert_called_once_with(5, 3)

    def test_domain_event_handler_with_values_equal_one(self, mocker):
        fake_db_actor = mocker.stub()
        fake_db_actor.start = mocker.stub()
        fake_db_actor.tell = mocker.stub()
        InfluxDBActor = mocker.patch(
            'migrationmonitor.common.db.InfluxDBActor')
        InfluxDBActor.return_value = fake_db_actor
        fake_settings = mocker.patch('migrationmonitor.settings')
        fake_settings.INFLUXDB = {"EVENTS_MEASUREMENT": "fake_measurement"}

        fake_domain = mocker.stub()
        fake_domain.ID = mocker.stub()
        fake_domain.ID.return_value = 12345
        fake_domain.name = mocker.stub()
        fake_domain.name.return_value = 'fake_domain_name'

        log_info = mocker.patch.object(logger, 'info')

        fake_conn = mocker.stub()
        fake_event = 2
        fake_detail = 1
        fake_opaque = mocker.stub()

        tags = {
            "domain_id": fake_domain.ID.return_value,
            "domain_name": fake_domain.name.return_value,
            "event": monitor.EVENT_STRINGS[fake_event],
            "event_detail": monitor.EVENT_DETAILS[fake_event][fake_detail]}

        libvirt_monitor = monitor.LibvirtMonitor()
        libvirt_monitor._domain_event_handler(
            fake_conn,
            fake_domain,
            fake_event,
            fake_detail,
            fake_opaque)

        fake_domain.ID.assert_called_once_with()
        fake_domain.name.assert_called_once_with()
        log_info.assert_called_once_with(
            "====> (%s)%s %s %s",
            fake_domain.ID.return_value,
            fake_domain.name.return_value,
            monitor.EVENT_STRINGS[fake_event],
            monitor.EVENT_DETAILS[fake_event][fake_detail])
        fake_db_actor.tell.assert_called_once_with((
            tags,
            {"value": 1},
            fake_settings.INFLUXDB["EVENTS_MEASUREMENT"]))

    def test_domain_event_handler_with_values_equal_zero(self, mocker):
        fake_db_actor = mocker.stub()
        fake_db_actor.start = mocker.stub()
        fake_db_actor.tell = mocker.stub()
        InfluxDBActor = mocker.patch(
            'migrationmonitor.common.db.InfluxDBActor')
        InfluxDBActor.return_value = fake_db_actor
        fake_settings = mocker.patch('migrationmonitor.settings')
        fake_settings.INFLUXDB = {"EVENTS_MEASUREMENT": "fake_measurement"}

        fake_domain = mocker.stub()
        fake_domain.ID = mocker.stub()
        fake_domain.ID.return_value = 12345
        fake_domain.name = mocker.stub()
        fake_domain.name.return_value = 'fake_domain_name'

        log_info = mocker.patch.object(logger, 'info')

        fake_conn = mocker.stub()
        fake_event = 3
        fake_detail = 3
        fake_opaque = mocker.stub()
        tags = {
            "domain_id": fake_domain.ID.return_value,
            "domain_name": fake_domain.name.return_value,
            "event": monitor.EVENT_STRINGS[fake_event],
            "event_detail": monitor.EVENT_DETAILS[fake_event][fake_detail]}

        libvirt_monitor = monitor.LibvirtMonitor()
        libvirt_monitor._domain_event_handler(
            fake_conn,
            fake_domain,
            fake_event,
            fake_detail,
            fake_opaque)

        fake_domain.ID.assert_called_once_with()
        fake_domain.name.assert_called_once_with()
        log_info.assert_called_once_with(
            "====> (%s)%s %s %s",
            fake_domain.ID.return_value,
            fake_domain.name.return_value,
            monitor.EVENT_STRINGS[fake_event],
            monitor.EVENT_DETAILS[fake_event][fake_detail])
        fake_db_actor.tell.assert_called_once_with((
            tags,
            {"value": 0},
            fake_settings.INFLUXDB["EVENTS_MEASUREMENT"]))

    def test_conn_close_handler_with_reason_equal_zero(self, mocker):
        mocker.patch('migrationmonitor.common.db.InfluxDBActor')

        fake_settings = mocker.patch('migrationmonitor.settings')
        fake_settings.INFLUXDB = {"RECONNECT": 9000}

        fake_conn = mocker.stub()
        fake_conn.getURI = mocker.stub()
        fake_conn.getURI.return_value = 'fake_uri'

        log_error = mocker.patch.object(logger, 'error')

        fake_defer = mocker.patch.object(actor, 'defer')

        fake_reason = 0
        fake_opaque = mocker.stub()

        libvirt_monitor = monitor.LibvirtMonitor()
        libvirt_monitor._conn_close_handler(
            fake_conn,
            fake_reason,
            fake_opaque)

        log_error.assert_called_once_with(
            "Closed connection: %s: %s",
            fake_conn.getURI.return_value,
            monitor.REASON_STRINGS[fake_reason])
        fake_defer.assert_called_once_with(
                libvirt_monitor._reconnect,
                seconds=fake_settings.INFLUXDB['RECONNECT'])

    def test_conn_close_handler_with_reason_not_equal_zero(self, mocker):
        mocker.patch('migrationmonitor.common.db.InfluxDBActor')

        fake_settings = mocker.patch('migrationmonitor.settings')
        fake_settings.INFLUXDB = {"RECONNECT": 9000}

        fake_conn = mocker.stub()
        fake_conn.getURI = mocker.stub()
        fake_conn.getURI.return_value = 'fake_uri'

        log_error = mocker.patch.object(logger, 'error')

        fake_defer = mocker.patch.object(actor, 'defer')

        fake_reason = 1
        fake_opaque = mocker.stub()

        libvirt_monitor = monitor.LibvirtMonitor()
        libvirt_monitor._conn_close_handler(
            fake_conn,
            fake_reason,
            fake_opaque)

        log_error.assert_called_once_with(
            "Closed connection: %s: %s",
            fake_conn.getURI.return_value,
            monitor.REASON_STRINGS[fake_reason])
        fake_defer.assert_not_called()

    def test_reconnect_on_success(self, mocker):
        mocker.patch('migrationmonitor.common.db.InfluxDBActor')

        fake_conn = mocker.stub()
        fake_conn.getURI = mocker.stub()
        fake_conn.getURI.return_value = 'fake_uri'

        log_debug = mocker.patch.object(logger, 'debug')

        _start = mocker.patch.object(monitor.LibvirtMonitor, '_start')

        libvirt_monitor = monitor.LibvirtMonitor()
        libvirt_monitor.connections.append(fake_conn)
        libvirt_monitor._reconnect(fake_conn)

        fake_conn.getURI.assert_called_once_with()
        log_debug.assert_called_once_with(
            "Reconnection %s" % (fake_conn.getURI.return_value))
        assert fake_conn not in libvirt_monitor.connections
        _start.assert_called_once_with(fake_conn.getURI.return_value)

    def test_stop_on_success(self, mocker):
        fake_db_actor = mocker.stub()
        fake_db_actor.start = mocker.stub()
        fake_db_actor.stop = mocker.stub()
        InfluxDBActor = mocker.patch(
            'migrationmonitor.common.db.InfluxDBActor')
        InfluxDBActor.return_value = fake_db_actor

        mocker.patch.object(logger, 'debug')

        fake_dom_actor1 = mocker.stub()
        fake_dom_actor1.stop = mocker.stub()
        fake_dom_actor2 = mocker.stub()
        fake_dom_actor2.stop = mocker.stub()

        fake_conn1 = mocker.stub()
        fake_conn1.getURI = mocker.stub()
        fake_conn1.close = mocker.stub()
        fake_conn2 = mocker.stub()
        fake_conn2.getURI = mocker.stub()
        fake_conn2.close = mocker.stub()

        libvirt_monitor = monitor.LibvirtMonitor()
        libvirt_monitor.migration_monitors = {
            'dom_1': fake_dom_actor1,
            'dom_2': fake_dom_actor2
        }
        libvirt_monitor.connections = [fake_conn1, fake_conn2]
        libvirt_monitor.stop()

        fake_dom_actor1.stop.assert_called_once_with()
        fake_dom_actor2.stop.assert_called_once_with()
        fake_db_actor.stop.assert_called_once_with()
        fake_conn1.close.assert_called_once_with()
        fake_conn2.close.assert_called_once_with()
