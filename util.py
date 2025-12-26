"""PyBlasher utility helper functions."""

import os.path
import sys

import serial
from serial.tools import list_ports

from constants import *


def parse_hex(s: str) -> bytes:
    """Accepts: '01 0A ff', '0x01,0x0A,0xFF', or '010AFF'."""
    cleaned = (
        s.replace("0x", "")
        .replace(",", " ")
        .replace("\n", " ")
        .replace("\t", " ")
        .strip()
    )
    parts = cleaned.split()
    if (
        len(parts) == 1
        and all(c in "0123456789abcdefABCDEF" for c in parts[0])
        and len(parts[0]) % 2 == 0
    ):
        return bytes.fromhex(parts[0])
    return bytes(int(p, 16) for p in parts if p)


def hexdump(data: bytes, width: int = 16) -> str:
    lines = []
    for i in range(0, len(data), width):
        chunk = data[i : i + width]
        hex_part = " ".join(f"{b:02X}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"{i:04X}  {hex_part:<{width*3}}  {ascii_part}")
    return "\n".join(lines)


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


def open_serial_port(
    port: str,
    baud: int = 115200,
    timeout: float = 0.2,
    write_timeout: float = 0.5,
) -> serial.Serial:
    """Open a serial port with sane defaults and clean buffers."""
    ser = serial.Serial(
        port=port,
        baudrate=baud,
        timeout=timeout,
        write_timeout=write_timeout,
        rtscts=False,
        dsrdtr=False,
    )
    ser.dtr = False
    ser.rts = False
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    return ser


def write_serial_bytes(ser: serial.Serial, data: bytes) -> None:
    ser.write(data)
    ser.flush()
