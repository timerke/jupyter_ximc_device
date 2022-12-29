import queue
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
import ipywidgets as widgets
import matplotlib.pyplot as plt
from IPython.display import clear_output, display
from ximc_device import utils as ut
from ximc_device.open_panel import OpenPanel


class ControlPanel:
    """
    Class for panel with widgets to move device.
    """

    USER_UNIT: str = "user unit"

    def __init__(self, open_panel: Optional[OpenPanel] = None) -> None:
        """
        :param open_panel: panel with widgets to open and close device.
        """

        self._user_unit: str = self.USER_UNIT
        self._open_panel: Optional[OpenPanel] = open_panel
        v_box = self._create_widgets()
        self._figures_thread: FiguresOutput = FiguresOutput(self._user_unit)
        self._figures_thread.start_thread()
        display(widgets.VBox([v_box, self._figures_thread.box]))
        if self._open_panel:
            self._open_panel.set_control_panel(self)

    def _check_device(self) -> bool:
        """
        Method checks that the device is open and can be operated.
        :return: True if device is open.
        """

        if self._open_panel and self._open_panel.device:
            with self.output:
                clear_output()
            return True
        with self.output:
            clear_output(wait=True)
            ut.print_flush("To move motor, you must first open device")
        return False

    def _create_widgets(self) -> widgets.VBox:
        """
        Method creates widgets for control panel.
        :return: box with control widgets.
        """

        style = {"description_width": "150px"}

        self.button_move_left = widgets.Button(description="Move left", icon="arrow-left")
        self.button_move_left.on_click(lambda _: self.move_left())
        self.button_stop = widgets.Button(description="Stop", icon="stop")
        self.button_stop.on_click(lambda _: self.stop_motion())
        self.button_move_right = widgets.Button(description="Move right", icon="arrow-right")
        self.button_move_right.on_click(lambda _: self.move_right())
        h_box_1 = widgets.HBox([self.button_move_left, self.button_stop, self.button_move_right])

        self.int_text_widget_position = widgets.BoundedIntText(value=0, min=-1000, max=1000, step=1,
                                                               description=f"Position, {self._user_unit}", style=style)
        self.button_move_to = widgets.Button(description="Move to")
        self.button_move_to.on_click(lambda _: self.move_to_position())
        h_box_2 = widgets.HBox([self.button_move_to, self.int_text_widget_position])

        self.int_text_widget_shift = widgets.BoundedIntText(value=0, min=-1000, max=1000, step=1,
                                                            description=f"Shift, {self._user_unit}", style=style)
        self.button_shift_on = widgets.Button(description="Shift on")
        self.button_shift_on.on_click(lambda _: self.move_on_shift())
        h_box_3 = widgets.HBox([self.button_shift_on, self.int_text_widget_shift])

        self.output = widgets.Output()
        return widgets.VBox([h_box_1, h_box_2, h_box_3, self.output])

    def move_left(self) -> None:
        """
        Method runs motion to left.
        """

        if self._check_device():
            self._open_panel.device.stop_motion()
            self._figures_thread.add_task(self._open_panel.device.move_left, device=self._open_panel.device)

    def move_on_shift(self) -> None:
        """
        Method runs motion on given shift.
        """

        if self._check_device():
            self._open_panel.device.stop_motion()
            shift = self.int_text_widget_shift.value
            current_position = self._open_panel.device.get_position_in_user_unit()
            position_to_move = current_position + shift
            self._figures_thread.add_task(self._open_panel.device.move_to_position_in_user_unit, position_to_move,
                                          device=self._open_panel.device)

    def move_right(self) -> None:
        """
        Method runs motion to right.
        """

        if self._check_device():
            self._open_panel.device.stop_motion()
            self._figures_thread.add_task(self._open_panel.device.move_right, device=self._open_panel.device)

    def move_to_position(self) -> None:
        """
        Method runs motion to given position.
        """

        if self._check_device():
            self._open_panel.device.stop_motion()
            position = self.int_text_widget_position.value
            self._figures_thread.add_task(self._open_panel.device.move_to_position_in_user_unit, position,
                                          device=self._open_panel.device)

    def set_user_unit(self, user_unit: str) -> None:
        self._user_unit = user_unit
        self.int_text_widget_position.description = f"Position, {self._user_unit}"
        self.int_text_widget_shift.description = f"Shift, {self._user_unit}"
        self._figures_thread.set_user_unit(self._user_unit)

    def stop_motion(self) -> None:
        """
        Method stops motion.
        """

        if self._check_device():
            self._open_panel.device.stop_motion()


class FiguresOutput:

    def __init__(self, user_unit: str) -> None:
        """
        :param user_unit: user unit (for example, mm, deg).
        """

        self._user_unit: str = user_unit
        self._axs: Dict[str, Any] = None
        self._lock: threading.Lock = threading.Lock()
        self._running: bool = False
        self._tasks: queue.Queue = queue.Queue()
        self._thread: threading.Thread = threading.Thread(target=self.run_thread)
        self._create_figs()

    @property
    def box(self):
        return self._box

    def _create_figs(self) -> None:
        self._data = {"position": {"y_label": "Position, {}",
                                   "color": "red",
                                   "values": []},
                      "speed": {"y_label": "Speed, {}/sec",
                                "color": "orange",
                                "values": []},
                      "power_current": {"y_label": "Current, mA",
                                        "color": "green",
                                        "values": []},
                      "power_voltage": {"y_label": "Voltage, V",
                                        "color": "blue",
                                        "values": []},
                      "temperature": {"y_label": "Temperature, °C",
                                      "color": "purple",
                                      "values": []}}
        plt.ioff()
        self._figs = {}
        self._axs = {}
        for fig_name, fig_data in self._data.items():
            self._figs[fig_name] = plt.figure(figsize=(4, 3))
            self._figs[fig_name].canvas.toolbar_visible = False
            self._figs[fig_name].canvas.header_visible = False
            self._figs[fig_name].canvas.footer_visible = False
            self._figs[fig_name].canvas.resizable = False

            self._axs[fig_name] = self._figs[fig_name].subplots()
            self._axs[fig_name].plot([], [], color=fig_data["color"])
            self._axs[fig_name].grid(True)
            self._axs[fig_name].set_xlabel("Time, sec")
            self._axs[fig_name].set_ylabel(fig_data["y_label"].format(self._user_unit))
        plt.ion()

        h_box_1 = widgets.HBox([self._figs["position"].canvas, self._figs["speed"].canvas])
        h_box_2 = widgets.HBox([self._figs["power_current"].canvas, self._figs["power_voltage"].canvas])
        self._box = widgets.VBox([h_box_1, h_box_2, self._figs["temperature"].canvas])

    @staticmethod
    def _get_max_limit(values: List[float]) -> float:
        max_value = max(values)
        if max_value < 0:
            return 0.9 * max_value
        if max_value == 0:
            return 1
        return 1.1 * max_value

    @staticmethod
    def _get_min_limit(values: List[float]) -> float:
        min_value = min(values)
        if min_value < 0:
            return 1.1 * min_value
        if min_value == 0:
            return -1
        return 0.9 * min_value

    def add_task(self, task, *args, **kwargs) -> None:
        """
        Method adds new task.
        :param task: function to be performed for task;
        :param args: arguments for task;
        :param kwargs:
        """

        with self._lock:
            self._tasks.put(lambda: self.do_task(task, *args, **kwargs))

    def do_task(self, move_function, *args, **kwargs) -> None:
        """
        Method performs task of starting a specific device movement.
        :param move_function: device move function;
        :param args: arguments for move function;
        :param kwargs:
        """

        device = kwargs["device"]
        start_time = datetime.now()
        params = device.get_params_in_user_unit()
        for param_name, param_data in self._data.items():
            param_data["values"] = [params[param_name]]
        times = [0]
        move_function(*args)
        while device.check_moving():
            device_params = device.get_params_in_user_unit()
            if device_params:
                delta_time = datetime.now() - start_time
                times.append(delta_time.total_seconds())
                for param_name, param_data in self._data.items():
                    param_data["values"].append(device_params[param_name])
                    self._axs[param_name].lines[0].set_data(times, param_data["values"])
                    self._axs[param_name].set_xlim([-1, max(times) + 1])
                    self._axs[param_name].set_ylim([self._get_min_limit(param_data["values"]),
                                                    self._get_max_limit(param_data["values"])])
                    plt.draw()
            time.sleep(0.5)

    def run_thread(self) -> None:
        """
        Method processes tasks in a thread.
        """

        while self._running:
            with self._lock:
                if not self._tasks.empty():
                    task = self._tasks.get()
                    task()
            time.sleep(0.5)

    def set_user_unit(self, user_unit: str) -> None:
        self._user_unit = user_unit
        for param_name, param_data in self._data.items():
            self._axs[param_name].set_ylabel(param_data["y_label"].format(self._user_unit))

    def start_thread(self) -> None:
        """
        Method starts thread.
        """

        self._running = True
        self._thread.start()

    def stop_thread(self) -> None:
        """
        Method stops thread.
        """

        self._running = False
