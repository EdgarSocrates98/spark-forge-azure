"""Testes do span de contexto: o que o SparkForge poe na janela.

Span de tool tem BYTE. Token de provider e do host, e custo em dolar exige uma
fonte de preco -- os dois ficam vazios aqui, e vazio significa "nao se aplica",
nao "deu zero".
"""
from __future__ import annotations

import sqlite3

import pytest

from sparkforge_azure.observability.store import SQLiteTraceStore
from sparkforge_azure.observability.tracer import AgentOpsTracker, TraceSpan


class TestOsCamposNovos:
    def test_a_tool_span_carries_bytes_and_the_formula(self):
        span = TraceSpan(
            span_id="span_1",
            run_id="run_1",
            parent_span_id=None,
            name="sparkforge_analyze_pyspark",
            component_type="tool",
            start_time=0.0,
            payload_bytes=1234,
            payload_basis='len(json.dumps(resultado, ensure_ascii=False).encode("utf-8"))',
        )

        assert span.payload_bytes == 1234
        assert "json.dumps" in span.payload_basis
        assert span.to_dict()["payload_bytes"] == 1234

    def test_the_new_fields_default_to_absent_not_zero(self):
        """`detail_level` e `item_count` vazios dizem "a tool nao declarou",
        e nao "veio vazio"."""
        span = TraceSpan(
            span_id="span_1",
            run_id="run_1",
            parent_span_id=None,
            name="sparkforge_case_get",
            component_type="tool",
            start_time=0.0,
        )

        assert span.detail_level == ""
        assert span.item_count is None
        assert span.outcome == "ok"


class TestCustoExigeFonte:
    def test_cost_without_a_basis_is_refused(self):
        """Custo sem fonte e o numero inventado que o subprojeto E recusou."""
        tracker = AgentOpsTracker()
        trace = tracker.start_trace("t")
        span = tracker.start_span(trace, "modelo", "model")

        with pytest.raises(ValueError, match="cost_basis"):
            tracker.end_span(span, estimated_cost_usd=0.05)

    def test_cost_with_a_named_basis_is_accepted(self):
        tracker = AgentOpsTracker()
        trace = tracker.start_trace("t")
        span = tracker.start_span(trace, "modelo", "model")

        tracker.end_span(
            span, estimated_cost_usd=0.05, cost_basis="TIER_PRICING:tier_3"
        )

        assert span.estimated_cost_usd == 0.05
        assert span.cost_basis == "TIER_PRICING:tier_3"

    def test_zero_cost_needs_no_basis(self):
        """Zero nao afirma preco nenhum, entao nao precisa de fonte."""
        tracker = AgentOpsTracker()
        trace = tracker.start_trace("t")
        span = tracker.start_span(trace, "tool", "tool")

        tracker.end_span(span)

        assert span.estimated_cost_usd == 0.0
        assert span.cost_basis == ""


class TestMigracaoDeBancoAntigo:
    def test_save_trace_nao_quebra_num_traces_db_criado_antes_desta_task(self, tmp_path):
        """Reproduz o achado do revisor: `CREATE TABLE IF NOT EXISTS` nao
        altera tabela que ja existe, entao um `traces.db` gravado com o
        schema anterior (sem as seis colunas novas) fazia `save_trace`
        quebrar com `OperationalError: table spans has no column named
        payload_bytes`."""
        db_path = tmp_path / "traces.db"

        # Schema de ANTES desta task -- sem as seis colunas novas.
        with sqlite3.connect(db_path) as conn:
            conn.execute("""
                CREATE TABLE traces (
                    run_id TEXT PRIMARY KEY,
                    task_description TEXT,
                    start_time REAL,
                    end_time REAL,
                    profile TEXT,
                    status TEXT,
                    total_tokens INTEGER,
                    total_cost_usd REAL
                )
            """)
            conn.execute("""
                CREATE TABLE spans (
                    span_id TEXT PRIMARY KEY,
                    run_id TEXT,
                    parent_span_id TEXT,
                    name TEXT,
                    component_type TEXT,
                    start_time REAL,
                    end_time REAL,
                    duration_seconds REAL,
                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    cached_tokens INTEGER,
                    estimated_cost_usd REAL,
                    status TEXT,
                    metadata_json TEXT,
                    FOREIGN KEY(run_id) REFERENCES traces(run_id)
                )
            """)
            conn.commit()

        # Abrir o store sobre esse banco antigo deve migrar em silencio.
        store = SQLiteTraceStore(db_path=db_path)

        tracker = AgentOpsTracker()
        trace = tracker.start_trace("t")
        span = tracker.start_span(trace, "sparkforge_case_get", "tool")
        span.payload_bytes = 42
        tracker.end_span(span)
        tracker.finish_trace(trace)

        store.save_trace(trace)  # nao pode levantar OperationalError

        retrieved = store.get_trace(trace.run_id)
        assert retrieved is not None
        assert retrieved["spans"][0]["payload_bytes"] == 42

    def test_pragma_table_info_de_tabela_inexistente_e_o_caminho_do_banco_novo(self, tmp_path):
        """Trava o caminho que a checagem por `PRAGMA` precisa acertar sem
        engolir excecao nenhuma: tabela que ainda nao existe devolve lista
        vazia de `PRAGMA table_info`, e essa lista vazia -- nao um erro --
        e o sinal de "nada a migrar" que deixa a criacao do zero para o
        `CREATE TABLE IF NOT EXISTS` seguinte."""
        db_path = tmp_path / "novo.db"
        with sqlite3.connect(db_path) as conn:
            assert conn.execute("PRAGMA table_info(spans)").fetchall() == []

        store = SQLiteTraceStore(db_path=db_path)  # nao pode levantar

        with sqlite3.connect(store.db_path) as conn:
            colunas = {linha[1] for linha in conn.execute("PRAGMA table_info(spans)").fetchall()}
        assert "payload_bytes" in colunas
        assert "cost_basis" in colunas








class TestPayloadNaoSerializavelNaoDerrubaAChamada:
    """Achado do revisor: `payload_bytes` sem `default=str` pode levantar
    `TypeError` sobre um `resultado` com valor nao serializavel -- e esse
    `TypeError` tem que morrer dentro do ledger, nunca escapar para quem
    chamou `record()`."""

    def test_um_resultado_nao_serializavel_nao_derruba_o_record_nem_grava_span(
        self, tmp_path
    ):
        import datetime
        import time

        from sparkforge_azure.observability.context_ledger import ContextLedger

        ledger = ContextLedger(db_path=tmp_path / "traces.db", run_id="run_teste")

        ledger.record(
            name="sparkforge_qualquer",
            resultado={"quando": datetime.datetime.now()},
            detail_level="",
            outcome="ok",
            start_time=time.time(),
        )  # nao pode levantar TypeError

        assert ledger.spans_of("run_teste") == []




class TestBufferEFlush:
    """A decisao de desenho: `record()` so acumula em memoria: `flush()` grava
    tudo de uma vez, numa transacao so, e e quem realmente toca o disco."""

    def test_spans_of_enxerga_span_ainda_no_buffer(self, tmp_path):
        import time

        from sparkforge_azure.observability.context_ledger import ContextLedger

        ledger = ContextLedger(db_path=tmp_path / "traces.db", run_id="run_teste")
        ledger.record(
            name="sparkforge_case_get",
            resultado={"ok": True},
            detail_level="",
            outcome="ok",
            start_time=time.time(),
        )

        # `record()` nao grava -- so `flush()` toca disco.
        assert not (tmp_path / "traces.db").exists()
        assert len(ledger.spans_of("run_teste")) == 1

    def test_apos_flush_final_a_linha_de_traces_tem_o_start_time_do_primeiro_span(
        self, tmp_path
    ):
        import sqlite3
        import time

        from sparkforge_azure.observability.context_ledger import ContextLedger

        ledger = ContextLedger(db_path=tmp_path / "traces.db", run_id="run_teste")
        primeiro = time.time()
        ledger.record(
            name="a",
            resultado={"ok": True},
            detail_level="",
            outcome="ok",
            start_time=primeiro,
        )
        time.sleep(0.01)
        ledger.record(
            name="b",
            resultado={"ok": True},
            detail_level="",
            outcome="ok",
            start_time=time.time(),
        )

        ledger.flush(final=True)

        with sqlite3.connect(tmp_path / "traces.db") as conn:
            linha = conn.execute(
                "SELECT start_time, end_time, status FROM traces WHERE run_id = ?",
                ("run_teste",),
            ).fetchone()

        assert linha is not None
        start_time, end_time, status = linha
        assert start_time == primeiro
        assert end_time is not None
        assert status == "completed"
        assert len(ledger.spans_of("run_teste")) == 2

    def test_dois_flush_no_mesmo_processo_mantem_o_start_time_do_primeiro_span(
        self, tmp_path
    ):
        """Achado do revisor: `flush("a") -> flush() -> record("b") ->
        flush()` deixava a linha de `traces` com o `start_time` do span
        `"b"`, porque cada `flush()` usava o inicio do PROPRIO lote. Agora
        `_run_start` e fixado uma vez, no primeiro `record()`, e sobrevive a
        quantos `flush()` vierem depois."""
        import sqlite3
        import time

        from sparkforge_azure.observability.context_ledger import ContextLedger

        ledger = ContextLedger(db_path=tmp_path / "traces.db", run_id="run_teste")

        primeiro = time.time()
        ledger.record(
            name="a", resultado={"ok": True}, detail_level="", outcome="ok",
            start_time=primeiro,
        )
        ledger.flush()

        time.sleep(0.01)
        ledger.record(
            name="b", resultado={"ok": True}, detail_level="", outcome="ok",
            start_time=time.time(),
        )
        ledger.flush()

        with sqlite3.connect(tmp_path / "traces.db") as conn:
            (start_time,) = conn.execute(
                "SELECT start_time FROM traces WHERE run_id = ?", ("run_teste",)
            ).fetchone()

        assert start_time == primeiro
        assert len(ledger.spans_of("run_teste")) == 2

    def test_flush_intermediario_grava_running_e_o_final_grava_completed(
        self, tmp_path
    ):
        import sqlite3
        import time

        from sparkforge_azure.observability.context_ledger import ContextLedger

        ledger = ContextLedger(db_path=tmp_path / "traces.db", run_id="run_teste")

        ledger.record(
            name="a", resultado={"ok": True}, detail_level="", outcome="ok",
            start_time=time.time(),
        )
        ledger.flush()  # checkpoint intermediario -- final=False por default

        with sqlite3.connect(tmp_path / "traces.db") as conn:
            (status,) = conn.execute(
                "SELECT status FROM traces WHERE run_id = ?", ("run_teste",)
            ).fetchone()
        assert status == "running"

        ledger.record(
            name="b", resultado={"ok": True}, detail_level="", outcome="ok",
            start_time=time.time(),
        )
        ledger.flush(final=True)  # o atexit chama assim

        with sqlite3.connect(tmp_path / "traces.db") as conn:
            (status,) = conn.execute(
                "SELECT status FROM traces WHERE run_id = ?", ("run_teste",)
            ).fetchone()
        assert status == "completed"

    def test_db_path_como_str_funciona(self, tmp_path):
        """Achado do revisor: `SQLiteTraceStore.__init__` fazia
        `db_path.parent.mkdir(...)` sem normalizar para `Path`. Passando
        `str`, isso levantava `AttributeError` dentro do `except Exception`
        de `flush()` -- e como o buffer ja tinha sido esvaziado antes do
        `try` (na versao antiga), TODOS os spans do processo sumiam de uma
        vez em silencio."""
        import sqlite3
        import time

        from sparkforge_azure.observability.context_ledger import ContextLedger

        ledger = ContextLedger(db_path=str(tmp_path / "traces.db"), run_id="run_teste")
        ledger.record(
            name="a", resultado={"ok": True}, detail_level="", outcome="ok",
            start_time=time.time(),
        )

        ledger.flush(final=True)  # nao pode levantar, nao pode perder o span

        with sqlite3.connect(tmp_path / "traces.db") as conn:
            linhas = conn.execute(
                "SELECT span_id FROM spans WHERE run_id = ?", ("run_teste",)
            ).fetchall()
        assert len(linhas) == 1

    def test_escrita_que_falha_nao_esvazia_o_buffer(self, tmp_path, monkeypatch):
        """O buffer so pode esvaziar DEPOIS da escrita dar certo. Forcando
        `save_trace` a falhar, o span tem que continuar disponivel para o
        proximo `flush()` tentar de novo -- nunca sumir numa excecao
        engolida."""
        import sqlite3
        import time

        from sparkforge_azure.observability.context_ledger import ContextLedger
        from sparkforge_azure.observability.store import SQLiteTraceStore

        def _save_trace_que_falha(self, trace):
            raise sqlite3.OperationalError("disco cheio (simulado)")

        monkeypatch.setattr(SQLiteTraceStore, "save_trace", _save_trace_que_falha)

        ledger = ContextLedger(db_path=tmp_path / "traces.db", run_id="run_teste")
        ledger.record(
            name="a", resultado={"ok": True}, detail_level="", outcome="ok",
            start_time=time.time(),
        )

        ledger.flush()  # a escrita falha, e nao pode levantar aqui

        # o span continua no buffer -- `spans_of` ainda o enxerga.
        assert len(ledger.spans_of("run_teste")) == 1




class TestIdaEVoltaEntreInstancias:
    """O caso real do CLI: um processo grava e sai, outro processo le. Achado
    do revisor: `spans_of()` so consultava o disco quando `self._store` ja
    tinha sido materializado -- e isso so acontecia dentro de `flush()`. Uma
    instancia NOVA, que nunca escreveu nada, tinha `_store is None` para
    sempre e devolvia `[]` sem nunca consultar o SQLite -- mesmo com o banco
    cheio."""

    def test_um_ledger_novo_no_mesmo_db_path_enxerga_o_que_o_outro_gravou(
        self, tmp_path
    ):
        import time

        from sparkforge_azure.observability.context_ledger import ContextLedger

        db_path = tmp_path / "traces.db"

        ledger_de_escrita = ContextLedger(db_path=db_path, run_id="run_teste")
        ledger_de_escrita.record(
            name="sparkforge_case_get",
            resultado={"ok": True},
            detail_level="",
            outcome="ok",
            start_time=time.time(),
        )
        ledger_de_escrita.flush(final=True)

        # instancia NOVA, que nunca chamou `record()` nem `flush()` --
        # `self._store` comeca `None`, do jeito que comecaria num processo B
        # que so le.
        ledger_de_leitura = ContextLedger(db_path=db_path, run_id="run_teste")

        spans = ledger_de_leitura.spans_of("run_teste")

        assert len(spans) == 1
        assert spans[0]["name"] == "sparkforge_case_get"

    def test_um_ledger_novo_apontando_para_disco_vazio_ainda_devolve_lista_vazia(
        self, tmp_path
    ):
        """A materializacao preguicosa do store nao pode fazer `spans_of`
        inventar dado: consultar um `run_id` que nunca foi gravado continua
        devolvendo `[]`, so que agora por TER CONSULTADO o disco, e nao por
        ter pulado a consulta."""
        from sparkforge_azure.observability.context_ledger import ContextLedger

        ledger = ContextLedger(db_path=tmp_path / "traces.db", run_id="run_teste")

        assert ledger.spans_of("run_nunca_gravado") == []


