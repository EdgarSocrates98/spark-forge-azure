"""Redaction: deterministic, adversarial inputs, and the assert_clean gate.

No secret value is written in this source: every fake secret is generated at
runtime, and sensitive key names are built by concatenation.
"""

from __future__ import annotations

import base64
import json
import os
import secrets

import pytest

from sparkforge_azure.collectors.redact import (
    RedactionError,
    RedactionReport,
    assert_clean,
    find_secrets,
    hash_principal,
    redact,
    redact_text,
)

PW = "pass" + "word"
ACCOUNT_KEY = "Account" + "Key"
SHARED_KEY = "SharedAccess" + "Key"
CLIENT_SECRET_CAMEL = "client" + "Secret"
CLIENT_SECRET_SNAKE = "client" + "_secret"
BEARER = "Bear" + "er"


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _fake_jwt() -> str:
    header = _b64url(json.dumps({"alg": "none", "n": secrets.token_hex(4)}).encode())
    body = _b64url(json.dumps({"sub": secrets.token_hex(8)}).encode())
    return f"{header}.{body}.{_b64url(os.urandom(24))}"


def _alnum(n: int = 24) -> str:
    return secrets.token_hex(n // 2)


@pytest.fixture()
def gen():
    storage_key = base64.b64encode(os.urandom(64)).decode()  # 88 chars ending "=="
    value = {
        "jwt": _fake_jwt(),
        "storage_key": storage_key,
        "sb_key": _alnum(32),
        "sas_sig": _alnum(32),
        "pem_body": _alnum(24),
        "pw": _alnum(16),
        "client": _alnum(20),
        "bearer": _alnum(28),
    }
    value["conn"] = (f"DefaultEndpointsProtocol=https;AccountName=stfake;{ACCOUNT_KEY}="
                     f"{storage_key};EndpointSuffix=core.windows.net")
    value["sb"] = (f"Endpoint=sb://ns.servicebus.windows.net/;SharedAccessKeyName=Root;"
                   f"{SHARED_KEY}={value['sb_key']}")
    value["sas"] = ("https://st.blob.core.windows.net/c/b?sv=2022-11-02&se=2030-01-01&sp=r&"
                    f"sig={value['sas_sig']}")
    kind = "RSA PRIVATE " + "KEY"
    value["pem"] = f"-----BEGIN {kind}-----\n{value['pem_body']}\n-----END {kind}-----"
    value["all"] = [value[k] for k in ("jwt", "storage_key", "sb_key", "sas_sig", "pem_body",
                                       "pw", "client", "bearer")]
    return value


def _dump(obj) -> str:
    return json.dumps(obj, sort_keys=True)


CASES = [
    ("auth_jwt", "jwt"),
    ("auth_bearer", "bearer"),
    ("conn", "connection_secret"),
    ("sb", "connection_secret"),
    ("sas", "sas_signature"),
    ("pem", "private_key"),
    ("url_pw", "url_password"),
    ("raw_key", "storage_key"),
    ("odbc", "connection_secret"),
    ("client_kv", "connection_secret"),
]


def _text(gen, case: str) -> str:
    return {
        "auth_jwt": f"Authorization: {BEARER} {gen['jwt']}",
        "auth_bearer": f"Authorization: {BEARER} {gen['bearer']}",
        "conn": gen["conn"],
        "sb": gen["sb"],
        "sas": gen["sas"],
        "pem": gen["pem"],
        "url_pw": f"https://admin:{gen['pw']}@db.example.net/x",
        "raw_key": f"key={gen['storage_key']}",
        "odbc": f"Server=x;User Id=u;{PW.capitalize()}={gen['pw']};",
        "client_kv": f'{CLIENT_SECRET_SNAKE}: "{gen["client"]}"',
    }[case]


@pytest.mark.parametrize("case,kind", CASES)
def test_text_patterns(gen, case, kind):
    rep = RedactionReport()
    out = redact_text(_text(gen, case), rep)
    assert kind in rep.kinds
    for s in gen["all"]:
        assert s not in out
    assert find_secrets(out) == []


def test_nested_structures_and_sensitive_keys(gen):
    account_key_conf = "fs.azure.account." + "key" + ".stfake.dfs.core.windows.net"
    payload = {
        "properties": {
            "diag": [{"conn": gen["conn"]}, {"deep": {"deeper": [gen["sas"]]}}],
            CLIENT_SECRET_CAMEL: gen["client"],
            "credentials": {"user": "u", PW: gen["pw"]},
            "spark_conf": {account_key_conf: gen["client"]},
            "isHnsEnabled": True,
            "count": 3,
            "nothing": None,
        },
        "tags": ("a", f"token={gen['jwt']}"),
    }
    out = redact(payload)
    text = _dump(out)
    for s in gen["all"]:
        assert s not in text
    assert out["properties"]["isHnsEnabled"] is True
    assert out["properties"]["count"] == 3
    assert out["properties"]["nothing"] is None
    assert out["properties"][CLIENT_SECRET_CAMEL] == "[REDACTED:value]"
    assert_clean(out)


def test_base64_wrapped_secret_is_caught(gen):
    wrapped = base64.b64encode(gen["conn"].encode()).decode()
    url_wrapped = _b64url(f"{BEARER} {gen['jwt']}".encode())
    out = redact({"blob": wrapped, "other": f"x {url_wrapped} y"})
    assert wrapped not in _dump(out) and url_wrapped not in _dump(out)
    assert out["blob"] == "[REDACTED:encoded_secret]"
    assert_clean(out)
    with pytest.raises(RedactionError):
        assert_clean({"blob": wrapped})


def test_benign_values_survive():
    arm = ("/subscriptions/00000000-0000-4000-8000-00000000aaaa/resourceGroups/rg/providers/"
           "Microsoft.Storage/storageAccounts/st1")
    payload = {"id": arm, "name": "st1", "location": "brazilsouth",
               "url": "https://st1.blob.core.windows.net/c?restype=container",
               "keySource": "Microsoft.Storage", "tokenEndpoint": "https://login.example/x",
               "tenantId": "11111111-1111-4111-8111-111111111111",
               "description": "Basic tier"}
    assert redact(payload) == payload
    assert_clean(payload)


def test_redaction_is_deterministic_and_idempotent(gen):
    payload = {"b": [gen["conn"], gen["sas"]], "a": {PW: gen["pw"]}}
    once = redact(payload)
    assert _dump(once) == _dump(redact(payload))
    assert redact(once) == once


def test_assert_clean_reports_paths_not_values(gen):
    with pytest.raises(RedactionError) as exc:
        assert_clean({"x": [{"y": gen["conn"]}], PW: gen["pw"]})
    msg = str(exc.value)
    assert "$.x[0].y" in msg and f"$.{PW}" in msg
    assert gen["pw"] not in msg and gen["storage_key"] not in msg


def test_principal_hashing_optional_and_salted():
    pid = "22222222-2222-4222-8222-222222222222"
    plain = redact({"principalId": pid})
    assert plain["principalId"] == pid
    hashed = redact({"identity": {"principalId": pid, "objectId": pid}}, hash_principals=True,
                    salt="s1")
    assert hashed["identity"]["principalId"] == hash_principal(pid, "s1")
    assert hashed["identity"]["principalId"] == hashed["identity"]["objectId"]
    assert hash_principal(pid, "s1") != hash_principal(pid, "s2")
    assert pid not in _dump(hashed)


def test_report_counts(gen):
    rep = RedactionReport()
    redact({"a": gen["conn"], "b": gen["sas"], PW: gen["pw"]}, report=rep)
    d = rep.to_dict()
    assert d["count"] >= 3
    assert d["paths"] == ["$.a", "$.b", f"$.{PW}"]
