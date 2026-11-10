from sparkforge_azure.context.obsidian import build_obsidian_diagnostic, to_obsidian_note_ref


def test_azure_projection_preserves_freshness_and_redacts_identity_secrets():
    note = build_obsidian_diagnostic(
        title="Fabric access",
        summary="Identity permissions require review.",
        workspace="analytics",
        vault_id="team-vault",
        freshness="stale",
        identity={"client_id": "app-1", "client_secret": "do-not-write"},
        source_refs=["resource-graph://subscription/resource"],
        templates=["password=do-not-write-text"],
    )
    assert note["schema"] == "theforge/ObsidianNoteDraft/v1"
    ref = to_obsidian_note_ref(note)
    assert ref["schema"] == "theforge/ObsidianNoteRef/v1"
    assert "content" not in ref
    assert note["version"] == "v1"
    assert "do-not-write" not in note["content"]
    assert "stale" in note["content"]


def test_azure_projection_redacts_secrets_in_title_and_summary():
    note = build_obsidian_diagnostic(
        title="Token=do-not-write",
        summary="password=do-not-write-summary",
        workspace="analytics",
        vault_id="team-vault",
    )
    assert "do-not-write" not in note["content"]
    assert "[REDACTED]" in note["content"]
