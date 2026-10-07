"""Synthetic transforms used by the example notebook and tests."""


def normalize_order(row: dict) -> dict:
    return {**row, "status": str(row.get("status", "")).lower()}


def silver_orders(rows: list[dict]) -> list[dict]:
    return [normalize_order(r) for r in rows if r.get("order_id")]


class OrderWriter:
    def target_path(self) -> str:
        return "abfss://silver@stlakehouse.dfs.core.windows.net/orders"
