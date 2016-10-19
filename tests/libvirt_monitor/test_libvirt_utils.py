from migrationmonitor.libvirt_monitor import utils


def test_start_event_loop(mocker):
    virEventRegisterDefaultImpl = mocker.patch(
        'libvirt.virEventRegisterDefaultImpl')

    event_loop_thread = mocker.stub()
    event_loop_thread.setDaemon = mocker.stub()
    event_loop_thread.start = mocker.stub()

    Thread = mocker.patch('threading.Thread')
    Thread.return_value = event_loop_thread
    run_native_event_loop = mocker.patch.object(utils, 'run_native_event_loop')

    utils.start_event_loop()

    virEventRegisterDefaultImpl.assert_called_once_with()
    Thread.assert_called_once_with(
        target=run_native_event_loop,
        name="libvirtEventLoop")
    event_loop_thread.setDaemon.assert_called_once_with(True)
    event_loop_thread.start.assert_called_once_with()


def test_get_dom_name_by_id(mocker):
    fake_dom = mocker.stub()
    fake_dom.name = mocker.stub()

    fake_conn = mocker.stub()
    fake_conn.lookupByID = mocker.stub()
    fake_conn.lookupByID.return_value = fake_dom
    dom_id = 12345

    dom_name = utils.get_dom_name_by_id(fake_conn, dom_id)

    assert dom_name == fake_dom.name.return_value
    fake_conn.lookupByID.assert_called_once_with(dom_id)
