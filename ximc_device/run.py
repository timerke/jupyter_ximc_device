from ximc_device import ControlPanel, utils as ut, XimcDevice


def run_app() -> None:
    device_uri, is_virtual = ut.search_device()
    device = XimcDevice(device_uri, is_virtual)
    ut.print_device_info_in_widgets(device)
    control_panel = ControlPanel(device)
    control_panel
