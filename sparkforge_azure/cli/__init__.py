"""CLI ``sparkforge-azure``.

``CliError`` lives in the package, not ``cli.main``: under
``python -m sparkforge_azure.cli.main`` the module is imported twice (as
``__main__`` and under its canonical name), which would make ``except CliError``
miss errors raised via the canonical import.  One class, one home.
"""


class CliError(Exception):
    """Refused input: exit 2 with a JSON error document."""
