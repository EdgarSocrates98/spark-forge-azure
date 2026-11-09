from sparkforge_azure.context.obsidian import build_obsidian_diagnostic


def test_azure_projection_preserves_freshness_and_redacts_identity_secrets():
    note = build_obsidian_diagnostic(
        title="Fabric access",
        summary="Identity permissions require review.",
        workspace="analytics",
        vault_id="team-vault",
        freshness="stale",
        identity={"client_id": "app-1", "client_secret": "do-not-write"},
        source_refs=["resource-graph://subscription/resource"],
    )
    assert note["schema"] == "theforge/ObsidianNoteRef/v1"
    assert note["version"] == "v1"
    assert "do-not-write" not in note["content"]
    assert "stale" in note["content"]
