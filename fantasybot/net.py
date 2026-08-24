"""Polite HTTP fetching: retries on 429 while honoring Retry-After.

Adds no artificial waits: it only waits if the server throttles us (429). This
way it doesn't get in the way of urgent actions but avoids bans from overload.
"""

import time
import urllib.error
import urllib.request

from . import config


def get(url: str, timeout: int = 20, retries: int = 3) -> str:
    """Fetches text. On 429, waits (Retry-After or backoff) and retries."""
    delay = 2
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, headers={"User-Agent": config.USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries:
                retry_after = e.headers.get("Retry-After") or ""
                wait = int(retry_after) if retry_after.isdigit() else delay
                time.sleep(min(wait, 30))
                delay *= 2
                continue
            raise
    raise RuntimeError(f"No response after {retries} retries: {url}")


def prefer_ipv4():
    """Makes address resolution return IPv4 first.

    On hosts with a flaky IPv6 path (common on VPS providers), Python tries the
    AAAA record first and blocks for the whole socket timeout before falling
    back to IPv4 -- freezing a Telegram menu for 35s. Unlike curl, urllib has no
    Happy Eyeballs fallback. Sorting IPv4 first avoids the stall while keeping
    IPv6 as fallback for IPv6-only hosts.

    Disable with FANTASYBOT_PREFER_IPV4=0.
    """
    import os
    import socket

    if os.environ.get("FANTASYBOT_PREFER_IPV4", "1") == "0":
        return
    if getattr(socket, "_fantasybot_ipv4_first", False):
        return

    original = socket.getaddrinfo

    def getaddrinfo_ipv4_first(*args, **kwargs):
        res = original(*args, **kwargs)
        return sorted(res, key=lambda entry: 0 if entry[0] == socket.AF_INET else 1)

    socket.getaddrinfo = getaddrinfo_ipv4_first
    socket._fantasybot_ipv4_first = True
