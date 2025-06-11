"""STM32 programmer prototype (USB to UART bootloader)."""

import time
from functools import reduce
from operator import xor

import serial

from nor_flash_comm import *


def checksum(data: bytes) -> int:
    """Compute XOR checksum over the data bytes."""
    return reduce(xor, data, 0)


def pulse_nrst(ser: serial.Serial, duration_ms: int = 50):
    """Hold NRST low for duration_ms, then release.

    Assumes RTS -> 100nF AC-coupling cap -> NRST wiring.
    """
    ser.rts = False  # NRST asserted (low)
    time.sleep(duration_ms / 1000.0)
    ser.rts = True  # NRST released (high)


def enter_bootloader(ser: serial.Serial):
    """Pulse NRST to exit reset into bootloader, then perform auto-baud sync."""
    pulse_nrst(ser, duration_ms=20)  # longer hold for reliability
    time.sleep(0.05)  # small delay to pass rebounce and allow MCU to reset
    # Auto-baud sync
    ser.write(b"\x7f")
    ack = ser.read(1)
    if ack != b"\x79":
        raise RuntimeError(f"Sync failed, expected 0x79, got {ack!r}")


def mass_erase(ser: serial.Serial):
    """Perform a global flash erase using the Extended Erase command."""
    # Send Extended Erase command (0x44)
    ser.write(bytes([0x44, 0xBB]))  # 0x44 ^ 0xFF = 0xBB
    if ser.read(1) != b"\x79":
        raise RuntimeError("Extended Erase command not ACKed")
    # Global erase sequence: 0xFFFF + checksum 0x00
    data = bytes([0xFF, 0xFF])
    ser.write(data + bytes([checksum(data)]))
    if ser.read(1) != b"\x79":
        raise RuntimeError("Global Erase not ACKed")


def write_block(ser: serial.Serial, addr: int, data: bytes):
    """Write a block of data to the given address."""
    # Write Memory command (0x31)
    ser.write(bytes([0x31, 0xCE]))  # 0x31 ^ 0xFF = 0xCE
    if ser.read(1) != b"\x79":
        raise RuntimeError("Write Memory command not ACKed")
    # Send 32-bit BE address + checksum
    addr_bytes = addr.to_bytes(4, "big")
    ser.write(addr_bytes + bytes([checksum(addr_bytes)]))
    if ser.read(1) != b"\x79":
        raise RuntimeError("Address not ACKed")
    # Send length-1, data, checksum(length-1 + data)
    length = len(data)
    if length > 256:
        raise ValueError("Block too large")
    packet = bytes([length - 1]) + data
    ser.write(packet + bytes([checksum(packet)]))
    if ser.read(1) != b"\x79":
        raise RuntimeError("Data block not ACKed")


def go(ser: serial.Serial, addr: int):
    """Send the Go command to start execution at addr."""
    ser.write(bytes([0x21, 0xDE]))  # 0x21 ^ 0xFF = 0xDE
    if ser.read(1) != b"\x79":
        raise RuntimeError("Go command not ACKed")
    addr_bytes = addr.to_bytes(4, "big")
    ser.write(addr_bytes + bytes([checksum(addr_bytes)]))
    if ser.read(1) != b"\x79":
        raise RuntimeError("Go address not ACKed")


def flash_image(
    ser: serial.Serial, image_path: str, base_addr: int = 0x08000000
):
    """Overall flow: enter bootloader, erase, program, and reset into app."""
    img = open(image_path, "rb").read()

    # 1) Pulse NRST before start
    pulse_nrst(ser, duration_ms=50)
    time.sleep(0.05)

    # 2) Enter bootloader via NRST pulse + sync
    enter_bootloader(ser)

    # 3) Mass erase flash
    mass_erase(ser)

    # 4) Program in 256-byte pages
    for offset in range(0, len(img), 256):
        chunk = img[offset : offset + 256]
        write_block(ser, base_addr + offset, chunk)

    # 5) Issue 'Go' to start application
    go(ser, base_addr)


if __name__ == "__main__":
    with serial.Serial("COM1", 115200) as ser:
        time.sleep(1)  # Wait for NRSTs to clear from COM port establishment.

        """NOTE: Example firmware flash."""
        # print("Flash new firmware")
        # flash_image(ser, "firmware.bin")

        """NOTE: Example NVM NOR flash write enable and disable."""
        # print("Enable NVM write")
        # write_enable(ser)
        # print("Disable NVM write")
        # write_disable(ser)

        """NOTE: Example NVM NOR flash memory communication."""
        # print("Reading NVM sector")
        # section_start = 0x001000
        # section_length = 4096
        # output_file_path = "nvm_dump.txt"
        # sector = read_section(
        #     ser, start_addr=section_start, length=section_length
        # )
        # save_hexdump(sector, start_addr=0x001000, filename=output_file_path)
        # print(f"Wrote {len(sector)} bytes to {output_file_path}")

    pass
