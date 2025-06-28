"""pyBlasher utility helper functions."""

from serial.tools import list_ports

from constants import *


def find_cp2102n_ports():
    """Scan serial ports and return those matching the CP2102N VID/PID."""
    matches = []
    vid_pid = f"{CP2102N_VID:04X}:{CP2102N_PID:04X}".lower()
    for port in list_ports.comports():
        if port.vid == CP2102N_VID and port.pid == CP2102N_PID:
            matches.append(port.device)
        elif port.hwid and vid_pid in port.hwid.lower():
            matches.append(port.device)
    return matches
