from unittest.mock import patch, MagicMock
import socket

from lib.discovery import scan, _parse_name


FAKE_RESPONSE = (
    "HTTP/1.1 200 OK\r\n"
    "USN: uuid:abc123::LG webOS TV\r\n"
    "ST: urn:lge-com:service:webos-second-screen:1\r\n"
    "\r\n"
)


class TestParseNname:
    def test_extracts_usn(self):
        assert "LG webOS TV" in _parse_name(FAKE_RESPONSE)

    def test_fallback_name(self):
        assert _parse_name("HTTP/1.1 200 OK\r\n\r\n") == "LG TV"


class TestScan:
    @patch("lib.discovery.socket.socket")
    def test_finds_tv(self, MockSocket):
        sock = MagicMock()
        MockSocket.return_value = sock
        sock.recvfrom.side_effect = [
            (FAKE_RESPONSE.encode(), ("10.0.0.5", 1900)),
            socket.timeout,
        ]

        results = scan(timeout=1)
        assert len(results) == 1
        assert results[0]["ip"] == "10.0.0.5"

    @patch("lib.discovery.socket.socket")
    def test_no_tvs(self, MockSocket):
        sock = MagicMock()
        MockSocket.return_value = sock
        sock.recvfrom.side_effect = socket.timeout

        results = scan(timeout=1)
        assert results == []

    @patch("lib.discovery.socket.socket")
    def test_deduplicates(self, MockSocket):
        sock = MagicMock()
        MockSocket.return_value = sock
        sock.recvfrom.side_effect = [
            (FAKE_RESPONSE.encode(), ("10.0.0.5", 1900)),
            (FAKE_RESPONSE.encode(), ("10.0.0.5", 1900)),
            socket.timeout,
        ]

        results = scan(timeout=1)
        assert len(results) == 1
