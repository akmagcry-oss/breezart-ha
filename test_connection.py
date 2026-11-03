#!/usr/bin/env python3
"""Test Breezart connection via Modbus TCP (port 502, JLV135/JL204c7) or Native TCP (port 1560)."""
from __future__ import annotations

import asyncio
import importlib.util
import pathlib
import struct
import sys


def _load_const():
    """Load const.py directly without requiring homeassistant package installed."""
    const_path = (
        pathlib.Path(__file__).resolve().parent
        / "custom_components"
        / "breezart"
        / "const.py"
    )
    spec = importlib.util.spec_from_file_location("breezart_const", const_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {const_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_const = _load_const()
DEFAULT_HOST = _const.DEFAULT_HOST
DEFAULT_MODBUS_PORT = _const.DEFAULT_MODBUS_PORT
DEFAULT_PASSWORD = _const.DEFAULT_PASSWORD
DEFAULT_PORT = _const.DEFAULT_PORT
DEFAULT_SLAVE_ID = _const.DEFAULT_SLAVE_ID
DEFAULT_TIMEOUT = _const.DEFAULT_TIMEOUT
DELIMITER = _const.DELIMITER
HEX_FORMAT_4DIGIT = _const.HEX_FORMAT_4DIGIT
MODBUS_FC_READ_HOLDING = _const.MODBUS_FC_READ_HOLDING
MODBUS_FC_READ_INPUT = _const.MODBUS_FC_READ_INPUT
MODBUS_HR_BLOCK_COUNT = _const.MODBUS_HR_BLOCK_COUNT
MODBUS_HR_BLOCK_START = _const.MODBUS_HR_BLOCK_START
MODBUS_IR_SENSORS_BLOCK_COUNT = _const.MODBUS_IR_SENSORS_BLOCK_COUNT
MODBUS_IR_SENSORS_BLOCK_START = _const.MODBUS_IR_SENSORS_BLOCK_START
MODBUS_IR_STATUS_BLOCK_COUNT = _const.MODBUS_IR_STATUS_BLOCK_COUNT
MODBUS_IR_STATUS_BLOCK_START = _const.MODBUS_IR_STATUS_BLOCK_START
MODBUS_MBAP_HEADER_LEN = _const.MODBUS_MBAP_HEADER_LEN
MODBUS_PROTOCOL_ID = _const.MODBUS_PROTOCOL_ID
MODBUS_READ_DELAY_SECONDS = _const.MODBUS_READ_DELAY_SECONDS
MODBUS_READ_PDU_LEN = _const.MODBUS_READ_PDU_LEN
READ_BUFFER_SIZE = _const.READ_BUFFER_SIZE
REQ_GET_PROPERTIES = _const.REQ_GET_PROPERTIES
SIGN_BIT_MASK = _const.SIGN_BIT_MASK
SIGN_BIT_OFFSET = _const.SIGN_BIT_OFFSET
TEMP_DIVISOR = _const.TEMP_DIVISOR
normalize_language = _const.normalize_language

CLI_MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "testing": "Testing Breezart at {host}:{port}",
        "connecting": "Connecting to {host}:{port}...",
        "connected": "TCP connection established",
        "sending": "Sending: {request}",
        "sent": "Request sent",
        "waiting": "Waiting for response ({timeout} seconds)...",
        "received": "Response received: {response}",
        "timeout": "Timeout - no response received",
        "no_data": "No data available",
        "closed": "Connection closed",
        "conn_timeout": "Connection timeout",
        "conn_refused": "Connection refused on port {port}",
        "error": "Error: {err}",
        "modbus_probe": "Testing Modbus TCP (JLV135 / JL204c7) on {host}:{port} (Slave ID={slave_id})...",
        "modbus_ok": "Modbus TCP Holding[0..8]: fan_set={fan}%, temp_target={temp}°C, power={power}, mode_hc={mode}",
        "modbus_status": "Modbus TCP Input[10..23]: cur_mode={cur_mode}, status=0x{status:04X}, cur_temp={cur_t}°C, cur_fan={cur_f}%",
        "modbus_sensors": "Modbus TCP Input[50..63]: supply={t_sup}°C, room={t_room}°C, outdoor={t_out}°C, water={t_wat}°C",
    },
    "ru": {
        "testing": "Проверка Breezart по адресу {host}:{port}",
        "connecting": "Подключение к {host}:{port}...",
        "connected": "TCP-соединение установлено",
        "sending": "Отправка: {request}",
        "sent": "Запрос отправлен",
        "waiting": "Ожидание ответа ({timeout} сек.)...",
        "received": "Ответ получен: {response}",
        "timeout": "Таймаут — ответ не получен",
        "no_data": "Данные отсутствуют",
        "closed": "Соединение закрыто",
        "conn_timeout": "Таймаут подключения",
        "conn_refused": "Порт {port} закрыт (Connection refused)",
        "error": "Ошибка: {err}",
        "modbus_probe": "Проверка Modbus TCP (пульт JLV135 / контроллер JL204c7) на {host}:{port} (Slave ID={slave_id})...",
        "modbus_ok": "Modbus TCP Holding[0..8]: задание скорости={fan}%, целевая темп.={temp}°C, питание={power}, режим(mode_hc)={mode}",
        "modbus_status": "Modbus TCP Input[10..23]: режим={cur_mode}, статус=0x{status:04X}, текущая темп.={cur_t}°C, вентилятор={cur_f}%",
        "modbus_sensors": "Modbus TCP Input[50..63]: приток={t_sup}°C, комната={t_room}°C, улица={t_out}°C, вода={t_wat}°C",
    },
}


def _signed16(val: int) -> int:
    return val - SIGN_BIT_OFFSET if (val & SIGN_BIT_MASK) else val


async def _modbus_read(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    tx_id: int,
    slave_id: int,
    func_code: int,
    start_addr: int,
    count: int,
) -> list[int]:
    frame = struct.pack(
        ">HHHBBHH",
        tx_id,
        MODBUS_PROTOCOL_ID,
        MODBUS_READ_PDU_LEN,
        slave_id,
        func_code,
        start_addr,
        count,
    )
    writer.write(frame)
    await writer.drain()
    await asyncio.sleep(MODBUS_READ_DELAY_SECONDS)

    header = await asyncio.wait_for(
        reader.readexactly(MODBUS_MBAP_HEADER_LEN),
        timeout=float(DEFAULT_TIMEOUT),
    )
    _rx_tx, _rx_proto, rx_len, _rx_unit = struct.unpack(">HHHB", header)
    pdu = await asyncio.wait_for(
        reader.readexactly(max(0, rx_len - 1)),
        timeout=float(DEFAULT_TIMEOUT),
    )
    if pdu[0] & 0x80:
        raise ValueError(f"Modbus exception 0x{pdu[1]:02X} on FC 0x{func_code:02X} addr={start_addr}")
    return list(struct.unpack(f">{count}H", pdu[2 : 2 + count * 2]))


async def test_breezart_modbus(
    host: str,
    port: int = DEFAULT_MODBUS_PORT,
    slave_id: int = DEFAULT_SLAVE_ID,
    lang: str = "ru",
) -> bool:
    """Test Modbus TCP connection (port 502) for JLV135 / JL204c7."""
    msg = CLI_MESSAGES[normalize_language(lang)]
    print(msg["modbus_probe"].format(host=host, port=port, slave_id=slave_id))

    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=float(DEFAULT_TIMEOUT),
        )
        print(f"✓ {msg['connected']}")

        hr = await _modbus_read(
            reader,
            writer,
            1,
            slave_id,
            MODBUS_FC_READ_HOLDING,
            MODBUS_HR_BLOCK_START,
            MODBUS_HR_BLOCK_COUNT,
        )
        print(
            "✓ "
            + msg["modbus_ok"].format(
                fan=round(hr[0] / 100.0, 1),
                temp=round(_signed16(hr[1]) / TEMP_DIVISOR, 1),
                power=hr[3],
                mode=hr[7],
            )
        )

        ir = await _modbus_read(
            reader,
            writer,
            2,
            slave_id,
            MODBUS_FC_READ_INPUT,
            MODBUS_IR_STATUS_BLOCK_START,
            MODBUS_IR_STATUS_BLOCK_COUNT,
        )
        print(
            "✓ "
            + msg["modbus_status"].format(
                cur_mode=ir[0],
                status=ir[1],
                cur_t=round(_signed16(ir[3]) / TEMP_DIVISOR, 1),
                cur_f=round(ir[7] / 100.0, 1),
            )
        )

        sens = await _modbus_read(
            reader,
            writer,
            3,
            slave_id,
            MODBUS_FC_READ_INPUT,
            MODBUS_IR_SENSORS_BLOCK_START,
            MODBUS_IR_SENSORS_BLOCK_COUNT,
        )
        print(
            "✓ "
            + msg["modbus_sensors"].format(
                t_sup=round(_signed16(sens[0]) / TEMP_DIVISOR, 1) if sens[1] == 0 else "N/A",
                t_room=round(_signed16(sens[4]) / TEMP_DIVISOR, 1) if sens[5] == 0 else "N/A",
                t_out=round(_signed16(sens[8]) / TEMP_DIVISOR, 1) if sens[9] == 0 else "N/A",
                t_wat=round(_signed16(sens[12]) / TEMP_DIVISOR, 1) if sens[13] == 0 else "N/A",
            )
        )

        writer.close()
        await writer.wait_closed()
        print(f"✓ {msg['closed']}")
        return True
    except asyncio.TimeoutError:
        print(f"✗ {msg['conn_timeout']}")
        return False
    except ConnectionRefusedError:
        print(f"✗ {msg['conn_refused'].format(port=port)}")
        return False
    except Exception as err:
        print(f"✗ {msg['error'].format(err=err)}")
        return False


async def test_breezart_native(
    host: str, port: int, password: int, lang: str = "ru"
) -> bool:
    """Test Native TCP connection (port 1560) for TPD-283U-H."""
    msg = CLI_MESSAGES[normalize_language(lang)]
    print(msg["connecting"].format(host=host, port=port))

    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=float(DEFAULT_TIMEOUT),
        )
        print(f"✓ {msg['connected']}")

        password_hex = format(password, HEX_FORMAT_4DIGIT)
        request = f"{REQ_GET_PROPERTIES}{DELIMITER}{password_hex}"
        print(msg["sending"].format(request=request))

        writer.write(request.encode())
        await writer.drain()
        print(f"✓ {msg['sent']}")

        print(msg["waiting"].format(timeout=DEFAULT_TIMEOUT))
        try:
            raw = await asyncio.wait_for(
                reader.read(READ_BUFFER_SIZE),
                timeout=float(DEFAULT_TIMEOUT),
            )
            if raw:
                response = raw.decode(errors="ignore").strip()
                print(f"✓ {msg['received'].format(response=response)}")
            else:
                print(f"✗ {msg['no_data']}")
        except asyncio.TimeoutError:
            print(f"✗ {msg['timeout']}")

        writer.close()
        await writer.wait_closed()
        print(f"✓ {msg['closed']}")
        return True

    except asyncio.TimeoutError:
        print(f"✗ {msg['conn_timeout']}")
        return False
    except ConnectionRefusedError:
        print(f"✗ {msg['conn_refused'].format(port=port)}")
        return False
    except Exception as err:
        print(f"✗ {msg['error'].format(err=err)}")
        return False


async def main() -> None:
    """Run connection test with auto-fallback between port 502 (Modbus) and 1560 (Native TCP)."""
    host_arg = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_HOST
    port_arg = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_MODBUS_PORT
    password_arg = int(sys.argv[3]) if len(sys.argv) > 3 else int(DEFAULT_PASSWORD)
    lang_arg = sys.argv[4] if len(sys.argv) > 4 else "ru"

    msg_table = CLI_MESSAGES[normalize_language(lang_arg)]
    print(msg_table["testing"].format(host=host_arg, port=port_arg))
    print("-" * 60)

    if port_arg == DEFAULT_MODBUS_PORT:
        ok = await test_breezart_modbus(host_arg, port_arg, DEFAULT_SLAVE_ID, lang_arg)
        if not ok:
            print("-" * 60)
            await test_breezart_native(host_arg, DEFAULT_PORT, password_arg, lang_arg)
    else:
        ok = await test_breezart_native(host_arg, port_arg, password_arg, lang_arg)
        if not ok:
            print("-" * 60)
            await test_breezart_modbus(host_arg, DEFAULT_MODBUS_PORT, DEFAULT_SLAVE_ID, lang_arg)


if __name__ == "__main__":
    asyncio.run(main())
