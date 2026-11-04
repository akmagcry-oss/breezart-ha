"""Protocol client tests against fake TCP servers (no Home Assistant needed)."""
from __future__ import annotations

import asyncio
import struct
from collections.abc import Awaitable, Callable

import pytest

from custom_components.breezart.const import (
    KEY_FILTER2_POLLUTION,
    KEY_TEMP_OUTDOOR,
    KEY_TEMP_ROOM,
    KEY_TEMP_SUPPLY,
    KEY_TEMP_WATER,
    MODBUS_FC_READ_INPUT,
    MODBUS_IR_FAN_BLOCK_START,
    MODBUS_OPTIONAL_BLOCK_MAX_FAILURES,
)
from custom_components.breezart.coordinator import (
    BreezartModbusClient,
    BreezartTCPClient,
    ModbusExceptionError,
)

# Fake devices listen on 127.0.0.1; the HA test harness blocks sockets by default.
pytestmark = pytest.mark.usefixtures("socket_enabled")

Handler = Callable[[asyncio.StreamReader, asyncio.StreamWriter], Awaitable[None]]


@pytest.fixture
async def serve():
    """Start a TCP server on localhost running the given handler; return its port."""
    servers: list[asyncio.Server] = []
    writers: list[asyncio.StreamWriter] = []

    async def _serve(handler: Handler) -> int:
        async def tracked(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            writers.append(writer)
            await handler(reader, writer)

        server = await asyncio.start_server(tracked, "127.0.0.1", 0)
        servers.append(server)
        return server.sockets[0].getsockname()[1]

    yield _serve
    # Close server-side sockets ourselves: wait_closed() blocks until every client
    # connection ends, which would hang teardown when a test fails mid-connection.
    for writer in writers:
        writer.close()
    for server in servers:
        server.close()
        await asyncio.wait_for(server.wait_closed(), timeout=5)


def _hex16(value: int) -> str:
    return format(value & 0xFFFF, "x")


def _vsens_reply() -> bytes:
    """VSens reply: supply 20.5, room 22.5, outdoor -3.2, water -3.2, filter2 6 %."""
    fields = [
        "VSens",
        _hex16(205), _hex16(40),    # supply temp x10, supply humidity
        _hex16(225), _hex16(45),    # room temp x10, room humidity
        _hex16(-32), _hex16(80),    # outdoor temp x10, outdoor humidity
        _hex16(-32),                # water temp x10
        "fb07", "fb07", "fb07",     # power, CO2, VOC: no data
        "5", "6", "fb07", "fb07",   # filters 1..4
    ]
    return "_".join(fields).encode()


# --- Native TCP -------------------------------------------------------------


async def test_native_sensors_decode_signed_x10_temperatures(serve) -> None:
    """Room and water temperatures are signed x10 values like supply/outdoor."""

    async def handler(reader, writer):
        await reader.read(100)
        writer.write(_vsens_reply())
        await writer.drain()

    client = BreezartTCPClient("127.0.0.1", await serve(handler), timeout=1)
    await client.connect()
    data = await client.get_sensors()
    await client.disconnect()

    assert data[KEY_TEMP_SUPPLY] == 20.5
    assert data[KEY_TEMP_ROOM] == 22.5
    assert data[KEY_TEMP_OUTDOOR] == -3.2
    assert data[KEY_TEMP_WATER] == -3.2


async def test_native_reads_reply_split_across_segments(serve) -> None:
    """A reply delivered in two TCP segments is read whole, not truncated."""
    reply = _vsens_reply()

    async def handler(reader, writer):
        await reader.read(100)
        writer.write(reply[:20])
        await writer.drain()
        await asyncio.sleep(0.01)
        writer.write(reply[20:])
        await writer.drain()

    client = BreezartTCPClient("127.0.0.1", await serve(handler), timeout=1)
    await client.connect()
    data = await client.get_sensors()
    await client.disconnect()

    assert data[KEY_FILTER2_POLLUTION] == 6.0  # field from the second segment


async def test_native_timeout_drops_connection(serve) -> None:
    """After a timeout the socket is closed so a late reply can't be misread."""

    async def handler(reader, writer):
        await reader.read(100)
        await asyncio.sleep(2)  # never answer in time

    client = BreezartTCPClient("127.0.0.1", await serve(handler), timeout=0.2)
    await client.connect()
    with pytest.raises(TimeoutError):
        await client.get_sensors()
    assert not client.is_connected


async def test_native_error_reply_keeps_connection(serve) -> None:
    """A complete error reply (wrong password) leaves the stream usable."""

    async def handler(reader, writer):
        await reader.read(100)
        writer.write(b"VEPas_")
        await writer.drain()
        await asyncio.sleep(1)

    client = BreezartTCPClient("127.0.0.1", await serve(handler), timeout=1)
    await client.connect()
    with pytest.raises(PermissionError):
        await client.get_sensors()
    assert client.is_connected
    await client.disconnect()


# --- Modbus TCP -------------------------------------------------------------


def modbus_handler(
    *, silent: set[int] = frozenset(), illegal: set[int] = frozenset(), bad_tx: set[int] = frozenset()
) -> tuple[Handler, list[int]]:
    """Fake Modbus server. Returns (handler, list of requested start addresses)."""
    requests: list[int] = []

    async def handler(reader, writer):
        while True:
            try:
                frame = await reader.readexactly(12)
            except asyncio.IncompleteReadError:
                return
            tx_id, _, _, unit, func, addr, count = struct.unpack(">HHHBBHH", frame)
            requests.append(addr)
            if addr in silent:
                continue
            if func == 0x06:
                pdu = frame[7:]  # write single register echoes the request
            elif addr in illegal:
                pdu = bytes([func | 0x80, 0x02])
            else:
                pdu = bytes([func, count * 2]) + struct.pack(f">{count}H", *range(count))
            if addr in bad_tx:
                tx_id = (tx_id + 7) & 0xFFFF
            writer.write(struct.pack(">HHHB", tx_id, 0, len(pdu) + 1, unit) + pdu)
            await writer.drain()

    return handler, requests


async def test_modbus_read_and_write(serve) -> None:
    """Registers are decoded and writes are acknowledged."""
    handler, _ = modbus_handler()
    client = BreezartModbusClient("127.0.0.1", await serve(handler), timeout=1)
    await client.connect()
    assert await client._read_registers(MODBUS_FC_READ_INPUT, 10, 3) == [0, 1, 2]
    await client._write_register(0, 5000)
    await client.disconnect()


async def test_modbus_exception_reply_keeps_connection(serve) -> None:
    """An exception frame is complete, so the connection stays in sync."""
    handler, _ = modbus_handler(illegal={999})
    client = BreezartModbusClient("127.0.0.1", await serve(handler), timeout=1)
    await client.connect()
    with pytest.raises(ModbusExceptionError) as exc_info:
        await client._read_registers(MODBUS_FC_READ_INPUT, 999, 1)
    assert exc_info.value.code == 0x02
    assert client.is_connected
    assert await client._read_registers(MODBUS_FC_READ_INPUT, 10, 2) == [0, 1]
    await client.disconnect()


async def test_modbus_transaction_id_mismatch_drops_connection(serve) -> None:
    """A reply for a different transaction is rejected and the socket dropped."""
    handler, _ = modbus_handler(bad_tx={888})
    client = BreezartModbusClient("127.0.0.1", await serve(handler), timeout=1)
    await client.connect()
    with pytest.raises(ConnectionError, match="transaction ID mismatch"):
        await client._read_registers(MODBUS_FC_READ_INPUT, 888, 1)
    assert not client.is_connected


async def test_modbus_timeout_drops_connection(serve) -> None:
    """A silent device causes a timeout and a dropped socket."""
    handler, _ = modbus_handler(silent={777})
    client = BreezartModbusClient("127.0.0.1", await serve(handler), timeout=0.2)
    await client.connect()
    with pytest.raises(TimeoutError):
        await client._read_registers(MODBUS_FC_READ_INPUT, 777, 1)
    assert not client.is_connected


async def test_modbus_illegal_optional_block_disabled_at_once(serve) -> None:
    """An "illegal address" reply disables the optional block immediately."""
    handler, requests = modbus_handler(illegal={MODBUS_IR_FAN_BLOCK_START})
    client = BreezartModbusClient("127.0.0.1", await serve(handler), timeout=1)
    await client.connect()

    for _ in range(3):
        assert await client._read_optional_block(MODBUS_IR_FAN_BLOCK_START, 4, "fan") is None

    assert requests.count(MODBUS_IR_FAN_BLOCK_START) == 1
    assert client.is_connected
    await client.disconnect()


async def test_modbus_silent_optional_block_disabled_after_retries(serve) -> None:
    """A silent optional block reconnects each time, then stops being polled."""
    handler, requests = modbus_handler(silent={MODBUS_IR_FAN_BLOCK_START})
    client = BreezartModbusClient("127.0.0.1", await serve(handler), timeout=0.2)
    await client.connect()

    for _ in range(MODBUS_OPTIONAL_BLOCK_MAX_FAILURES + 2):
        assert await client._read_optional_block(MODBUS_IR_FAN_BLOCK_START, 4, "fan") is None
        # The rest of the poll still works on the reopened socket.
        assert await client._read_registers(MODBUS_FC_READ_INPUT, 10, 1) == [0]

    assert requests.count(MODBUS_IR_FAN_BLOCK_START) == MODBUS_OPTIONAL_BLOCK_MAX_FAILURES
    await client.disconnect()


async def test_modbus_optional_block_failure_counter_resets(serve) -> None:
    """A success between failures resets the count, so the block stays enabled."""
    handler, _ = modbus_handler()
    client = BreezartModbusClient("127.0.0.1", await serve(handler), timeout=1)
    await client.connect()
    client._optional_failures[MODBUS_IR_FAN_BLOCK_START] = MODBUS_OPTIONAL_BLOCK_MAX_FAILURES - 1

    assert await client._read_optional_block(MODBUS_IR_FAN_BLOCK_START, 4, "fan") == [0, 1, 2, 3]
    assert MODBUS_IR_FAN_BLOCK_START not in client._optional_failures
    assert MODBUS_IR_FAN_BLOCK_START not in client._unsupported_blocks
    await client.disconnect()
