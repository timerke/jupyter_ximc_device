import queue
import threading
import time
from datetime import datetime
from typing import Any, Dict, List
import ipywidgets as widgets
import matplotlib.pyplot as plt
from IPython.display import display
from ximc_device.device import XimcDevice


class ControlPanel:

    def __init__(self, device: XimcDevice) -> None:
        """
        :param device: device.
        """

        self._device: XimcDevice = device
        v_box = self._create_widgets()
        self._figures_thread: FiguresOutput = FiguresOutput(self._device)
        self._figures_thread.start_thread()
        display(widgets.VBox([v_box, self._figures_thread.box]))

    def _create_widgets(self) -> widgets.VBox:
        """
        Method creates widgets for motion panel.
        """

        style = {"description_width": "150px"}
        self.button_move_left = widgets.Button(description="Move left", icon="arrow-left")
        self.button_move_left.on_click(lambda _: self.move_left())
        self.button_stop = widgets.Button(description="Stop", icon="stop")
        self.button_stop.on_click(lambda _: self._device.stop_motion())
        self.button_move_right = widgets.Button(description="Move right", icon="arrow-right")
        self.button_move_right.on_click(lambda _: self.move_right())
        h_box_0 = widgets.HBox([self.button_move_left, self.button_stop, self.button_move_right])

        self.int_text_widget_position = widgets.BoundedIntText(value=0, min=-1000, max=1000, step=1,
                                                               description="Position, mm", style=style)
        self.button_move_to = widgets.Button(description="Move to")
        self.button_move_to.on_click(lambda _: self.move_to_position())
        h_box_1 = widgets.HBox([self.button_move_to, self.int_text_widget_position])

        self.int_text_widget_shift = widgets.BoundedIntText(value=0, min=-1000, max=1000, step=1,
                                                            description="Shift, mm", style=style)
        self.button_shift_on = widgets.Button(description="Shift on")
        self.button_shift_on.on_click(lambda _: self.move_on_shift())
        h_box_2 = widgets.HBox([self.button_shift_on, self.int_text_widget_shift])

        return widgets.VBox([h_box_0, h_box_1, h_box_2])

    def move_left(self) -> None:
        """
        Method runs motion to left.
        """

        self._device.stop_motion()
        self._figures_thread.add_task(self._device.move_left)

    def move_on_shift(self) -> None:
        """
        Method runs motion on given shift.
        """

        self._device.stop_motion()
        shift = self.int_text_widget_shift.value
        current_position = self._device.get_position_in_user_units()
        position_to_move = current_position + shift
        self._figures_thread.add_task(self._device.move_to_position_in_user_units, position_to_move)

    def move_right(self) -> None:
        """
        Method runs motion to right.
        """

        self._device.stop_motion()
        self._figures_thread.add_task(self._device.move_right)

    def move_to_position(self) -> None:
        """
        Method runs motion to given position.
        """

        self._device.stop_motion()
        position = self.int_text_widget_position.value
        self._figures_thread.add_task(self._device.move_to_position_in_user_units, position)


class FiguresOutput:

    def __init__(self, device: XimcDevice) -> None:
        """
        :param device: device.
        """

        self._axs: Dict[str, Any] = None
        self._device: XimcDevice = device
        self._lock: threading.Lock = threading.Lock()
        self._running: bool = False
        self._tasks: queue.Queue = queue.Queue()
        self._thread: threading.Thread = threading.Thread(target=self.run_thread)
        self._create_figs()

    @property
    def box(self):
        return self._box

    def _create_figs(self) -> None:
        data = {"position": {"y_label": "Position, mm",
                             "color": "red"},
                "speed": {"y_label": "Speed, mm/sec",
                          "color": "orange"},
                "power_current": {"y_label": "Current, mA",
                                  "color": "green"},
                "power_voltage": {"y_label": "Voltage, V",
                                  "color": "blue"},
                "temperature": {"y_label": "Temperature, °C",
                                "color": "purple"}}
        plt.ioff()
        self._figs = {}
        self._axs = {}
        for fig_name, fig_data in data.items():
            self._figs[fig_name] = plt.figure(figsize=(4, 3))
            self._figs[fig_name].canvas.toolbar_visible = False
            self._figs[fig_name].canvas.header_visible = False
            self._figs[fig_name].canvas.footer_visible = False
            self._figs[fig_name].canvas.resizable = False

            self._axs[fig_name] = self._figs[fig_name].subplots()
            self._axs[fig_name].plot([], [], color=fig_data["color"])
            self._axs[fig_name].grid(True)
            self._axs[fig_name].set_xlabel("Time, sec")
            self._axs[fig_name].set_ylabel(fig_data["y_label"])
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

    def add_task(self, task, *args) -> None:
        """
        Method adds new task.
        :param task: function to be performed for task;
        :param args: arguments for task.
        """

        with self._lock:
            self._tasks.put(lambda: self.do_task(task, *args))

    def do_task(self, move_function, *args) -> None:
        """
        Method performs task of starting a specific device movement.
        :param move_function: device move function;
        :param args: arguments for move function.
        """

        start_time = datetime.now()
        params = self._device.get_params_in_user_units()
        data = {"position": [params["position"]],
                "speed": [params["speed"]],
                "power_current": [params["power_current"]],
                "power_voltage": [params["power_voltage"]],
                "temperature": [params["temperature"]]}
        times = [0]
        move_function(*args)
        while self._device.check_moving():
            device_params = self._device.get_params_in_user_units()
            if device_params:
                delta_time = datetime.now() - start_time
                times.append(delta_time.total_seconds())
                for param_name, param_values in data.items():
                    param_values.append(device_params[param_name])
                    self._axs[param_name].lines[0].set_data(times, param_values)
                    self._axs[param_name].set_xlim([-1, max(times) + 1])
                    self._axs[param_name].set_ylim([self._get_min_limit(param_values),
                                                    self._get_max_limit(param_values)])
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
