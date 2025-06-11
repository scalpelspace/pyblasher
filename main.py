"""Main pyBlasher application for Momentum."""

import time

import serial

from flash_firmware import flash_image
from nor_flash_comm import (
    write_enable,
    write_disable,
    read_section,
    save_hexdump,
)

COM_PORT = "COM18"


def example_flash_image():
    with serial.Serial(
        COM_PORT, 115200, parity=serial.PARITY_EVEN, timeout=1
    ) as ser:

        print("Flash new firmware")
        flash_image(ser, "firmware.bin")


def example_nvm_write_enable():
    with serial.Serial(COM_PORT, 115200) as ser:
        time.sleep(1)  # Wait for NRSTs to clear from COM port establishment

        print("Enable NVM write")
        write_enable(ser)


def example_nvm_write_disable():
    with serial.Serial(COM_PORT, 115200) as ser:
        time.sleep(1)  # Wait for NRSTs to clear from COM port establishment

        print("Disable NVM write")
        write_disable(ser)


def example_nvm_memory_extract():
    time.sleep(1)  # Rapid serial port reopens from examples seems unstable.

    with serial.Serial(COM_PORT, 115200) as ser:
        time.sleep(1)  # Wait for NRSTs to clear from COM port establishment

        print("Reading NVM sector")
        section_start = 0x001000
        section_length = 4096
        output_file_path = "nvm_dump.txt"
        sector = read_section(
            ser, start_addr=section_start, length=section_length
        )
        save_hexdump(
            sector, start_addr=section_start, filename=output_file_path
        )
        print(f"Wrote {len(sector)} bytes to {output_file_path}")


if __name__ == "__main__":
    start = time.time()

    # example_flash_image()
    # example_nvm_write_enable()
    # example_nvm_write_disable()
    # example_nvm_memory_extract()

    print(f"\tCompleted in {time.time() - start} seconds")
