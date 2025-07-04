"""pyBlasher GUI app."""

import time

import serial
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

from flash_firmware import flash_image
from util import find_cp2102n_ports

MSG_NO_PORTS_FOUND = "No ports found"


class FirmwareToolUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical", spacing=10, padding=10, **kwargs
        )
        # Port selection
        self.port_spinner = Spinner(
            text="Click to select a port",
            size_hint=(1, None),
            height=40,
            background_normal="",
            background_color=(0.1, 0.4, 0.1, 1),
        )
        self.add_widget(self.port_spinner)
        self.add_widget(
            Button(
                text="Refresh ports",
                size_hint=(1, None),
                height=40,
                background_normal="",
                background_color=(0.1, 0.4, 0.1, 1),
                on_press=lambda _: self.refresh_ports(),
            )
        )

        # Spacer
        self.add_widget(Widget(size_hint_y=None, height=10))

        # Firmware file selection
        self.bin_label = Label(
            text="No .bin selected", size_hint=(1, None), height=30
        )
        self.add_widget(self.bin_label)
        self.add_widget(
            Button(
                text="Drop a .bin file here or click to browse",
                size_hint=(1, None),
                height=40,
                background_normal="",
                background_color=(0.8, 0.5, 0.1, 1),
                on_press=self.browse_bin,
            )
        )
        self.bin_path = None
        Window.bind(on_drop_file=self._on_file_drop)

        # Spacer
        self.add_widget(Widget(size_hint_y=None, height=10))

        # Execute & Log
        self.add_widget(
            Button(
                text="Flash Firmware",
                size_hint=(1, None),
                height=40,
                background_normal="",
                background_color=(0.8, 0.3, 0.3, 1),
                on_press=lambda _: self.execute_flash(),
            )
        )
        self.log_view = TextInput(
            readonly=True, multiline=True, size_hint=(1, 1)
        )
        self.add_widget(self.log_view)

        # Post init actions
        self.refresh_ports()

    def log(self, message: str):
        self.log_view.text += message + "\n"

    def refresh_ports(self):
        found_ports = find_cp2102n_ports()
        if found_ports:
            self.port_spinner.values = found_ports
            self.port_spinner.text = found_ports[0]  # Default to first port
        else:
            self.port_spinner.values = []
            self.port_spinner.text = MSG_NO_PORTS_FOUND
        log_text = (
            ",".join(self.port_spinner.values)
            if self.port_spinner.values
            else MSG_NO_PORTS_FOUND
        )
        self.log(f"Ports refreshed: {log_text}")

    def browse_bin(self, _):
        chooser = FileChooserListView(filters=["*.bin"])
        popup = Popup(
            title="Select .bin file", content=chooser, size_hint=(0.9, 0.9)
        )
        chooser.bind(selection=lambda fs, sel: self._select_bin(sel, popup))
        popup.open()

    def _select_bin(self, selection, popup):
        if selection:
            self.bin_path = selection[0]
            self.bin_label.text = self.bin_path
            popup.dismiss()

    def _on_file_drop(self, window, file_path, x, y):
        path = file_path.decode("utf-8")
        if path.endswith(".bin"):
            self.bin_path = path
            self.bin_label.text = path
            self.log(f"Dropped .bin file: {path}")
        else:
            self.log(f"Ignored dropped file (not .bin): {path}")

    def _confirm_flash_proceed(self, port):
        try:
            ser = serial.Serial(
                port, 115200, parity=serial.PARITY_EVEN, timeout=1
            )
        except Exception as e:
            self.log(f"Could not open port {port}: {e}")
            return
        time.sleep(1)
        self.log(f"Starting firmware update on {port} with {self.bin_path}")
        try:
            flash_image(ser, self.bin_path)
            self.log("Firmware update successful.")
        except Exception as e:
            self.log(f"Error during flash: {e}")
        finally:
            ser.close()

    def execute_flash(self):
        port = self.port_spinner.text
        if port == MSG_NO_PORTS_FOUND:
            self.log("Select a port!")
            return
        if not self.bin_path:
            self.log("Select a .bin file!")
            return

        confirm_layout = BoxLayout(
            orientation="vertical", padding=10, spacing=10
        )
        confirm_layout.add_widget(
            Label(
                text=f"Proceed with flashing\n"
                f"{self.bin_path}\n"
                f"on port {port}?",
                halign="center",
            )
        )

        button_row = BoxLayout(size_hint=(1, None), height=40, spacing=10)
        yes_btn = Button(text="Yes", background_color=(0.1, 0.6, 0.1, 1))
        cancel_btn = Button(text="Cancel", background_color=(0.6, 0.1, 0.1, 1))
        button_row.add_widget(yes_btn)
        button_row.add_widget(cancel_btn)

        confirm_layout.add_widget(button_row)

        popup = Popup(
            title="Confirm Firmware Flash",
            content=confirm_layout,
            size_hint=(0.8, 0.6),
        )

        yes_btn.bind(
            on_press=lambda _: (
                popup.dismiss(),
                self._confirm_flash_proceed(port),
            )
        )
        cancel_btn.bind(on_press=popup.dismiss)

        popup.open()


class PyBlasherApp(App):
    def build(self):
        Window.size = (600, 450)
        Window.minimum_width = 350
        Window.minimum_height = 350
        Window.set_icon("assets/icon.png")
        return FirmwareToolUI()


def run_gui():
    PyBlasherApp().run()
