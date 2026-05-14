import time

import aiohttp

_cache: dict = {"rates": None, "updated_at": 0.0}
_TTL = 86400  # 24 hours
_URL = "https://open.er-api.com/v6/latest/KRW"


async def get_rates() -> dict[str, float]:
    if _cache["rates"] and time.time() - _cache["updated_at"] < _TTL:
        return _cache["rates"]
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(_URL, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                data = await resp.json()
                r = data.get("rates", {})
                result = {
                    "RUB": float(r.get("RUB", 0)),
                    "USD": float(r.get("USD", 0)),
                }
                _cache["rates"] = result
                _cache["updated_at"] = time.time()
                return result
    except Exception:
        return _cache["rates"] or {"RUB": 0.0, "USD": 0.0}
