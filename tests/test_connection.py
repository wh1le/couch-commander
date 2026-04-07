import asyncio
import threading
from unittest.mock import AsyncMock, MagicMock, patch

from lib.connection import TVConnection


def test_init_defaults():
    conn = TVConnection()
    assert conn.ip == "192.168.50.160"
    assert conn.client is None
    assert conn.loop is None


def test_init_custom_ip():
    conn = TVConnection(ip="10.0.0.1")
    assert conn.ip == "10.0.0.1"


def test_tv_property_returns_client():
    conn = TVConnection()
    conn.client = MagicMock()
    assert conn.tv is conn.client


def test_tv_property_none_when_no_client():
    conn = TVConnection()
    assert conn.tv is None


def test_run_async_does_nothing_without_loop():
    conn = TVConnection()
    coro = AsyncMock()()
    conn.run_async(coro)
    # Should not raise — just silently skip
    coro.close()


def test_run_async_does_nothing_without_client():
    conn = TVConnection()
    conn.loop = asyncio.new_event_loop()
    coro = AsyncMock()()
    conn.run_async(coro)
    coro.close()
    conn.loop.close()


def test_run_async_submits_to_loop():
    conn = TVConnection()
    conn.loop = asyncio.new_event_loop()
    conn.client = MagicMock()

    future = MagicMock()
    with patch("asyncio.run_coroutine_threadsafe", return_value=future) as mock_submit:
        coro = AsyncMock()()
        conn.run_async(coro)
        mock_submit.assert_called_once_with(coro, conn.loop)

    conn.loop.close()


def test_start_creates_daemon_thread():
    conn = TVConnection()
    with patch.object(conn, "_run"):
        conn.start(on_connected=lambda: None, on_failed=lambda e: None)
        assert conn._thread is not None
        assert conn._thread.daemon is True
        conn._thread.join(timeout=1)


@patch("lib.connection.WebOsClient")
@patch("lib.connection.load_key", return_value="existing_key")
@patch("lib.connection.save_key")
def test_run_connects_and_calls_on_connected(mock_save, mock_load, MockClient):
    client = AsyncMock()
    client.client_key = "existing_key"
    client.connect = AsyncMock()
    MockClient.return_value = client

    conn = TVConnection(ip="10.0.0.1")
    connected = threading.Event()

    def on_connected():
        connected.set()
        conn.loop.call_soon_threadsafe(conn.loop.stop)

    conn.start(on_connected=on_connected)
    assert connected.wait(timeout=3)
    mock_load.assert_called_once_with("10.0.0.1")
    MockClient.assert_called_once_with("10.0.0.1", client_key="existing_key")
    client.connect.assert_awaited_once()
    mock_save.assert_not_called()  # key unchanged


@patch("lib.connection.WebOsClient")
@patch("lib.connection.load_key", return_value="old_key")
@patch("lib.connection.save_key")
def test_run_saves_new_key(mock_save, mock_load, MockClient):
    client = AsyncMock()
    client.client_key = "new_key"
    client.connect = AsyncMock()
    MockClient.return_value = client

    conn = TVConnection(ip="10.0.0.1")
    connected = threading.Event()

    def on_connected():
        connected.set()
        conn.loop.call_soon_threadsafe(conn.loop.stop)

    conn.start(on_connected=on_connected)
    assert connected.wait(timeout=3)
    mock_save.assert_called_once_with("new_key", "10.0.0.1")


@patch("lib.connection.WebOsClient")
@patch("lib.connection.load_key", return_value=None)
def test_run_calls_on_failed(mock_load, MockClient):
    client = AsyncMock()
    client.connect = AsyncMock(side_effect=ConnectionError("refused"))
    MockClient.return_value = client

    conn = TVConnection(ip="10.0.0.1")
    failed = threading.Event()
    error = []

    def on_failed(e):
        error.append(e)
        failed.set()

    conn.start(on_failed=on_failed)
    assert failed.wait(timeout=3)
    assert isinstance(error[0], ConnectionError)
