"""PyBlasher utility helper functions."""

import os.path
import sys

from serial.tools import list_ports

from constants import *


def resource_path(relative_path: str) -> str:
    """Get absolute path using a relative path to a resource.

    Based on: https://stackoverflow.com/questions/31836104/pyinstaller-and-onefile-how-to-include-an-image-in-the-exe-file.
    """
    try:
        base_path = sys._MEIPASS2
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def find_cp2102n_ports() -> list[str]:
    """Scan serial ports and return those matching the CP2102N VID/PID."""
    matches = []
    vid_pid = f"{CP2102N_VID:04X}:{CP2102N_PID:04X}".lower()
    for port in list_ports.comports():
        if port.vid == CP2102N_VID and port.pid == CP2102N_PID:
            matches.append(port.device)
        elif port.hwid and vid_pid in port.hwid.lower():
            matches.append(port.device)
    return matches
