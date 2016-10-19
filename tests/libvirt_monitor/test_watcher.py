import time

import libvirt

from migrationmonitor.common import logger
from migrationmonitor.libvirt_monitor import utils
from migrationmonitor.libvirt_monitor import watcher


class TestLibvirtDomainWatcher(object):

    def test_init_on_success(self, mocker):
        doms_job_monitor = mocker.stub()
        doms_job_monitor.start = mocker.stub()
        DomainsJobMonitorActorCreator = mocker.patch.object(
            watcher, 'DomainsJobMonitorActorCreator')
        DomainsJobMonitorActorCreator.return_value = doms_job_monitor

        fake_conn = mocker.stub()
        fake_migration_monitors = mocker.stub()
        fake_db_actor = mocker.stub()

        watcher.LibvirtDomainsWatcher(
            fake_conn,
            fake_migration_monitors,
            fake_db_actor)

        DomainsJobMonitorActorCreator.assert_called_once_with(
            fake_conn,
            fake_migration_monitors,
            fake_db_actor)
        doms_job_monitor.start.assert_called_once_with()


class TestDomainsJobMonitorActorCreator(object):

    def test_on_receive_on_success(self, mocker):
        fake_conn = mocker.stub()
        fake_conn.getURI = mocker.stub()
        fake_migration_monitors = {}
        fake_db_actor = mocker.stub()

        fake_dom_actor = mocker.stub()
        fake_dom_actor.start = mocker.stub()
        fake_dom_actor.tell = mocker.stub()
        DomainJobMonitorActor = mocker.patch.object(
            watcher, 'DomainJobMonitorActor')
        DomainJobMonitorActor.return_value = fake_dom_actor

        get_dom_name_by_id = mocker.patch.object(utils, 'get_dom_name_by_id')
        log_info = mocker.patch.object(logger, 'info')
        fake_dom_id = 12345

        doms_job_monitor = watcher.DomainsJobMonitorActorCreator(
            fake_conn,
            fake_migration_monitors,
            fake_db_actor)
        doms_job_monitor._on_receive(('cmd', fake_dom_id))

        DomainJobMonitorActor.assert_called_once_with(
            fake_conn,
            fake_dom_id,
            fake_migration_monitors,
            fake_db_actor)
        fake_dom_actor.start.assert_called_once_with()
        fake_dom_actor.tell.assert_called_once_with(
                ('start_job_monitoring', fake_dom_id))
        log_info.assert_called_once_with(
            "Start job monitoring for domain (%s)%s on %s",
            fake_dom_id,
            get_dom_name_by_id.return_value,
            fake_conn.getURI.return_value)
        get_dom_name_by_id.assert_called_once_with(fake_conn, fake_dom_id)


class TestDomainJobMonitorActor(object):
    def test_on_receive_on_success(self, mocker):
        fake_dom = mocker.stub()
        fake_dom.jobStats = mocker.stub()
        fake_dom.name = mocker.stub()

        fake_conn = mocker.stub()
        fake_conn.lookupByID = mocker.stub()
        fake_conn.lookupByID.return_value = fake_dom

        fake_settings = mocker.patch('migrationmonitor.settings')
        fake_settings.MEASUREMENT = {"JOBINFO_MEASUREMENT": "fake_measurement"}
        fake_settings.LIBVIRT = {"POLL_FREQ": 9000}

        fake_dom_id = 12345
        fake_migration_monitors = {}
        fake_reporter = mocker.stub()
        fake_reporter.tell = mocker.stub()

        log_debug = mocker.patch.object(logger, 'debug')
        time_sleep = mocker.patch.object(time, 'sleep')

        tell = mocker.patch.object(watcher.DomainJobMonitorActor, 'tell')

        dom_actor = watcher.DomainJobMonitorActor(
            fake_conn,
            fake_dom_id,
            fake_migration_monitors,
            fake_reporter)
        dom_actor._on_receive(('foo', fake_dom_id))

        fake_conn.lookupByID.assert_called_once_with(fake_dom_id)
        fake_dom.jobStats.assert_called_once_with()
        log_debug.assert_called_once_with(
            "jobStats: {0}".format(fake_dom.jobStats.return_value))
        fake_reporter.tell.assert_called_once_with({
            "tags": {
                "domain_id": fake_dom_id,
                "domain_name": fake_dom.name.return_value},
            "values": fake_dom.jobStats.return_value,
            "measurement": fake_settings.MEASUREMENT["JOBINFO_MEASUREMENT"]})
        time_sleep.assert_called_once_with(fake_settings.LIBVIRT["POLL_FREQ"])
        tell.assert_called_once_with(("continue", fake_dom_id))

    def test_on_receive_with_exception_on_success(self, mocker):
        fake_conn = mocker.stub()
        fake_conn.lookupByID = mocker.stub()
        fake_conn.lookupByID.side_effect = libvirt.libvirtError('foo')

        fake_dom_id = 12345
        fake_migration_monitors = {fake_dom_id: 'fake_domain'}
        fake_db_actor = mocker.stub()

        log_debug = mocker.patch.object(logger, 'debug')
        stop = mocker.patch.object(watcher.DomainJobMonitorActor, 'stop')

        dom_actor = watcher.DomainJobMonitorActor(
            fake_conn,
            fake_dom_id,
            fake_migration_monitors,
            fake_db_actor)
        dom_actor._on_receive(('foo', fake_dom_id))

        stop.assert_called_once_with()
        log_debug.assert_called_once_with(
            "Destroy DomJobMonitorActor for domain with id %s",
            fake_dom_id)
        assert fake_dom_id not in dom_actor.migration_monitors
