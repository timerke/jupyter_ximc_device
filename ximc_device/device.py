import ctypes
import logging
import sys
import time
from typing import Any, Dict, List, Optional, Tuple
import libximc
from ximc_device import utils as ut


logging.basicConfig(format="[%(asctime)s %(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO)


def check_open(func):

    def wrapper(self, *args, **kwargs):
        if self.device_id > 0:
            return func(self, *args, **kwargs)
        logging.info("Device not open")

    return wrapper


class XimcDevice:
    """
    Class to control XIMC controller.
    """

    ACCEL_IN_STEPS: int = 1
    ACCEL_IN_USER_UNIT: float = 1
    ANTIPLAY_SPEED_IN_STEPS: int = 5
    ANTIPLAY_SPEED_IN_USER_UNIT: float = 5
    CONTROLLER_NAME: str = "VirtualXimc"
    DECEL_IN_STEPS: int = 1
    DECEL_IN_USER_UNIT: float = 1
    SPEED_IN_STEPS: int = 5
    SPEED_IN_USER_UNIT: float = 5
    UANTIPLAY_SPEED_IN_STEPS: int = 0
    USER_MULTIPLIER: float = 1 / 400
    USPEED_IN_STEPS: int = 0

    def __init__(self, device_uri: str, is_virtual: bool, user_multiplier: float = None, defer_open: bool = False
                 ) -> None:
        """
        :param device_uri: URI of device to open;
        :param is_virtual: if True then device is virtual;
        :param user_multiplier:
        :param defer_open: if True then device will not be opened.
        """

        self._device_id: int = -1
        self._device_uri: str = device_uri
        self._is_virtual: bool = is_virtual
        self._user_multiplier: float = 1 / user_multiplier if user_multiplier else self.USER_MULTIPLIER
        self._user_unit: libximc.calibration_t = libximc.calibration_t()
        if not defer_open:
            self.open_device()

    @property
    def device_id(self) -> int:
        return self._device_id

    @property
    def device_uri(self) -> str:
        return self._device_uri

    def _get_bootloader_or_firmware_version(self, firmware: bool = False) -> str:
        """
        :param firmware: if True then firmware version will be returned.
        :return: firmware or bootloader version.
        """

        func = libximc.lib.get_firmware_version if firmware else libximc.lib.get_bootloader_version
        major = ctypes.c_uint()
        minor = ctypes.c_uint()
        release = ctypes.c_uint()
        if func(self._device_id, ctypes.byref(major), ctypes.byref(minor), ctypes.byref(release)) == libximc.Result.Ok:
            return f"{major.value}.{minor.value}.{release.value}"
        return "None"

    def _get_controller_name(self) -> str:
        """
        :return: friendly controller name.
        """

        controller_name = libximc.controller_name_t()
        if libximc.lib.get_controller_name(self._device_id, ctypes.byref(controller_name)) == libximc.Result.Ok:
            return controller_name.ControllerName.decode()
        logging.warning("Failed to get controller name")
        return "None"

    def _get_device_information(self) -> List[Tuple[str, str]]:
        """
        :return: main device information.
        """

        device_information = libximc.device_information_t()
        result = libximc.lib.get_device_information(self._device_id, ctypes.byref(device_information))
        if result == libximc.Result.Ok:
            return [("Manufacturer", ctypes.string_at(device_information.Manufacturer).decode()),
                    ("Manufacturer ID", ctypes.string_at(device_information.ManufacturerId).decode()),
                    ("Product description", ctypes.string_at(device_information.ProductDescription).decode()),
                    ("Hardware version", f"{device_information.Major}.{device_information.Minor}."
                                         f"{device_information.Release}")]
        return [("Manufacturer", "None"),
                ("Manufacturer ID", "None"),
                ("Product description", "None"),
                ("Hardware version", "None")]

    def _get_engine_microstep_mode(self) -> int:
        """
        :return: engine microstep mode.
        """

        engine_settings = libximc.engine_settings_t()
        if libximc.lib.get_engine_settings(self._device_id, ctypes.byref(engine_settings)) == libximc.Result.Ok:
            return engine_settings.MicrostepMode
        logging.warning("Failed to get engine settings")
        return 0

    def _get_serial_number(self) -> str:
        """
        :return: serial number of device.
        """

        serial_number = libximc.serial_number_t()
        if libximc.lib.get_serial_number(self._device_id, ctypes.byref(serial_number)) == libximc.Result.Ok:
            return str(serial_number.SN)
        return "None"

    def _set_controller_name(self) -> None:
        """
        Method sets default friendly controller name for virtual device.
        """

        controller_name = libximc.controller_name_t()
        controller_name.ControllerName = self.CONTROLLER_NAME.encode("utf-8")
        controller_name.CtrlFlags = ctypes.c_uint(0)
        if libximc.lib.set_controller_name(self._device_id, ctypes.byref(controller_name)) != libximc.Result.Ok:
            logging.warning("Failed to set friendly controller name %s", self.CONTROLLER_NAME)

    def _set_move_settings(self) -> None:
        """
        Method sets default motion settings for virtual device.
        """

        move_settings = libximc.move_settings_t()
        move_settings.Speed = ctypes.c_uint(self.SPEED_IN_STEPS)
        move_settings.uSpeed = ctypes.c_uint(self.USPEED_IN_STEPS)
        move_settings.Accel = ctypes.c_uint(self.ACCEL_IN_STEPS)
        move_settings.Decel = ctypes.c_uint(self.DECEL_IN_STEPS)
        move_settings.AntiplaySpeed = ctypes.c_uint(self.ANTIPLAY_SPEED_IN_STEPS)
        move_settings.uAntiplaySpeed = ctypes.c_uint(self.UANTIPLAY_SPEED_IN_STEPS)
        move_settings.MoveFlags = ctypes.c_uint(0)
        if libximc.lib.set_move_settings(self._device_id, ctypes.byref(move_settings)) != libximc.Result.Ok:
            logging.warning("Failed to set motion settings")

    def _set_move_settings_with_user_unit(self) -> None:
        """
        Method sets default motion settings with user unit for virtual device.
        """

        move_settings = libximc.move_settings_calb_t()
        move_settings.Speed = ctypes.c_float(self.SPEED_IN_USER_UNIT)
        move_settings.Accel = ctypes.c_float(self.ACCEL_IN_USER_UNIT)
        move_settings.Decel = ctypes.c_float(self.DECEL_IN_USER_UNIT)
        move_settings.AntiplaySpeed = ctypes.c_float(self.ANTIPLAY_SPEED_IN_USER_UNIT)
        move_settings.MoveFlags = ctypes.c_uint(0)
        if libximc.lib.set_move_settings_calb(self._device_id, ctypes.byref(move_settings),
                                              ctypes.byref(self._user_unit)) != libximc.Result.Ok:
            logging.warning("Failed to set motion settings with user unit")

    def _set_params_for_virtual(self) -> None:
        """
        Method sets default settings for virtual device.
        """

        self._set_move_settings()
        self._set_move_settings_with_user_unit()
        self._set_controller_name()
        self._set_position()

    def _set_position(self) -> None:
        """
        Method sets zero position for virtual device.
        """

        position = libximc.set_position_t()
        position.Position = ctypes.c_int(0)
        position.uPosition = ctypes.c_int(0)
        position.EncPosition = ctypes.c_longlong(0)
        position.PosFlags = ctypes.c_uint(0)
        if libximc.lib.set_position(self._device_id, ctypes.byref(position)) != libximc.Result.Ok or \
                libximc.lib.command_zero(self._device_id) != libximc.Result.Ok:
            logging.warning("Failed to set zero position")

    @check_open
    def check_moving(self) -> bool:
        """
        :return: True if device is moving.
        """

        params = self.get_params()
        return params.get("moving_status", 0) & libximc.MvcmdStatus.MVCMD_RUNNING

    @check_open
    def close_device(self) -> None:
        """
        Method closes device.
        """

        if libximc.lib.close_device(ctypes.byref(ctypes.c_int(self._device_id))) != libximc.Result.Ok:
            logging.warning("Failed to close device")

    @check_open
    def get_device_full_info(self) -> List[Tuple[str, str]]:
        """
        :return: full device information.
        """

        data = [("libximc version", ut.get_libximc_version())]
        data.extend(self._get_device_information())
        data.append(("Serial number", self._get_serial_number()))
        data.append(("Firmware version", self._get_bootloader_or_firmware_version(True)))
        data.append(("Bootloader version", self._get_bootloader_or_firmware_version(False)))
        data.append(("Friendly name", self._get_controller_name()))
        return data

    @check_open
    def get_params(self) -> Dict[str, Any]:
        status = libximc.status_t()
        if libximc.lib.get_status(self._device_id, ctypes.byref(status)) == libximc.Result.Ok:
            return {"moving_status": status.MvCmdSts,
                    "position": status.CurPosition,
                    "u_position": status.uCurPosition,
                    "speed": status.CurSpeed,
                    "u_speed": status.uCurSpeed,
                    "power_current": status.Ipwr,
                    "power_voltage": status.Upwr / 100,
                    "temperature": status.CurT / 10}
        return {}

    @check_open
    def get_params_in_user_unit(self) -> Dict[str, Any]:
        status = libximc.status_calb_t()
        if libximc.lib.get_status_calb(self._device_id, ctypes.byref(status), ctypes.byref(self._user_unit)) ==\
                libximc.Result.Ok:
            return {"moving_status": status.MvCmdSts,
                    "position": status.CurPosition,
                    "speed": status.CurSpeed,
                    "power_current": status.Ipwr,
                    "power_voltage": status.Upwr / 100,
                    "temperature": status.CurT / 10}
        return {}

    @check_open
    def get_position(self) -> Optional[int]:
        """
        :return: position of device in steps.
        """

        position = libximc.get_position_t()
        if libximc.lib.get_position(self._device_id, ctypes.byref(position)) == libximc.Result.Ok:
            return position.Position

    @check_open
    def get_position_in_user_unit(self) -> Optional[float]:
        """
        :return: position in user unit.
        """

        position = libximc.get_position_calb_t()
        if libximc.lib.get_position_calb(self._device_id, ctypes.byref(position), ctypes.byref(self._user_unit)) == \
                libximc.Result.Ok:
            return position.Position

    @check_open
    def move_left(self) -> None:
        """
        Method runs device to left.
        """

        if libximc.lib.command_left(self._device_id) != libximc.Result.Ok:
            logging.warning("Failed to start move to left")

    @check_open
    def move_right(self) -> None:
        """
        Method runs device to right.
        """

        if libximc.lib.command_right(self._device_id) != libximc.Result.Ok:
            logging.debug("Failed to start move to right")

    @check_open
    def move_to_position(self, position: int) -> None:
        """
        Method runs device to given position in steps.
        :param position: position to move.
        """

        if libximc.lib.command_move(self._device_id, position, 0) != libximc.Result.Ok:
            logging.warning("Failed to start move to position %d", position)

    @check_open
    def move_to_position_in_user_unit(self, position: float) -> None:
        """
        Method runs device to given position in user unit.
        :param position: position to move.
        """

        if libximc.lib.command_move_calb(self._device_id, ctypes.c_float(position), ctypes.byref(self._user_unit)) != \
                libximc.Result.Ok:
            logging.warning("Failed to start move to position %f in user units", position)

    def open_device(self) -> None:
        """
        Method opens device.
        """

        device_id = libximc.lib.open_device(self._device_uri.encode())
        if device_id <= 0:
            logging.warning("Failed to open device %s", self._device_uri)
            return
        self._device_id = device_id
        logging.debug("Device with ID %d was opened", self._device_id)

        self._user_unit = libximc.calibration_t()
        self._user_unit.A = self._user_multiplier
        self._user_unit.MicrostepMode = self._get_engine_microstep_mode()

        if self._is_virtual:
            self._set_params_for_virtual()

    @check_open
    def set_user_multiplier(self, multiplier: float) -> None:
        self._user_multiplier = 1 / multiplier
        self._user_unit.A = self._user_multiplier

    @check_open
    def stop_motion(self) -> None:
        if libximc.lib.command_sstp(self._device_id) != libximc.Result.Ok:
            logging.warning("Failed to stop moving")


if __name__ == "__main__":
    devices_type_and_uri = ut.search_devices()
    if not devices_type_and_uri:
        sys.exit(0)

    is_virtual = devices_type_and_uri[0][0].lower() == "virtual"
    device = XimcDevice(devices_type_and_uri[0][1], is_virtual)
    ut.print_device_info(device)

    POS_1 = 5
    print(f"\nPosition before moving to position {POS_1:.3f}: {device.get_position_in_user_unit():.3f}")
    device.move_to_position_in_user_unit(POS_1)
    while device.check_moving():
        print(f"\tMoving to {device.get_position_in_user_unit():.3f}")
        time.sleep(0.5)
    print(f"Position after moving to position {POS_1:.3f}: {device.get_position_in_user_unit():.3f}")

    POS_2 = -13
    print(f"\nPosition before moving to position {POS_2:.3f}: {device.get_position_in_user_unit():.3f}")
    device.move_to_position_in_user_unit(POS_2)
    while device.check_moving():
        print(f"\tMoving to {device.get_position_in_user_unit():.3f}")
        time.sleep(0.5)

    print(f"\nPosition before moving to right {device.get_position_in_user_unit():.3f}")
    device.move_right()
    i = 0
    while device.check_moving():
        print(f"\tMoving to {device.get_position_in_user_unit():.3f}")
        i += 1
        time.sleep(1)
        if i > 3:
            device.stop_motion()

    device.close_device()
