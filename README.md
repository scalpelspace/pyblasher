# pyblasher

![black_formatter](https://github.com/scalpelspace/pyblasher/actions/workflows/black_formatter.yaml/badge.svg)

Python based firmware flash and utility tool for
the [`momentum_pcb`](https://github.com/scalpelspace/momentum_pcb)
running [`momentum`](https://github.com/scalpelspace/momentum) firmware.

---

<details markdown="1">
  <summary>Table of Contents</summary>

<!-- TOC -->
* [pyblasher](#pyblasher)
  * [1 Overview](#1-overview)
    * [1.1 PyBlasher Graphical User Interface (GUI)](#11-pyblasher-graphical-user-interface-gui)
    * [1.2 PyBlasher Command Line Interface (CLI)](#12-pyblasher-command-line-interface-cli)
  * [2 Flashing Firmware](#2-flashing-firmware)
    * [2.1 UART Bootloader (USB-C)](#21-uart-bootloader-usb-c)
    * [2.2 SWD (TC2050)](#22-swd-tc2050)
  * [3 Dev Notes](#3-dev-notes)
    * [3.1 Deprecated PyInstaller Workflow](#31-deprecated-pyinstaller-workflow)
<!-- TOC -->

</details>

---

## 1 Overview

### 1.1 PyBlasher Graphical User Interface (GUI)

PyBlasher runs in GUI mode by default.

![gui_image.png](docs/pictures/gui_image.png)

### 1.2 PyBlasher Command Line Interface (CLI)

To manually run the CLI run use the `-c` or `--cli` flag.

```shell
python3 main.py --cli  # py instead of "python3" for Windows.
```

---

## 2 Flashing Firmware

3 methods of firmware flashing:

1. UART Bootloader via USB-C (Handsfree programming).
2. UART Bootloader via USB-C (Manual BOOT0 control).
3. SWD via TC2050.

### 2.1 UART Bootloader (USB-C)

There are 2 primary operating modes that affect USB-C firmware flashing:

1. **Default:** Handsfree programming.
2. **Modified:** Manual BOOT0 control.
    - `BOOT0 DTR bridge` cut/open for custom serial access.
    - For users using the second modified option will have additional steps,
      format shown below:
      > 1. _**For modified boards:**_ Example step only required for Manual
           BOOT0 control.

**Steps:**

1. If not done so already, download the Silicon
   Labs's [VCP CP210x USB to UART Bridge VCP Drivers](https://www.silabs.com/developer-tools/usb-to-uart-bridge-vcp-drivers).
2. _**For modified boards:**_ Short the `BOOT0 jumper` to raise BOOT0.
3. Connect your desktop computer to the Momentum USB-C.
4. Find the serial port for your Momentum board.
    - If you’re unsure which one is correct you can try unplugging, refreshing
      and replugging in the USB-C to see which new port is opened.
        - **Windows:** Open Device Manager and under `Ports (COM & LPT)` find
          the
          `COMx` port named something along the lines of
          `Silicon Labs CP210x USB to UART Bridge (COMx)`.
        - **macOS:** Open a terminal and enter the following command:
            ```shell
            ls /dev/tty.* /dev/cu.*
            ```
            - The expected name is similar to `/dev/tty.usbserial-*`.
        - **Linux:** Open a terminal and enter the following command:
            ```shell
            dmesg | grep tty
            ````
            - The expected name is `/dev/ttyUSB*`.
5. Find the file path of the new Momentum firmware (`.bin`) you’d like to flash.
6. Run pyBlasher and enter the serial port name for your momentum board from
   earlier steps.
7. Run the Firmware Update option.
8. Enter the new firmware filepath.
9. Firmware flashing will begin, the `UART RX` and `UART TX` leds should flash
   throughout the process.
10. Upon completion of flashing, the Momentum firmware will be auto reset.
11. _**For modified boards:**_ Re-open the `BOOT0 jumper` and push the RESET
    button (short NRST to ground) to begin running the firmware.

### 2.2 SWD (TC2050)

1. Using an STM32 SWD flash tool (ie, ST-Link) connect to the TV2050 connector.
2. Flash/debug firmware with an SWD firmware flash setup (ie,
   STM32CubeProgrammer).

---

## 3 Dev Notes

### 3.1 Deprecated PyInstaller Workflow

The PyInstaller macOS, Windows, Linux builds workflow is saved
in [docs/pyinstaller.yaml](docs/pyinstaller.yaml) for reference.

- Discontinued use due to fatal error on Windows build related to Kivy and
  OpenGL versions, see
  issue [#2](https://github.com/scalpelspace/pyblasher/issues/2).

The badge markdown would be as follows:

```
![pyinstaller](https://github.com/scalpelspace/pyblasher/actions/workflows/pyinstaller.yaml/badge.svg)
```
