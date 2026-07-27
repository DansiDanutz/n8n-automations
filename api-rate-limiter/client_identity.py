"""Resolve rate-limit client addresses across explicitly trusted proxies."""

from ipaddress import ip_address


def resolve_client_ip(
    peer_ip: str,
    forwarded_for: str | None,
    *,
    trusted_proxy_hops: int,
) -> str:
    """Return a validated client IP without trusting arbitrary forwarding data."""
    if trusted_proxy_hops <= 0 or not forwarded_for:
        return peer_ip

    forwarded = [value.strip() for value in forwarded_for.split(",")]
    if len(forwarded) < trusted_proxy_hops or any(not value for value in forwarded):
        return peer_ip
    try:
        for value in forwarded:
            ip_address(value)
    except ValueError:
        return peer_ip

    return forwarded[-trusted_proxy_hops]
