"""pyBlasher CLI app."""

import time
from sys import exit

import serial

from flash_firmware import flash_image, pulse_nrst
from nor_flash_comm import (
    reset,
    read_section,
    save_hexdump,
)
from util import find_cp2102n_ports

SERIAL_PORT = "COM1"


def __flash_image():
    print(f"1. Enter a firmware filepath (.bin):")
    image_path = input("> ")
    if len(image_path) < 5 or image_path[-4:] != ".bin":
        image_path += ".bin"

    print(f"2. Opening serial port ({SERIAL_PORT})")
    with serial.Serial(
        SERIAL_PORT, 115200, parity=serial.PARITY_EVEN, timeout=1
    ) as ser:
        time.sleep(1)  # Wait for NRSTs to clear from serial port establishment

        print(f"3. Beginning firmware flash")

        try:
            flash_image(ser, image_path)
        except RuntimeError as e:
            if "Sync failed" in str(e):
                raise RuntimeError("Ensure BOOT0 is raised, then retry")

    print("\tFirmware update successful")


def __nvm_reset():
    print(f"1. Opening serial port ({SERIAL_PORT})")
    with serial.Serial(SERIAL_PORT, 115200) as ser:
        time.sleep(1)  # Wait for NRSTs to clear from serial port establishment

        print(f"2. Beginning NVM reset")
        reset(ser)

    print("\tReset NVM")


def __nvm_memory_extract():
    print(f"1. Enter a starting address (Hex):")
    section_start = input("> ").strip()
    try:
        section_start = int(section_start, 16)
    except TypeError:
        raise ValueError("Expected hexadecimal address")

    print(f"2. Enter a read length (recommended 4096):")
    section_length = input("> ").strip()
    try:
        section_length = int(section_length)
    except TypeError:
        raise ValueError("Expected hexadecimal address")

    print(f"3. Enter a output filepath (recommended .txt):")
    output_file_path = input("> ")
    if len(output_file_path) < 5 or output_file_path[-4:] != ".txt":
        output_file_path += ".txt"

    print(f"4. Opening serial port ({SERIAL_PORT})")
    with serial.Serial(SERIAL_PORT, 115200) as ser:
        # Pulse NRST before start
        pulse_nrst(ser, duration_ms=50)
        time.sleep(0.05)

        time.sleep(7)  # Wait for NRSTs to clear from serial port establishment

        print(f"5. Beginning NVM read communication")
        sector = read_section(
            ser, start_addr=section_start, length=section_length
        )

    print(f"6. Beginning hex dump file save")
    save_hexdump(sector, start_addr=section_start, filename=output_file_path)

    print(f"\tWrote {len(sector)} bytes to {output_file_path}")


def __serial_port_manual_config():
    global SERIAL_PORT

    print(f"Current serial port: {SERIAL_PORT}")
    print("Enter a serial port:")
    input_serial_port = input("> ").strip().lower()
    if input_serial_port.isnumeric():
        SERIAL_PORT = f"COM{input_serial_port}"
    else:
        SERIAL_PORT = input_serial_port.upper()
    print(f"\tSerial port configured to: {SERIAL_PORT}")


def __serial_port_auto_config():
    global SERIAL_PORT

    cp_ports = find_cp2102n_ports()
    if cp_ports:
        print(
            f"\tFound CP2102N device(s): "
            f"{', '.join([port for port in cp_ports])}"
        )
        SERIAL_PORT = cp_ports[0]
        print(f"\tSerial port configured to: {SERIAL_PORT}")
    else:
        print("\tNo CP2102N devices found, please add a serial port manually")


def header_print():
    print(
        "-------------------------------------------------------------------------------\n"
        "                       Momentum pyBlasher (v0.1.0-alpha)                       \n"
        "-------------------------------------------------------------------------------\n"
    )


def end_of_command_print():
    print()


def main_menu_print():
    print(
        "    Options: (Not case sensitive)\n"
        "     1 = Momentum firmware update\n"
        "     2 = NVM reset (wipe memory)\n"
        "     3 = NVM sector readout\n"
        "     8 = Automatic serial port configuration\n"
        "     9 = Manual serial port configuration\n"
        "     e = Exit\n"
    )


def run_cli():
    header_print()

    __serial_port_auto_config()

    end_of_command_print()

    try:
        while True:
            main_menu_print()
            choice = input("> ").strip().lower()[0]

            start = time.time()

            try:
                if choice == "1":
                    __flash_image()
                elif choice == "2":
                    __nvm_reset()
                elif choice == "3":
                    __nvm_memory_extract()
                elif choice == "8":
                    __serial_port_auto_config()
                elif choice == "9":
                    __serial_port_manual_config()
                elif choice == "e":
                    raise KeyboardInterrupt
                else:
                    print(f"Invalid choice: {choice!r}!")
            except ValueError as e:
                print(f"\tValueError: {e}")
            except serial.serialutil.SerialException as e:
                print(f"\tSerialException: {e}")
            except FileNotFoundError as e:
                print(f"\tFileNotFoundError: {e}")
            except RuntimeError as e:
                print(f"\tRuntimeError: {e}")

            print(f"\tCompleted in {time.time() - start} seconds")

            end_of_command_print()

    except KeyboardInterrupt:
        print("\nTerminating program...")
        exit(1)
