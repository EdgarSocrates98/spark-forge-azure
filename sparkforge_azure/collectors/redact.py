"""Deterministic redaction for collector payloads (section 174).

Pipeline position: Azure API -> raw artifact -> **redaction** -> facts.
``redact`` returns a new object; ``assert_clean`` is the gate run before
anything is written to disk or returned to a caller.

Covered: JWTs, bearer headers, connection strings (``AccountKey=``,
``SharedAccessKey=``, ``SharedAccessSignature``, ``Password=``), SAS query
tokens (``sig=``), client secrets, PEM private keys, URL userinfo, Azure
storage account keys (88-char base64), values under sensitive key names, and
base64-wrapped copies of any of the above.  Optionally principal object ids
are replaced by a salted hash (stable within a run/salt).

Replacement tokens are fixed strings (``[REDACTED:<kind>]``), never a digest
of the secret.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


class RedactionError(ValueError):
    """Secret-like content survived redaction.  Message lists paths only."""


def token(kind: str) -> str:
    return f"[REDACTED:{kind}]"


_KV_SECRET = re.compile(
    r"(?i)\b(AccountKey|SharedAccessKey|SharedAccessSignature|"
    r"Password|Pwd|ClientSecret|client_secret|ApiKey|api_key|access_token|refresh_token|"
    r"AccessKey|SecretKey)(\s*[=:]\s*)(\"?)([^;&\s\"',}]+)"
)
_SAS = re.compile(r"(?i)([?&](?:sig|signature)=)([^&\s\"'#]+)")
_JWT = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}")
_BEARER = re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]{12,}")
_PEM = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S
)
_URL_USERINFO = re.compile(r"(?i)\b([a-z][a-z0-9+.-]*://[^/\s:@]+):([^@/\s]+)@")
_STORAGE_KEY = re.compile(r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{86}==(?![A-Za-z0-9+/=])")
_B64_CANDIDATE = re.compile(r"(?<![A-Za-z0-9+/_-])[A-Za-z0-9+/_-]{24,}={0,2}(?![A-Za-z0-9+/=_-])")

# Matched against the key with "-", "_", "." and spaces removed, lowercased.
SENSITIVE_KEY = re.compile(
    r"(password|passwd|pwd|secret|token|connectionstring|accountkey|accesskey|apikey|"
    r"primarykey|secondarykey|sasurl|credential|privatekey|signature|authorization)"
)
# Sensitive-looking names that hold configuration, not secret material.
SAFE_KEYS = frozenset(
    {
        "tokenendpoint", "keysource", "keyvaulturi", "keyvaultproperties", "secretspermissions",
        "allowsharedkeyaccess", "credentialtype",
        "disablelocalauth", "accesstier", "tokenlifetime", "keytype", "keyname",
    }
)
PRINCIPAL_KEYS = frozenset(
    {"principalid", "objectid", "oid", "clientid", "principal_id", "object_id", "client_id"}
)


@dataclass
class RedactionReport:
    count: int = 0
    kinds: dict[str, int] = field(default_factory=dict)
    paths: list[str] = field(default_factory=list)

    def hit(self, kind: str, path: str) -> None:
        self.count += 1
        self.kinds[kind] = self.kinds.get(kind, 0) + 1
        if path not in self.paths:
            self.paths.append(path)

    def to_dict(self) -> dict[str, Any]:
        return {"count": self.count, "kinds": dict(sorted(self.kinds.items())),
                "paths": sorted(self.paths)}


def _decoded_secret(candidate: str) -> bool:
    """True when a base64/base64url blob decodes to text holding a secret."""

    raw = candidate.rstrip("=")
    for alphabet in ("std", "url"):
        padded = raw + "=" * (-len(raw) % 4)
        try:
            data = (base64.urlsafe_b64decode(padded) if alphabet == "url"
                    else base64.b64decode(padded, validate=True))
        except (binascii.Error, ValueError):
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        if not text.isprintable() and "\n" not in text:
            continue
        if _scan_text(text):
            return True
    return False


def _scan_text(text: str) -> list[str]:
    found = []
    if _PEM.search(text):
        found.append("private_key")
    if _JWT.search(text):
        found.append("jwt")
    if _BEARER.search(text):
        found.append("bearer")
    for m in _KV_SECRET.finditer(text):
        if not m.group(4).startswith("[REDACTED"):
            found.append("connection_secret")
            break
    for m in _SAS.finditer(text):
        if not m.group(2).startswith("[REDACTED") and not m.group(2).startswith("%5BREDACTED"):
            found.append("sas_signature")
            break
    m = _URL_USERINFO.search(text)
    if m and not m.group(2).startswith("[REDACTED"):
        found.append("url_password")
    if _STORAGE_KEY.search(text):
        found.append("storage_key")
    return found


def redact_text(text: str, report: RedactionReport | None = None, path: str = "$") -> str:
    rep = report if report is not None else RedactionReport()
    out = text

    def sub(pattern: re.Pattern[str], kind: str, repl: Any) -> None:
        nonlocal out

        def _r(m: re.Match[str]) -> str:
            rep.hit(kind, path)
            return repl(m) if callable(repl) else repl

        out = pattern.sub(_r, out)

    sub(_PEM, "private_key", token("private_key"))
    sub(_JWT, "jwt", token("jwt"))
    sub(_BEARER, "bearer", lambda m: f"{m.group(1)} {token('bearer')}")
    sub(_URL_USERINFO, "url_password", lambda m: f"{m.group(1)}:{token('password')}@")
    sub(_KV_SECRET, "connection_secret",
        lambda m: f"{m.group(1)}{m.group(2)}{m.group(3)}{token('secret')}")
    sub(_SAS, "sas_signature", lambda m: f"{m.group(1)}{token('sas')}")
    sub(_STORAGE_KEY, "storage_key", token("storage_key"))

    def _b64(m: re.Match[str]) -> str:
        value = m.group(0)
        if value.startswith("[REDACTED") or not _decoded_secret(value):
            return value
        rep.hit("encoded_secret", path)
        return token("encoded_secret")

    out = _B64_CANDIDATE.sub(_b64, out)
    return out


def _is_sensitive_key(key: str) -> bool:
    norm = re.sub(r"[-_. ]", "", key).lower()
    if norm in SAFE_KEYS:
        return False
    return bool(SENSITIVE_KEY.search(norm))


def hash_principal(value: str, salt: str) -> str:
    digest = hashlib.sha256(f"{salt}:{value.lower()}".encode()).hexdigest()
    return f"principal:{digest[:16]}"


def redact(
    obj: Any,
    *,
    hash_principals: bool = False,
    salt: str = "sparkforge-azure",
    report: RedactionReport | None = None,
    _path: str = "$",
    _sensitive: bool = False,
) -> Any:
    """Return a redacted deep copy of ``obj`` (dict/list/tuple/str/scalars)."""

    rep = report if report is not None else RedactionReport()
    if isinstance(obj, Mapping):
        out: dict[str, Any] = {}
        for key in sorted(obj, key=str):
            value = obj[key]
            skey = str(key)
            child = f"{_path}.{skey}"
            sensitive = _sensitive or _is_sensitive_key(skey)
            if (
                hash_principals
                and skey.lower() in PRINCIPAL_KEYS
                and isinstance(value, str)
                and value
            ):
                rep.hit("principal_id", child)
                out[skey] = hash_principal(value, salt)
                continue
            out[skey] = redact(value, hash_principals=hash_principals, salt=salt, report=rep,
                               _path=child, _sensitive=sensitive)
        return out
    if isinstance(obj, (list, tuple)):
        return [
            redact(v, hash_principals=hash_principals, salt=salt, report=rep,
                   _path=f"{_path}[{i}]", _sensitive=_sensitive)
            for i, v in enumerate(obj)
        ]
    if isinstance(obj, str):
        if _sensitive and obj and not obj.startswith("[REDACTED"):
            rep.hit("sensitive_key", _path)
            return token("value")
        return redact_text(obj, rep, _path)
    if isinstance(obj, bytes):
        return redact(obj.decode("utf-8", errors="replace"), hash_principals=hash_principals,
                      salt=salt, report=rep, _path=_path, _sensitive=_sensitive)
    return obj


def find_secrets(obj: Any, _path: str = "$", _sensitive: bool = False) -> list[str]:
    """Paths (never values) of content that still looks secret."""

    hits: list[str] = []
    if isinstance(obj, Mapping):
        for key in sorted(obj, key=str):
            skey = str(key)
            hits += find_secrets(obj[key], f"{_path}.{skey}",
                                 _sensitive or _is_sensitive_key(skey))
            if _scan_text(skey):
                hits.append(f"{_path}.<key>")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            hits += find_secrets(v, f"{_path}[{i}]", _sensitive)
    elif isinstance(obj, str):
        if _sensitive and obj and not obj.startswith("[REDACTED"):
            hits.append(_path)
        elif _scan_text(obj):
            hits.append(_path)
        else:
            for m in _B64_CANDIDATE.finditer(obj):
                if _decoded_secret(m.group(0)):
                    hits.append(_path)
                    break
    return hits


def assert_clean(obj: Any) -> None:
    hits = find_secrets(obj)
    if hits:
        shown = ", ".join(sorted(set(hits))[:10])
        raise RedactionError(f"secret-like content at {len(set(hits))} path(s): {shown}")


__all__ = [
    "RedactionError",
    "RedactionReport",
    "assert_clean",
    "find_secrets",
    "hash_principal",
    "redact",
    "redact_text",
    "token",
]
