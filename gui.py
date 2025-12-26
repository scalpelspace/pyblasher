"""PyBlasher GUI app."""

import time
from threading import Thread

import serial
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

from constants import VERSION
from flash_firmware import flash_image
from util import (
    resource_path,
    find_cp2102n_ports,
    open_serial_port,
    write_serial_bytes,
    parse_hex,
)

MSG_NO_PORTS_FOUND = "No ports found"


def dim_btn(btn):
    btn.disabled = True


def undim_btn(btn):
    btn.disabled = False


class FirmwareToolUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical", spacing=10, padding=10, **kwargs
        )
        # Port selection
        self.port_spinner = Spinner(
            text="Click to select a port",
            size_hint=(1, 0.25),
            font_size=sp(16),
            background_normal="",
            background_color=(0.1, 0.4, 0.1, 1),
        )
        self.add_widget(self.port_spinner)
        self.add_widget(
            Button(
                text="Refresh ports",
                size_hint=(1, 0.25),
                font_size=sp(16),
                background_normal="",
                background_color=(0.1, 0.4, 0.1, 1),
                on_press=lambda _: self.refresh_ports(),
            )
        )

        # Spacer
        self.add_widget(Widget(size_hint=(1, 0.05)))

        # Firmware file selection
        self.bin_label = Label(
            text="No .bin selected",
            size_hint=(1, 0.25),
            font_size=sp(16),
        )
        self.add_widget(self.bin_label)
        self.add_widget(
            Button(
                text="Drop a .bin file here or click to browse",
                size_hint=(1, 0.25),
                font_size=sp(16),
                background_normal="",
                background_color=(0.8, 0.5, 0.1, 1),
                on_press=self.browse_bin,
            )
        )
        self.bin_path = None
        Window.bind(on_drop_file=self._on_file_drop)

        # Spacer
        self.add_widget(Widget(size_hint=(1, 0.05)))

        # Execute flash
        self.flash_btn = Button(
            text="Flash firmware",
            size_hint=(1, 0.25),
            font_size=sp(16),
            background_normal="",
            background_color=(0.8, 0.3, 0.3, 1),
            on_press=lambda _: self.execute_flash(),
        )
        self.add_widget(self.flash_btn)

        # Log
        self.log_view = TextInput(
            readonly=True, multiline=True, size_hint=(1, 1)
        )
        self.add_widget(self.log_view)

        # Post init actions
        self.log(f"Running PyBlasher v{VERSION}")
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
            title="Select .bin file", content=chooser, size_hint=(0.8, 0.8)
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

    def _start_flash_thread(self, port):
        """Spawn a daemon thread for flashing so the UI thread is free."""
        dim_btn(self.flash_btn)

        Thread(
            target=self.__confirm_flash_proceed, args=(port,), daemon=True
        ).start()

    def __confirm_flash_proceed(self, port):
        """Runs in a worker thread to flash firmware."""
        try:
            ser = serial.Serial(
                port, 115200, parity=serial.PARITY_EVEN, timeout=1
            )
        except Exception as e:
            Clock.schedule_once(
                lambda dt, err=e: self.log(f"Could not open port {port}: {err}")
            )
            return

        time.sleep(1)

        Clock.schedule_once(
            lambda dt: self.log(
                f"Starting firmware update on {port} with {self.bin_path}"
            )
        )

        try:
            flash_image(ser, self.bin_path)
            Clock.schedule_once(
                lambda dt: self.log("Firmware update successful.")
            )
        except Exception as e:
            Clock.schedule_once(
                lambda dt, err=e: self.log(f"Error during flash: {err}")
            )
        finally:
            ser.close()

            Clock.schedule_once(lambda dt: undim_btn(self.flash_btn))

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

        button_row = BoxLayout(size_hint=(1, 0.25))
        yes_btn = Button(text="Yes", background_color=(0.1, 0.6, 0.1, 1))
        cancel_btn = Button(text="Cancel", background_color=(0.6, 0.1, 0.1, 1))
        button_row.add_widget(yes_btn)
        button_row.add_widget(cancel_btn)

        confirm_layout.add_widget(button_row)

        popup = Popup(
            title="Confirm firmware flash",
            content=confirm_layout,
            size_hint=(0.8, 0.6),
        )

        yes_btn.bind(
            on_press=lambda _: (
                popup.dismiss(),
                self._start_flash_thread(port),
            )
        )
        cancel_btn.bind(on_press=popup.dismiss)

        popup.open()


class TerminalUI(BoxLayout):
    """Minimal UART terminal for sending/receiving arbitrary messages."""

    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical", spacing=10, padding=10, **kwargs
        )

        # Top row: port + connect + refresh
        top = BoxLayout(
            orientation="horizontal", size_hint=(1, 0.15), spacing=10
        )

        self.port_spinner = Spinner(
            text="Click to select a port",
            size_hint=(0.55, 1),
            font_size=sp(16),
            background_normal="",
            background_color=(0.1, 0.1, 0.4, 1),
        )
        top.add_widget(self.port_spinner)

        self.connect_btn = Button(
            text="Connect",
            size_hint=(0.2, 1),
            font_size=sp(16),
            background_normal="",
            background_color=(0.15, 0.5, 0.15, 1),
            on_press=self.toggle_connect,
        )
        top.add_widget(self.connect_btn)

        top.add_widget(
            Button(
                text="Refresh Ports",
                size_hint=(0.25, 1),
                font_size=sp(16),
                background_normal="",
                background_color=(0.35, 0.35, 0.35, 1),
                on_press=lambda *_: self.refresh_ports(),
            )
        )

        self.add_widget(top)

        # Log (read-only)
        self.log_box = TextInput(
            text="",
            readonly=True,
            multiline=True,
            size_hint=(1, 0.65),
            font_size=sp(14),
        )
        self.add_widget(self.log_box)

        # Send row
        send_row = BoxLayout(
            orientation="horizontal", size_hint=(1, 0.2), spacing=10
        )

        self.tx_input = TextInput(
            hint_text="Type ASCII (or HEX if enabled) ...",
            multiline=False,
            size_hint=(0.7, 1),
            font_size=sp(16),
        )
        send_row.add_widget(self.tx_input)

        self.hex_mode = Spinner(
            text="ASCII",
            values=["ASCII", "HEX"],
            size_hint=(0.15, 1),
            font_size=sp(16),
        )
        send_row.add_widget(self.hex_mode)

        send_row.add_widget(
            Button(
                text="Send",
                size_hint=(0.15, 1),
                font_size=sp(16),
                background_normal="",
                background_color=(0.8, 0.5, 0.1, 1),
                on_press=lambda *_: self.send_line(),
            )
        )

        self.add_widget(send_row)

        self._ser = None
        self._rx_thread = None
        self._rx_buf = bytearray()
        self._running = False

        self.refresh_ports()

    def refresh_ports(self):
        found_ports = find_cp2102n_ports()
        if found_ports:
            self.port_spinner.values = found_ports
            self.port_spinner.text = found_ports[0]
        else:
            self.port_spinner.values = []
            self.port_spinner.text = MSG_NO_PORTS_FOUND
        self._append(
            f"Ports refreshed: {', '.join(found_ports) if found_ports else MSG_NO_PORTS_FOUND}"
        )

    def _append(self, msg: str):
        self.log_box.text += msg + "\n"
        # scroll to end
        try:
            row = max(0, len(self.log_box.text.splitlines()) - 1)
            self.log_box.cursor = (0, row)
            self.log_box.scroll_y = 0
        except Exception:
            pass

    def toggle_connect(self, *_):
        if self._ser:
            self._running = False
            try:
                self._ser.close()
            except Exception:
                pass
            self._ser = None
            self.connect_btn.text = "Connect"
            self._append("Disconnected.")
            return

        port = self.port_spinner.text
        if not port or port == MSG_NO_PORTS_FOUND:
            self._append("No valid port selected.")
            return

        try:
            self._ser = open_serial_port(port, baud=115200)
        except Exception as e:
            self._ser = None
            self._append(f"Connect failed: {e}")
            return

        self.connect_btn.text = "Disconnect"
        self._append(f"Connected to {port} @ 115200.")

        self._running = True
        self._rx_thread = Thread(target=self._rx_loop, daemon=True)
        self._rx_thread.start()

    def _rx_loop(self):
        while self._running and self._ser:
            try:
                n = self._ser.in_waiting
                data = self._ser.read(n if n else 1)
                if not data:
                    continue

                self._rx_buf.extend(data)

                # Emit complete lines (keeps messages together).
                while b"\n" in self._rx_buf:
                    line, _, rest = self._rx_buf.partition(b"\n")
                    self._rx_buf = bytearray(rest)

                    # Include the '\n' you consumed (optional).
                    line_bytes = line + b"\n"

                    text = line_bytes.decode("utf-8", errors="replace").rstrip(
                        "\r\n"
                    )
                    hex_part = line_bytes.hex(" ").upper()

                    Clock.schedule_once(
                        lambda *_, t=text, h=hex_part: self._append(
                            f"RX: {t}   [{h}]"
                        )
                    )

            except Exception as e:
                Clock.schedule_once(
                    lambda *_, err=e: self._append(f"RX error: {err}")
                )
                break

    def send_line(self):
        if not self._ser:
            self._append("Not connected.")
            return
        raw = self.tx_input.text.strip()
        if not raw:
            return
        try:
            if self.hex_mode.text == "HEX":
                payload = parse_hex(raw)
            else:
                payload = raw.encode("utf-8")
            write_serial_bytes(self._ser, payload)
            Clock.schedule_once(lambda *_: self._append(f"TX: {raw}"))
        except Exception as e:
            self._append(f"TX error: {e}")


class RootUI(BoxLayout):
    """Page-swap UI: Firmware flasher + UART terminal."""

    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical", spacing=10, padding=10, **kwargs
        )

        # Nav bar
        nav = BoxLayout(
            orientation="horizontal", size_hint=(1, 0.12), spacing=10
        )
        self.btn_flash = Button(text="Firmware", font_size=sp(16))
        self.btn_term = Button(text="UART Terminal", font_size=sp(16))
        nav.add_widget(self.btn_flash)
        nav.add_widget(self.btn_term)
        self.add_widget(nav)

        # Pages
        self.sm = ScreenManager()
        self.flash_ui = FirmwareToolUI()
        self.term_ui = TerminalUI()

        s1 = Screen(name="flash")
        s1.add_widget(self.flash_ui)
        s2 = Screen(name="term")
        s2.add_widget(self.term_ui)

        self.sm.add_widget(s1)
        self.sm.add_widget(s2)
        self.add_widget(self.sm)

        self.btn_flash.bind(on_press=lambda *_: self._go("flash"))
        self.btn_term.bind(on_press=lambda *_: self._go("term"))

        self._go("flash")

    def _go(self, name: str):
        self.sm.current = name
        if name == "flash":
            try:
                self.flash_ui.refresh_ports()
            except Exception:
                pass
        elif name == "term":
            try:
                self.term_ui.refresh_ports()
            except Exception:
                pass


class PyBlasherApp(App):
    def build(self):
        Window.size = (600, 450)
        Window.clearcolor = (0.12, 0.12, 0.12, 1)  # Dark gray background.
        Window.minimum_width = 350
        Window.minimum_height = 350
        Window.set_icon(resource_path("assets\\icon.png"))
        self.root_ui = RootUI()
        return self.root_ui

    def on_stop(self):
        # Ensure serial port is closed when the app exits.
        try:
            if hasattr(self, "root_ui") and getattr(
                self.root_ui, "term_ui", None
            ):
                self.root_ui.term_ui._running = False
                if self.root_ui.term_ui._ser:
                    self.root_ui.term_ui._ser.close()
        except Exception:
            pass


def run_gui():
    PyBlasherApp().run()
