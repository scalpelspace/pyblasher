"""NOR Flash Memory communication prototype (USB to UART communication)."""

import string
import time

import serial

# Flash memory control defined values
SOF = 0x7E
CMD_ACK = 0x06
CMD_NACK = 0x07
CMD_WRITE_EN = 0x10
CMD_WRITE_DEN = 0x11
CMD_WRITE = 0x12
CMD_READ_DATA = 0x20
CMD_DATA = 0x21


def __crc16_calc(data: bytes, init: int = 0xFFFF, poly: int = 0x1021) -> int:
    crc = init
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ poly) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def __build_frame(cmd: int, payload: bytes = b"") -> bytes:
    length = len(payload)
    frame = bytearray([SOF, cmd]) + length.to_bytes(2, "big") + payload
    crc = __crc16_calc(frame)
    frame += crc.to_bytes(2, "big")
    return bytes(frame)


def __parse_frame(buf: bytes):
    if len(buf) < 6 or buf[0] != SOF:
        raise ValueError("Frame too short or no SOF")
    cmd = buf[1]
    length = int.from_bytes(buf[2:4], "big")
    total_len = 1 + 1 + 2 + length + 2
    if len(buf) < total_len:
        raise ValueError("Incomplete frame")
    payload = buf[4 : 4 + length]
    recv_crc = int.from_bytes(buf[4 + length : 4 + length + 2], "big")
    calc_crc = __crc16_calc(buf[: 4 + length])
    if recv_crc != calc_crc:
        raise ValueError(
            f"CRC mismatch (got 0x{recv_crc:04X}, calc=0x{calc_crc:04X})"
        )
    return cmd, payload, total_len


def __read_exactly(ser, count, timeout=1.0):
    """
    Read exactly `count` bytes from ser, or raise TimeoutError.
    """
    buf = bytearray()
    deadline = time.time() + timeout
    while len(buf) < count:
        if time.time() > deadline:
            raise TimeoutError(f"Timeout reading {count} bytes, got {len(buf)}")
        chunk = ser.read(count - len(buf))
        if chunk:
            buf.extend(chunk)
        else:
            # No data right now -> wait a bit
            time.sleep(0.001)
    return bytes(buf)


def __read_frame(ser, timeout=1.0):
    """
    1) Sync on 0x7E
    2) Read CMD (1B) + LEN_H + LEN_L (2B)
    3) Read [LEN] + CRC(2)
    Returns full frame bytes.
    """
    # 1) Wait for SOF
    deadline = time.time() + timeout
    while True:
        if time.time() > deadline:
            raise TimeoutError("Timeout waiting for SOF")
        b = ser.read(1)
        if not b:
            time.sleep(0.001)
            continue
        if b[0] == SOF:
            break

    # 2) Read cmd + length
    hdr = __read_exactly(ser, 3, timeout)
    cmd = hdr[0]
    length = int.from_bytes(hdr[1:3], "big")

    # 3) Read payload + CRC
    rest = __read_exactly(ser, length + 2, timeout)

    frame = bytes([SOF]) + hdr + rest
    return frame


def write_enable(ser: serial.Serial):
    """Unlock flash writes for exactly one write operation."""
    ser.reset_input_buffer()
    ser.write(__build_frame(CMD_WRITE_EN))
    cmd, _, _ = __parse_frame(__read_frame(ser))
    if cmd != CMD_ACK:
        raise RuntimeError("WREN not ACKed")


def write_disable(ser: serial.Serial):
    """Manually lock flash writes (if you ever need to)."""
    ser.reset_input_buffer()
    ser.write(__build_frame(CMD_WRITE_DEN))
    cmd, _, _ = __parse_frame(__read_frame(ser))
    if cmd != CMD_ACK:
        raise RuntimeError("WDIS not ACKed")


def read_section(
    ser: serial.Serial, start_addr: int, length: int, chunk_size: int = 256
) -> bytes:
    """
    Dump an arbitrary flash range by repeatedly issuing CMD_READ.
    """
    data = bytearray()
    for offset in range(0, length, chunk_size):
        sz = min(chunk_size, length - offset)
        payload = (start_addr + offset).to_bytes(3, "big") + sz.to_bytes(
            2, "big"
        )
        ser.reset_input_buffer()
        ser.write(__build_frame(CMD_READ_DATA, payload))
        frame = __read_frame(ser)
        cmd, chunk, _ = __parse_frame(frame)
        if cmd != CMD_DATA:
            raise RuntimeError(f"Expected DATA, got 0x{cmd:02X}")
        data.extend(chunk)
    return bytes(data)


def save_hexdump(
    data: bytes, start_addr: int, filename: str, line_width: int = 16
):
    """Writes a hexdump to `filename`.

    Each hexdump line shows:
        ```
        OFFSET:  XX XX XX ... D D D ... ASCII...
        ```

    Example hexdump line:
        ```
        00001000:  00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F    0   1   3   4   5   6   7   8   9  10  11  12  13  14  15  16   ................
        ```
    """
    with open(filename, "w", encoding="utf-8") as f:
        for i in range(0, len(data), line_width):
            chunk = data[i : i + line_width]
            # Hex bytes
            hex_bytes = " ".join(f"{b:02X}" for b in chunk)
            # Decimal values
            dec_bytes = " ".join(f"{b:3d}" for b in chunk)
            # ASCII (printable or dot)
            ascii_repr = "".join(
                (chr(b) if chr(b) in string.printable and b >= 0x20 else ".")
                for b in chunk
            )

            offset = start_addr + i
            # Pad hex_bytes to fixed width so columns line up
            hex_col_width = line_width * 3 - 1
            f.write(
                f"{offset:08X}:  {hex_bytes:<{hex_col_width}}  {dec_bytes:<{line_width*4}}  {ascii_repr}\n"
            )
