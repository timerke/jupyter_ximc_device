import configparser
from typing import Any, Dict, List, Optional, Tuple
from IPython.display import clear_output, display
from ipywidgets import widgets
from ximc_device import utils as ut
from ximc_device.device import XimcDevice


class OpenPanel:
    """
    Class for panel with widgets to open and close device.
    """

    DEFAULT_USER_UNITS_MULTIPLIER: float = 400

    def __init__(self) -> None:
        self._device: Optional[XimcDevice] = None
        self._devices_type_and_uri: List[Tuple[str, str]] = []
        self._create_widgets()
        self.search_devices()

    @property
    def device(self) -> Optional[XimcDevice]:
        return self._device

    def _create_widgets(self) -> None:
        """
        Method creates widgets on panel.
        """

        self.button_refresh = widgets.Button(description="Refresh", icon="rotate-right",
                                             tooltip="Refresh list of available devices")
        self.button_refresh.on_click(lambda _: self.search_devices())
        self.drop_down_devices = widgets.Dropdown(options=[], description="Devices:")
        self.button_open = widgets.Button(description="Open device", icon="unlock")
        self.button_open.on_click(lambda _: self.open_device())
        self.button_close = widgets.Button(description="Close device", icon="lock")
        self.button_close.on_click(lambda _: self.close_device())
        h_box_1 = widgets.HBox([self.button_refresh, self.drop_down_devices, self.button_open, self.button_close])

        self.label = widgets.Label(value="Enter user units or upload a config file for your motor")
        self.float_text_user_units = widgets.BoundedFloatText(
            value=self.DEFAULT_USER_UNITS_MULTIPLIER, description="", tooltip="Number of motor steps in one mm",
            min=1, max=1000000, layout=widgets.Layout(width="100px"), continuous_update=False)
        self.float_text_user_units.observe(self.handle_user_units_change, names="value")
        self.file_upload = widgets.FileUpload(description="Upload config file", accept=".cfg", multiple=False,
                                              layout=widgets.Layout(width="250px"))
        self.file_upload.observe(self.handle_upload_config_file)
        h_box_2 = widgets.HBox([self.label, self.float_text_user_units, self.file_upload])

        self.output = widgets.Output()
        v_box = widgets.VBox([h_box_1, h_box_2, self.output])
        display(v_box)

    def close_device(self) -> None:
        """
        Method closes device.
        """

        with self.output:
            clear_output(wait=True)
            if not self._device:
                ut.print_flush("No open devices")
                return
            self._device.close_device()
            ut.print_flush(f"Device {self._device.device_uri} was closed")
            self._device = None

    def handle_upload_config_file(self, change: Dict[str, Any]) -> None:
        """
        Method handles the event of uploading a configuration file with user units.
        :param change: dictionary with data.
        """

        if not change["new"] or "value" not in change["new"]:
            return
        with self.output:
            clear_output(wait=True)
            try:
                parser = configparser.ConfigParser()
                parser.read_string(change["new"]["value"][0]["content"].tobytes().decode())
                multiplier = float(parser["User_units"]["Unit_multiplier"])
            except Exception as exc:
                ut.print_flush(f"Failed to read user units from file {change['new']['value'][0]['name']}: {exc}")
            else:
                self.float_text_user_units.value = multiplier
                if self._device:
                    self._device.set_user_multiplier(multiplier)

    def handle_user_units_change(self, change: Dict[str, Any]) -> None:
        """
        Method handles user units change event.
        :param change: dictionary with data.
        """

        if change["new"] > self.float_text_user_units.max:
            multiplier = self.float_text_user_units.max
        elif change["new"] < self.float_text_user_units.min:
            multiplier = self.float_text_user_units.min
        else:
            multiplier = change["new"]
        if self._device:
            self._device.set_user_multiplier(multiplier)

    def open_device(self) -> None:
        """
        Method opens selected device.
        """

        with self.output:
            clear_output(wait=True)
            if not self.drop_down_devices.value:
                ut.print_flush("No device is selected. Select a device to open it")
                return
            for device_type, device_uri in self._devices_type_and_uri:
                if f"{device_uri} ({device_type})" == self.drop_down_devices.value:
                    is_virtual = device_type.lower() == "virtual"
                    self._device = XimcDevice(device_uri, is_virtual, self.float_text_user_units.value)
                    if self._device.device_id > 0:
                        ut.print_flush(f"Device {self._device.device_uri} was opened")
                        ut.print_device_info_in_widgets(self._device)
                    else:
                        self._device = None
                        ut.print_flush(f"Failed to open device {device_uri}")
                    break

    def search_devices(self) -> None:
        """
        Method searches for devices and updates combo box widget.
        """

        with self.output:
            clear_output(wait=True)
            self._devices_type_and_uri = ut.search_devices()
        self.drop_down_devices.options = [f"{device_uri} ({device_type})" for device_type, device_uri in
                                          self._devices_type_and_uri]
