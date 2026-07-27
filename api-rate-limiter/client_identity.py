"""Resolve rate-limit client addresses across explicitly trusted proxies."""

from ipaddress import ip_address, ip_network
from typing import Collection, Optional


def _address_is_trusted(address: str, trusted_proxy_cidrs: Collection[str]) -> bool:
    try:
        parsed_address = ip_address(address)
    except ValueError:
        return False
    for cidr in trusted_proxy_cidrs:
        try:
            if parsed_address in ip_network(cidr, strict=False):
                return True
        except ValueError:
            continue
    return False


def resolve_client_ip(
    peer_ip: str,
    forwarded_for: Optional[str],
    *,
    trusted_proxy_hops: int,
    trusted_proxy_cidrs: Collection[str],
) -> Optional[str]:
    """Return a validated client IP without trusting arbitrary forwarding data."""
    if trusted_proxy_hops <= 0 or not forwarded_for:
        return peer_ip

    if not _address_is_trusted(peer_ip, trusted_proxy_cidrs):
        return peer_ip

    forwarded = [value.strip() for value in forwarded_for.split(",")]
    if len(forwarded) < trusted_proxy_hops or any(not value for value in forwarded):
        return None
    intervening_proxies = forwarded[-(trusted_proxy_hops - 1):] if trusted_proxy_hops > 1 else []
    if any(
        not _address_is_trusted(proxy, trusted_proxy_cidrs)
        for proxy in intervening_proxies
    ):
        return None
    candidate = forwarded[-trusted_proxy_hops]
    try:
        ip_address(candidate)
    except ValueError:
        return None

    return candidate
