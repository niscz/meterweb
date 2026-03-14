from starlette.requests import Request

from meterweb.infrastructure.settings import AppSettings
from meterweb.interfaces.http.web.auth_router import _client_ip


def _request(peer_ip: str, forwarded_for: str | None = None) -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if forwarded_for is not None:
        headers.append((b"x-forwarded-for", forwarded_for.encode("latin-1")))
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/login",
            "headers": headers,
            "query_string": b"",
            "client": (peer_ip, 12345),
        }
    )


def test_client_ip_ignores_forwarded_for_without_trusted_proxy() -> None:
    request = _request(peer_ip="10.0.0.1", forwarded_for="198.51.100.10")
    settings = AppSettings(trust_proxy_headers=False, trusted_proxy_ips=("10.0.0.1",))

    assert _client_ip(request, settings) == "10.0.0.1"


def test_client_ip_uses_first_forwarded_hop_for_trusted_proxy() -> None:
    request = _request(peer_ip="10.0.0.1", forwarded_for="198.51.100.10")
    settings = AppSettings(trust_proxy_headers=True, trusted_proxy_ips=("10.0.0.1",))

    assert _client_ip(request, settings) == "198.51.100.10"


def test_client_ip_parses_first_forwarded_hop_from_list() -> None:
    request = _request(peer_ip="10.0.0.1", forwarded_for="198.51.100.10, 203.0.113.5, 10.0.0.1")
    settings = AppSettings(trust_proxy_headers=True, trusted_proxy_ips=("10.0.0.1",))

    assert _client_ip(request, settings) == "198.51.100.10"
