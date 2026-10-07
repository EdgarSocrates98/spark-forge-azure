import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _pyproject_version() -> str:
    """Le `version = "..."` de [project]. Regex em vez de tomllib porque
    tomllib so existe em 3.11 e o CI tambem roda 3.10."""
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    assert match, "pyproject.toml sem `version = \"...\"` em [project]"
    return match.group(1)


def test_package_version_exposed():
    import sparkforge_azure

    assert sparkforge_azure.__version__ == _pyproject_version()




def test_core_imports_without_optional_extras():
    """Core must not import boto3 or the MCP SDK. Devin CLI and CI run without them."""
    code = (
        "import sys;"
        "sys.modules['boto3'] = None;"
        "sys.modules['mcp'] = None;"
        "import sparkforge_azure, sparkforge_azure.findings, sparkforge_azure.rules,"
        "sparkforge_azure.findings.models, sparkforge_azure.rules.expr,"
        "sparkforge_azure.facts, sparkforge_azure.case, sparkforge_azure.agentic,"
        "sparkforge_azure.decision, sparkforge_azure.cli.main, sparkforge_azure.mcp.tools;"
        "print('ok')"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT
    )
    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout
