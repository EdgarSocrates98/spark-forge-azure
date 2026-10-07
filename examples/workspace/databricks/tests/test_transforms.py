from lakehouse.transforms import normalize_order


def test_normalize_order():
    assert normalize_order({"status": "OPEN"})["status"] == "open"
