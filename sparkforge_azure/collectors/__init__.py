"""Read-only Azure collectors (layer L6, sections 173-179).

Pipeline: Azure API or offline export -> raw (memory) -> redaction ->
``assert_clean`` -> facts -> Graphfy live nodes.  Every collector class exposes
only ``collect(...)``, which performs GET/list/query operations.  Importing this
package never imports an Azure or Databricks SDK; live paths import lazily and
raise ``CollectorUnavailable`` when the optional extra is missing.
"""

from __future__ import annotations

from sparkforge_azure.collectors.base import (
    CollectorInputError,
    CollectorResult,
    CollectorUnavailable,
)
from sparkforge_azure.collectors.redact import (
    RedactionError,
    RedactionReport,
    assert_clean,
    redact,
)

__all__ = [
    "CollectorInputError",
    "CollectorResult",
    "CollectorUnavailable",
    "RedactionError",
    "RedactionReport",
    "assert_clean",
    "redact",
]
