"""ABFSS URL grammar — kernel-leaf pure parser (no package imports).

Single source for ``abfss://<container>@<account>.dfs.core.windows.net/<path>``
splitting.  Domain layers wrap this in their own error types; kernel and
mid-layers call ``split_abfss`` directly and get ``None`` on non-abfss input.
"""
from __future__ import annotations


def split_abfss(url: object) -> tuple[str, str, str] | None:
    """``abfss://container@account.host/a/b`` -> (account, container, "/a/b").

    Returns ``None`` when the value is not a well-formed abfss url.  The
    account is the first DNS label of the host (``.dfs.core.windows.net`` and
    sovereign-cloud variants resolve identically).
    """
    if not isinstance(url, str) or not url.startswith("abfss://") or "@" not in url:
        return None
    rest = url[len("abfss://"):]
    container, _, hostpath = rest.partition("@")
    host, _, path = hostpath.partition("/")
    account = host.split(".")[0]
    if not container or not account:
        return None
    clean = path.strip("/")
    return account, container, "/" + clean if clean else "/"


__all__ = ["split_abfss"]
