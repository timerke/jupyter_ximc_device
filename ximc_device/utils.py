import ctypes
import os
import sys
from typing import Any, Optional, Tuple
import ipywidgets as widgets
from IPython.display import display
import libximc


def _get_virtual_device_file() -> str:
    virtaul_device_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "VirtualDevice")
    if os.altsep:
        virtaul_device_file = virtaul_device_file.replace(os.sep, os.altsep)
    return virtaul_device_file


def get_libximc_version() -> str:
    string_buffer = ctypes.create_string_buffer(64)
    libximc.lib.ximc_version(string_buffer)
    return string_buffer.raw.decode().rstrip("\0")


def print_device_info(device) -> None:
    """
    Output of information about the device.
    :param device: device.
    """

    info = device.get_device_full_info()
    print_flush("\nDevice information")
    for item_name, item_value in info:
        print_flush(f"\t{item_name}: {item_value}")


def print_device_info_in_widgets(device) -> None:
    """
    Output of information about the device in widgets.
    :param device: device.
    """

    info = device.get_device_full_info()
    style = {"description_width": "150px"}
    text_widgets = [widgets.HTML("<h2>Device information</h2>")]
    for item_name, item_value in info:
        text_widgets.append(widgets.Text(value=item_value, description=f"{item_name}:", style=style, disabled=True))
    layout = widgets.VBox(text_widgets)
    display(layout)


def print_flush(text: Any) -> None:
    print(text, flush=True)


def search_device() -> Tuple[Optional[str], bool]:
    """
    Automatic search of controller. If no real controllers are found, a virtual
    controller will be returned.
    :return: controller name and flag whether the controller is virtual.
    """

    print_flush("Searching for controllers...")
    # Set bindy (network) keyfile. Must be called before any call to "enumerate_devices" or "open_device" if you
    # wish to use network-attached controllers. Accepts both absolute and relative paths, relative paths are resolved
    # relative to the process working directory. If you do not need network devices then "set_bindy_key" is optional.
    # In Python make sure to pass byte-array object to this function (b"string literal").
    result = libximc.lib.set_bindy_key("keyfile.sqlite".encode("utf-8"))
    if result != libximc.Result.Ok:
        print_flush("keyfile not found")

    # This is device search and enumeration with probing. It gives more information about devices
    probe_flags = libximc.EnumerateFlags.ENUMERATE_PROBE + libximc.EnumerateFlags.ENUMERATE_NETWORK
    enum_hints = b"addr="  # use this hint string for broadcast enumerate
    devices = libximc.lib.enumerate_devices(probe_flags, enum_hints)

    device_count = libximc.lib.get_device_count(devices)
    print_flush(f"Device count: {device_count}")

    controller_name = libximc.controller_name_t()
    for device_index in range(device_count):
        device_name = libximc.lib.get_device_name(devices, device_index)
        result = libximc.lib.get_enumerate_device_controller_name(devices, device_index, ctypes.byref(controller_name))
        if result == libximc.Result.Ok:
            print_flush(f"Device #{device_index}, name: {device_name}, "
                        f"controller name: {controller_name.ControllerName}")

    is_virtual = False
    device_name_to_open = None
    if device_count > 0:
        device_name_to_open = libximc.lib.get_device_name(devices, 0)
    elif sys.version_info >= (3, 0):
        virtual_device_file = _get_virtual_device_file()
        device_name_to_open = f"xi-emu:///{virtual_device_file}"
        is_virtual = True
        print_flush("Real usb controller not found.\nReal ethernet controller not found.\n"
                    "Virtual controller found.")

    if not device_name_to_open:
        print_flush("Could not find any device")
        return None, is_virtual

    if isinstance(device_name_to_open, bytes):
        device_name_to_open = device_name_to_open.decode()

    return device_name_to_open, is_virtual
