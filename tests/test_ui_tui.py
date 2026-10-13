"""TUI/menu contract tests — vendored ui.* surface."""

import pytest


def test_menu_well_formed():
    """Every _MENU item is a (label, argv|None) pair — no bare strings."""
    from sparkforge_azure.ui import home
    for item in home._MENU:
        assert isinstance(item, tuple) and len(item) == 2, item
        label, argv = item
        assert isinstance(label, str) and label
        assert argv is None or argv == "__wizard__" or isinstance(argv, list)


def test_menu_argvs_parse_in_real_parser():
    """Every menu argv must parse in the real CLI parser — the menu is a
    shell over the real surface, and a broken path fails at select time."""
    from sparkforge_azure.cli.main import build_parser
    from sparkforge_azure.ui import home

    parser = build_parser()
    broken = []
    for label, argv in home._MENU:
        if argv is None or argv == "__wizard__":
            continue
        try:
            parser.parse_args(list(argv))
        except SystemExit:
            broken.append((label, argv))
    assert not broken, f"menu argvs the real parser rejects: {broken}"


def test_tui_entries_real():
    from sparkforge_azure.ui import tui
    entries = tui.entries()
    assert len(entries) >= 3
    assert any("wizard" in e.label for e in entries)


def test_tui_renders_non_tty_ctx():
    from sparkforge_azure.ui import tui
    from sparkforge_azure.ui.app import ForgeApp
    from sparkforge_azure.ui.kit import UIContext
    from sparkforge_azure.ui.screen import Buffer
    ctx = UIContext(interactive=False, color=False, unicode=False,
                    width=80, height=24, ansi=False)
    app = ForgeApp(ctx, forge_id="x", title="cc", entries=tui.entries())
    buf = Buffer(ctx, 80, 24)
    app.render(buf)
    assert "menu" in chr(10).join(buf.render())


def test_home_requires_tty():
    from sparkforge_azure.ui import home
    from sparkforge_azure.ui.kit import NonInteractive, UIContext
    ctx = UIContext(interactive=False, color=False, unicode=False, width=80)
    with pytest.raises(NonInteractive):
        home.run_home(ctx=ctx)
