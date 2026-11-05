"""Protocol client tests against fake TCP servers (no Home Assistant needed)."""
from __future__ import annotations

import asyncio
import struct
from collections.abc import Awaitable, Callable
from unittest.mock import patch

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
    PROTOCOL_AUTO,
    PROTOCOL_MODBUS_TCP,
    PROTOCOL_NATIVE_TCP,
)
from custom_components.breezart.coordinator import (
    BreezartModbusClient,
    BreezartTCPClient,
    DiscoveredBreezartDevice,
    ModbusExceptionError,
    async_detect_and_connect_client,
    async_discover_breezart_devices,
    build_subnet_hosts,
)

# Fake devices listen on 127.0.0.1; the HA test harness blocks sockets by default.
pytestmark = pytest.mark.usefixtures("socket_enabled")

Handler = Callable[[asyncio.StreamReader, asyncio.StreamWriter], Awaitable[None]]


@pytest.fixture
async def serve():
    """Start a TCP server on localhost running the given handler; return its port."""
    servers: list[asyncio.Server] = []
    writers: list[asyncio.StreamWriter] = []
    tasks: list[asyncio.Task[None]] = []

    async def _serve(handler: Handler) -> int:
        async def tracked(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            task = asyncio.current_task()
            if task is not None:
                tasks.append(task)
            writers.append(writer)
            await handler(reader, writer)

        server = await asyncio.start_server(tracked, "127.0.0.1", 0)
        servers.append(server)
        return server.sockets[0].getsockname()[1]

    yield _serve
    # Close server-side sockets and cancel any sleeping handler tasks so
    # pytest-homeassistant-custom-component's verify_cleanup sees no lingering tasks.
    for writer in writers:
        writer.close()
    for task in tasks:
        if not task.done():
            task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
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


# --- Protocol detection -----------------------------------------------------


class _ProbeClient:
    """Records what the detection loop tried; fails unless (protocol, port) is accepted."""

    def __init__(self, accepted: set[tuple[str, int]], log: list, *, protocol: str, port: int, **_):
        self.protocol, self.port = protocol, port
        self._accepted, self._log = accepted, log
        self.connected = False

    async def connect(self) -> None:
        self.connected = True

    async def get_properties(self) -> None:
        self._log.append((self.protocol, self.port))
        if (self.protocol, self.port) not in self._accepted:
            raise ConnectionError("no answer")

    async def disconnect(self) -> None:
        self.connected = False


async def _detect(protocol: str, port: int, accepted: set[tuple[str, int]]):
    log: list[tuple[str, int]] = []
    made: list[_ProbeClient] = []

    def factory(**kwargs):
        made.append(_ProbeClient(accepted, log, **kwargs))
        return made[-1]

    with patch("custom_components.breezart.coordinator.create_breezart_client", factory):
        try:
            result = await async_detect_and_connect_client("192.0.2.10", port, protocol=protocol)
        except ConnectionError:
            result = None
    return result, log, made


@pytest.mark.parametrize(
    ("protocol", "port", "expected_port"),
    [
        (PROTOCOL_NATIVE_TCP, 502, 1560),   # Modbus entry switched to Native
        (PROTOCOL_MODBUS_TCP, 1560, 502),   # Native entry switched to Modbus
        (PROTOCOL_NATIVE_TCP, 4000, 4000),  # custom ports are kept
        (PROTOCOL_MODBUS_TCP, 5020, 5020),
    ],
)
async def test_detect_explicit_protocol_uses_matching_port(
    protocol: str, port: int, expected_port: int
) -> None:
    """An explicit protocol is probed once, on its own default port if needed."""
    result, log, _ = await _detect(protocol, port, {(protocol, expected_port)})
    assert log == [(protocol, expected_port)]
    assert result is not None
    assert result[1:] == (protocol, expected_port)


async def test_detect_auto_falls_back_to_native() -> None:
    """Auto on 502 tries Modbus first, then Native on 1560."""
    result, log, _ = await _detect(PROTOCOL_AUTO, 502, {(PROTOCOL_NATIVE_TCP, 1560)})
    assert log == [(PROTOCOL_MODBUS_TCP, 502), (PROTOCOL_NATIVE_TCP, 1560)]
    assert result[1:] == (PROTOCOL_NATIVE_TCP, 1560)


@pytest.mark.parametrize("protocol", [PROTOCOL_NATIVE_TCP, PROTOCOL_MODBUS_TCP, PROTOCOL_AUTO])
async def test_detect_failure_closes_probe_sockets(protocol: str) -> None:
    """A probe that connects but fails get_properties() doesn't leak its socket."""
    result, log, made = await _detect(protocol, 502, accepted=set())
    assert result is None
    assert log  # at least one candidate was tried
    assert made and not any(client.connected for client in made)


# --- Local network discovery ------------------------------------------------


def test_build_subnet_hosts_filters_local_and_excluded_ips() -> None:
    """Subnet host builder returns /24 private hosts excluding local and configured IPs."""
    hosts = build_subnet_hosts("192.168.1.42", exclude_hosts={"192.168.1.121"})
    assert len(hosts) == 252
    assert "192.168.1.1" in hosts
    assert "192.168.1.254" in hosts
    assert "192.168.1.42" not in hosts
    assert "192.168.1.121" not in hosts

    # Loopback or invalid IPs produce no LAN scan targets
    assert build_subnet_hosts("127.0.0.1") == []
    assert build_subnet_hosts("invalid") == []


async def test_discover_breezart_devices_identifies_modbus_and_native(serve) -> None:
    """Discovery detects Modbus TCP, Native TCP (even with custom password), and ignores non-Breezart ports."""
    mb_handler, _ = modbus_handler()
    modbus_port = await serve(mb_handler)

    async def native_wrong_pass_handler(reader, writer):
        await reader.read(100)
        writer.write(b"VEPas_")
        await writer.drain()

    native_port = await serve(native_wrong_pass_handler)

    async def junk_http_handler(reader, writer):
        await reader.read(100)
        writer.write(b"HTTP/1.1 400 Bad Request\r\n\r\n")
        await writer.drain()

    junk_port = await serve(junk_http_handler)

    found = await async_discover_breezart_devices(
        hosts=["127.0.0.1"],
        candidates=(
            (PROTOCOL_MODBUS_TCP, modbus_port),
            (PROTOCOL_NATIVE_TCP, native_port),
            (PROTOCOL_NATIVE_TCP, junk_port),
        ),
    )

    assert found == [
        DiscoveredBreezartDevice(
            host="127.0.0.1",
            port=modbus_port,
            protocol=PROTOCOL_MODBUS_TCP,
            firmware_ver="JL204c7",
            requires_password=False,
        ),
        DiscoveredBreezartDevice(
            host="127.0.0.1",
            port=native_port,
            protocol=PROTOCOL_NATIVE_TCP,
            firmware_ver=None,
            requires_password=True,
        ),
    ]
