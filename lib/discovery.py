import socket
import re


SSDP_ADDR = "239.255.255.250"
SSDP_PORT = 1900
SSDP_REQUEST = (
    "M-SEARCH * HTTP/1.1\r\n"
    "HOST: 239.255.255.250:1900\r\n"
    "MAN: \"ssdp:discover\"\r\n"
    "MX: 3\r\n"
    "ST: urn:lge-com:service:webos-second-screen:1\r\n"
    "\r\n"
)


def scan(timeout=3):
    """Scan for LG webOS TVs on the local network via SSDP.

    Returns a list of dicts: [{"ip": "...", "name": "..."}]
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(timeout)

    sock.sendto(SSDP_REQUEST.encode(), (SSDP_ADDR, SSDP_PORT))

    found = {}
    while True:
        try:
            data, addr = sock.recvfrom(4096)
            ip = addr[0]
            if ip in found:
                continue
            response = data.decode(errors="replace")
            name = _parse_name(response)
            found[ip] = {"ip": ip, "name": name}
        except socket.timeout:
            break

    sock.close()
    return list(found.values())


def _parse_name(response):
    """Extract a friendly name from the SSDP response headers."""
    for header in ("USN", "SERVER"):
        match = re.search(rf"^{header}:\s*(.+)$", response, re.MULTILINE | re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return "LG TV"
