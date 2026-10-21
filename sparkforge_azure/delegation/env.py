"""Environment for delegated subprocesses: allowlist first, credential filter second.

Mirrors ``theforge/security/env.py`` (lf-0029) — sparkforge_azure cannot import
theforge, so the same two-layer control is re-implemented here:

- ``SAFE_ENV_ALLOWLIST`` is the primary control: a delegated specialist
  receives only the variables it needs to resolve executables, decode text
  and find a home directory.
- ``CREDENTIAL_PATTERNS`` is the defense-in-depth pass: any credential-shaped
  name is dropped even if it is ever allowlisted by mistake. Azure-shaped
  credentials (``^AZURE_``, ``^ARM_``, ``^AZ_*``, client secrets, connection
  strings) are scrubbed on purpose: Azure authentication for a delegatee
  resolves *inside the delegatee* through its own chain — Azure CLI /
  ``az`` session, ``DefaultAzureCredential`` (managed identity, workload
  identity, service principal env it owns), shared ``~/.azure/`` files —
  never through forwarded environment variables. AWS-shaped credentials
  (``^AWS_``) are scrubbed the same way: this forge never forwards a cloud
  identity it does not own.

Everything persisted or passed to the child is a plain ``str`` map — env
values carrying URL userinfo (``scheme://user@host``) are dropped too,
because they may embed credentials without looking like a credential name.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from typing import Final

SAFE_ENV_ALLOWLIST: Final[frozenset[str]] = frozenset(
    {
        "PATH",          # resolve executables the delegatee spawns
        "PATHEXT",       # Windows: executable extensions on PATH
        "SYSTEMROOT",    # Windows: required by the CPython runtime / Winsock
        "SYSTEMDRIVE",   # Windows: system drive for temp-path resolution
        "WINDIR",        # Windows: expected by system libraries
        "COMSPEC",       # Windows: command interpreter resolution
        "HOME",          # POSIX: home-dir resolution and tool config lookup
        "USERPROFILE",   # Windows: home-dir resolution and tool config lookup
        "TEMP", "TMP", "TMPDIR",  # tempfile
        "LANG", "LC_ALL", "LC_CTYPE",  # consistent text decoding
        "TERM",          # terminal detection (harmless; colors off via NO_COLOR)
        "NO_COLOR",      # keep delegatee output plain
        "PYTHONIOENCODING",
        "PYTHONUTF8",
    }
)

_FORCED_ENV: Final[Mapping[str, str]] = {
    "PYTHONIOENCODING": "utf-8",
    "PYTHONUTF8": "1",
}

CREDENTIAL_PATTERNS: Final[tuple[re.Pattern[str], ...]] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"^AZURE_",        # AZURE_CLIENT_ID/SECRET/TENANT_ID, AZURE_STORAGE_KEY, …
        r"^ARM_",          # Terraform ARM_* service-principal env
        r"^AZ_",           # AZ_* short-form variants
        r"^AWS_",          # never forward another cloud's identity either
        r"(^|_)TOKEN(_|$)",  # *_TOKEN, GITHUB_TOKEN, VAULT_TOKEN, …
        r"SECRET",
        r"PASS(WORD|WD)",
        r"API_?KEY",
        r"ACCESS_?KEY",
        r"CREDENTIAL",     # GOOGLE_APPLICATION_CREDENTIALS, *_CREDENTIALS_FILE
        r"^SSH_AUTH_SOCK$",
        r"^(GH|CLOUDSDK|ACTIONS|DBT)_",
        r"^DATABRICKS_",   # host/token env the delegatee resolves itself
        r"^(KUBECONFIG|DOCKER_CONFIG|NETRC)$",
        r"_PROXY$",        # *_PROXY may carry userinfo credentials
        r"CONNECTION_?STRING",  # Event Hubs / Storage account strings
    )
)

_URL_USERINFO: Final = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://[^/?#\s@]+@")


def is_credential_name(name: str) -> bool:
    """True when an env var *name* is credential-shaped (case-insensitive)."""
    return any(pattern.search(name) for pattern in CREDENTIAL_PATTERNS)


def safe_env(
    source: Mapping[str, str] | None = None,
    *,
    extra: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """The environment a delegated specialist is allowed to see.

    ``source`` defaults to ``os.environ``. ``extra`` is a governed override
    channel for non-secret configuration a caller deliberately forwards —
    every entry is re-checked against the credential filter and the
    userinfo rule, so a credential can never ride in through ``extra``.
    """
    src = os.environ if source is None else source
    env = {
        key: value
        for key, value in src.items()
        if key.upper() in SAFE_ENV_ALLOWLIST
        and key.upper() not in _FORCED_ENV
        and not is_credential_name(key)
        and not _URL_USERINFO.search(value)
    }
    if extra:
        for key, value in extra.items():
            if (
                not is_credential_name(key)
                and key.upper() not in _FORCED_ENV
                and not _URL_USERINFO.search(value)
            ):
                env[key] = value
    env.update(_FORCED_ENV)
    return env
