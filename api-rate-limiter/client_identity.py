"""Resolve rate-limit client addresses across explicitly trusted proxies."""

from ipaddress import ip_address, ip_network
from typing import Collection, Optional


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

    try:
        peer = ip_address(peer_ip)
        peer_is_trusted = any(
            peer in ip_network(cidr, strict=False) for cidr in trusted_proxy_cidrs
        )
    except ValueError:
        return peer_ip
    if not peer_is_trusted:
        return peer_ip

    forwarded = [value.strip() for value in forwarded_for.split(",")]
    if len(forwarded) < trusted_proxy_hops or any(not value for value in forwarded):
        return None
    candidate = forwarded[-trusted_proxy_hops]
    try:
        ip_address(candidate)
    except ValueError:
        return None

    return candidate
