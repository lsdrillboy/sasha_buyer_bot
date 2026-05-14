from __future__ import annotations

import json
from pathlib import Path

_rates: dict[str, int] = {}


def _load() -> None:
    global _rates
    path = Path(__file__).parent.parent / "data" / "shipping_rates.json"
    with open(path, encoding="utf-8") as f:
        _rates = json.load(f)


def calculate(weight_kg: float) -> tuple[str, int] | None:
    """Return (rate_key, price_in_krw) for the first tariff >= weight_kg."""
    if not _rates:
        _load()
    for k in sorted(_rates, key=float):
        if float(k) >= weight_kg - 1e-9:
            return k, _rates[k]
    return None


def all_rates() -> dict[str, int]:
    if not _rates:
        _load()
    return dict(sorted(_rates.items(), key=lambda x: float(x[0])))
