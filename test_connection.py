#!/usr/bin/env python3
"""Test Breezart TCP connection using centralized constants and bilingual output."""
from __future__ import annotations

import asyncio
import importlib.util
import pathlib
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
DEFAULT_PASSWORD = _const.DEFAULT_PASSWORD
DEFAULT_PORT = _const.DEFAULT_PORT
DEFAULT_TIMEOUT = _const.DEFAULT_TIMEOUT
DELIMITER = _const.DELIMITER
HEX_FORMAT_4DIGIT = _const.HEX_FORMAT_4DIGIT
READ_BUFFER_SIZE = _const.READ_BUFFER_SIZE
REQ_GET_PROPERTIES = _const.REQ_GET_PROPERTIES
normalize_language = _const.normalize_language

CLI_MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "testing": "Testing Breezart at {host}:{port} with password {password}",
        "connecting": "Connecting to {host}:{port}...",
        "connected": "TCP connection established",
        "sending": "Sending: {request}",
        "sent": "Request sent",
        "waiting": "Waiting for response ({timeout} seconds)...",
        "received": "Response received: {response}",
        "timeout": "Timeout - no response received",
        "partial": "Partial data received: {raw}",
        "no_data": "No data available",
        "closed": "Connection closed",
        "conn_timeout": "Connection timeout",
        "conn_refused": "Connection refused - is the device on?",
        "error": "Error: {err}",
    },
    "ru": {
        "testing": "Проверка Breezart по адресу {host}:{port} с паролем {password}",
        "connecting": "Подключение к {host}:{port}...",
        "connected": "TCP-соединение установлено",
        "sending": "Отправка: {request}",
        "sent": "Запрос отправлен",
        "waiting": "Ожидание ответа ({timeout} сек.)...",
        "received": "Ответ получен: {response}",
        "timeout": "Таймаут — ответ не получен",
        "partial": "Получены частичные данные: {raw}",
        "no_data": "Данные отсутствуют",
        "closed": "Соединение закрыто",
        "conn_timeout": "Таймаут подключения",
        "conn_refused": "В подключении отказано — устройство включено?",
        "error": "Ошибка: {err}",
    },
}


async def test_breezart(
    host: str, port: int, password: int, lang: str = "en"
) -> bool:
    """Test connection to Breezart."""
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
                response = raw.decode().strip()
                print(f"✓ {msg['received'].format(response=response)}")
            else:
                print(f"✗ {msg['no_data']}")
        except asyncio.TimeoutError:
            print(f"✗ {msg['timeout']}")

        writer.close()
        await writer.wait_closed()
        print(f"✓ {msg['closed']}")

    except asyncio.TimeoutError:
        print(f"✗ {msg['conn_timeout']}")
        return False
    except ConnectionRefusedError:
        print(f"✗ {msg['conn_refused']}")
        return False
    except Exception as err:
        print(f"✗ {msg['error'].format(err=err)}")
        return False

    return True


if __name__ == "__main__":
    host_arg = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_HOST
    port_arg = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PORT
    password_arg = int(sys.argv[3]) if len(sys.argv) > 3 else int(DEFAULT_PASSWORD)
    lang_arg = sys.argv[4] if len(sys.argv) > 4 else "ru"

    msg_table = CLI_MESSAGES[normalize_language(lang_arg)]
    print(
        msg_table["testing"].format(
            host=host_arg, port=port_arg, password=password_arg
        )
    )
    print("-" * 60)

    asyncio.run(test_breezart(host_arg, port_arg, password_arg, lang_arg))
