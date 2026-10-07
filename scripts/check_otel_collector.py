"""Conferidor do job `otel-collector`: a saida do Collector contra os goldens.

O Collector so existe no CI. Este script compara o que o receiver `otlp_json_file`
exportou (`--traces`, `--metrics`, JSONL do OTLP) com `fixtures/otel/*/expected/`
-- os goldens que o proprio `projetar()` emite. A comparacao e por SPAN e por
PONTO DE METRICA, nos atributos semanticos (`gen_ai.*`, `mcp.*`,
`sparkforge_azure.*`, `error.*`, `network.*`, `service.*`, `telemetry.*`):
decoracao do collector (ex.: `log.file.name`) nao entra, mas qualquer atributo
semantico adulterado -- um `gen_ai.usage.*` trocado, um `error.type` sumido --
falha.

Uma ultima linha JSONL truncada nao derruba o conferidor: o exporter `file` pode
estar no meio da escrita e a linha "ainda nao chegou" nao e adulteracao. Linha
malformada no meio do arquivo e.

Uso:
    python scripts/check_otel_collector.py --traces traces.jsonl \
        --metrics metrics.jsonl [--goldens fixtures/otel]

Sai 0 e imprime `OK:` quando todo elemento esperado esta presente; 1 com a
lista de problemas.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GOLDENS = ROOT / "fixtures" / "otel"

SEMANTIC_PREFIXES = (
    "gen_ai.",
    "mcp.",
    "error.",
    "network.",
    "service.",
    "telemetry.",
    "sparkforge_azure.",
)


def _mesmos_atributos_semanticos(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """Igualdade so nos atributos semanticos: decoracao de pipeline nao conta."""
    def filtrar(d: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in d.items() if k.startswith(SEMANTIC_PREFIXES)}

    return filtrar(a) == filtrar(b)


def _jsonl(path: Path) -> tuple[list[dict[str, Any]], str | None]:
    """Objetos das linhas completas; `None`/motivo quando o arquivo falha."""
    if not path.is_file():
        return [], "arquivo_inexistente"
    texto = path.read_text(encoding="utf-8", errors="replace")
    if not texto.strip():
        return [], "arquivo_vazio"
    linhas = texto.splitlines()
    objetos: list[dict[str, Any]] = []
    for i, linha in enumerate(linhas):
        if not linha.strip():
            continue
        try:
            valor = json.loads(linha)
        except json.JSONDecodeError:
            if i == len(linhas) - 1:
                continue  # escrita em andamento: a linha ainda nao chegou
            return [], f"linha_{i + 1}_malformada"
        if isinstance(valor, dict):
            objetos.append(valor)
    if not objetos:
        return [], "sem_objetos_json"
    return objetos, None


def _atributos(items: Iterable[dict[str, Any]]) -> dict[str, Any]:
    saida: dict[str, Any] = {}
    for item in items or ():
        valor = item.get("value") or {}
        saida[str(item.get("key"))] = next(iter(valor.values()), None)
    return saida


def _spans(documentos: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    for doc in documentos:
        for rs in doc.get("resourceSpans") or ():
            for ss in rs.get("scopeSpans") or ():
                spans.extend(ss.get("spans") or ())
    return spans


def _pontos(documentos: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Cada data point de cada metrica, normalizado para comparacao."""
    pontos: list[dict[str, Any]] = []
    for doc in documentos:
        for rm in doc.get("resourceMetrics") or ():
            for sm in rm.get("scopeMetrics") or ():
                for metrica in sm.get("metrics") or ():
                    nome = metrica.get("name")
                    for grupo in ("histogram", "sum", "gauge"):
                        dados = metrica.get(grupo) or {}
                        for ponto in dados.get("dataPoints") or ():
                            pontos.append(
                                {
                                    "metric": nome,
                                    "attrs": _atributos(ponto.get("attributes")),
                                    "value": {
                                        k: ponto.get(k)
                                        for k in (
                                            "count",
                                            "sum",
                                            "asInt",
                                            "asDouble",
                                            "timeUnixNano",
                                            "startTimeUnixNano",
                                            "bucketCounts",
                                            "explicitBounds",
                                            "quantileValues",
                                        )
                                        if k in ponto
                                    },
                                }
                            )
    return pontos


def _faltam_spans(esperados, reais) -> list[str]:
    usados: set[int] = set()
    faltando: list[str] = []
    for esperado in esperados:
        achado = None
        for i, real in enumerate(reais):
            if i in usados:
                continue
            if (
                real.get("spanId") == esperado.get("spanId")
                and real.get("traceId") == esperado.get("traceId")
            ):
                achado = i
                break
        if achado is None:
            faltando.append(f"span {esperado.get('spanId')} ausente")
            continue
        real = reais[achado]
        esperado_attrs = _atributos(esperado.get("attributes"))
        real_attrs = _atributos(real.get("attributes"))
        if not _mesmos_atributos_semanticos(esperado_attrs, real_attrs):
            faltando.append(f"span {esperado.get('spanId')} com atributos divergentes")
            continue
        for campo in ("name", "kind", "startTimeUnixNano", "endTimeUnixNano", "status"):
            if esperado.get(campo) != real.get(campo):
                faltando.append(f"span {esperado.get('spanId')} difere em {campo}")
                break
        else:
            usados.add(achado)
    return faltando


def _faltam_pontos(esperados, reais) -> list[str]:
    faltando: list[str] = []
    chaves = [
        (p["metric"], json.dumps(p["value"], sort_keys=True, default=str)) for p in reais
    ]
    for esperado in esperados:
        chave = (esperado["metric"], json.dumps(esperado["value"], sort_keys=True, default=str))
        candidatos = [i for i, c in enumerate(chaves) if c == chave]
        if not any(
            _mesmos_atributos_semanticos(esperado["attrs"], reais[i]["attrs"])
            for i in candidatos
        ):
            faltando.append(f"metrica {esperado['metric']} sem ponto correspondente")
    return faltando


def _esperados(goldens: Path, sinal: str) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for caso in sorted(goldens.iterdir()):
        esperado = caso / "expected" / f"{sinal}.jsonl"
        if esperado.is_file():
            objetos, _ = _jsonl(esperado)
            docs.extend(objetos)
    return docs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--traces", type=Path, required=True)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--goldens", type=Path, default=GOLDENS)
    args = parser.parse_args(argv)

    problemas: list[str] = []
    reais_traces, erro = _jsonl(args.traces)
    if erro:
        problemas.append(f"traces: {erro}")
    reais_metrics, erro = _jsonl(args.metrics)
    if erro:
        problemas.append(f"metrics: {erro}")

    if not problemas:
        problemas += [
            f"traces: {p}"
            for p in _faltam_spans(_spans(_esperados(args.goldens, "traces")), _spans(reais_traces))
        ]
        problemas += [
            f"metrics: {p}"
            for p in _faltam_pontos(
                _pontos(_esperados(args.goldens, "metrics")), _pontos(reais_metrics)
            )
        ]

    if problemas:
        for problema in problemas:
            print(f"FAIL: {problema}")
        return 1
    print("OK: saida do Collector cobre todos os goldens")
    return 0


if __name__ == "__main__":
    sys.exit(main())
