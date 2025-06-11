"""Main pyBlasher application for Momentum."""

import time

import serial

# from flash_firmware import flash_image
# from nor_flash_comm import (
#     write_enable,
#     write_disable,
#     read_section,
#     save_hexdump,
# )

if __name__ == "__main__":
    with serial.Serial("COM18", 115200) as ser:
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
