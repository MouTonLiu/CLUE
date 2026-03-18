"""
Deribit ETH Options Data Fetcher

Fetches ETH options data from Deribit public API every 10 minutes.
Filters:
  - Expiry: from now until end of the next day
  - Strike: within ±3% of current ETH index price
"""

import json
import time
import logging
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

BASE_URL = "https://www.deribit.com/api/v2/public"
CURRENCY = "ETH"
FETCH_INTERVAL = 600  # 10 minutes
STRIKE_RANGE_PCT = 0.03  # 3%
OUTPUT_DIR = Path("options_data")


def api_get(method: str, params: dict | None = None) -> dict:
    """Call Deribit public API."""
    url = f"{BASE_URL}/{method}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    if "error" in data:
        raise RuntimeError(f"API error: {data['error']}")
    return data["result"]


def get_index_price() -> float:
    """Get current ETH index price."""
    result = api_get("get_index_price", {"index_name": "eth_usd"})
    price = result["index_price"]
    log.info(f"Current ETH index price: ${price:.2f}")
    return price


def get_instruments() -> list[dict]:
    """Get all active ETH option instruments."""
    return api_get("get_instruments", {"currency": CURRENCY, "kind": "option"})


def filter_instruments(instruments: list[dict], index_price: float) -> list[dict]:
    """Filter instruments by expiry and strike range."""
    now = datetime.now(timezone.utc)
    # End of the next day (UTC)
    tomorrow_end = (now + timedelta(days=1)).replace(
        hour=23, minute=59, second=59, microsecond=0
    )
    max_expiry_ms = int(tomorrow_end.timestamp() * 1000)

    strike_low = index_price * (1 - STRIKE_RANGE_PCT)
    strike_high = index_price * (1 + STRIKE_RANGE_PCT)

    filtered = []
    for inst in instruments:
        expiry_ms = inst["expiration_timestamp"]
        strike = inst["strike"]
        # Expiry must be between now and end of next day
        if expiry_ms < now.timestamp() * 1000:
            continue
        if expiry_ms > max_expiry_ms:
            continue
        # Strike outside ±3% of current price (above +3% or below -3%)
        if strike >= strike_high or strike <= strike_low:
            filtered.append(inst)

    log.info(
        f"Filtered {len(filtered)} instruments "
        f"(strike <=${strike_low:.0f} or >=${strike_high:.0f}, "
        f"expiry before {tomorrow_end.strftime('%Y-%m-%d %H:%M UTC')})"
    )
    return filtered


def get_order_book(instrument_name: str) -> dict:
    """Get order book / ticker data for an instrument."""
    return api_get("get_order_book", {"instrument_name": instrument_name})


def fetch_options_data():
    """Main fetch cycle: get index price, filter instruments, fetch prices."""
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d_%H%M%S")

    index_price = get_index_price()
    instruments = get_instruments()
    filtered = filter_instruments(instruments, index_price)

    if not filtered:
        log.warning("No instruments match the filter criteria.")
        return

    records = []
    for inst in filtered:
        name = inst["instrument_name"]
        try:
            book = get_order_book(name)
            record = {
                "instrument_name": name,
                "strike": inst["strike"],
                "option_type": inst["option_type"],
                "expiration": datetime.fromtimestamp(
                    inst["expiration_timestamp"] / 1000, tz=timezone.utc
                ).isoformat(),
                "mark_price": book.get("mark_price"),
                "mark_iv": book.get("mark_iv"),
                "best_bid_price": book.get("best_bid_price"),
                "best_bid_amount": book.get("best_bid_amount"),
                "best_ask_price": book.get("best_ask_price"),
                "best_ask_amount": book.get("best_ask_amount"),
                "last_price": book.get("last_price"),
                "open_interest": book.get("open_interest"),
                "volume_24h": book.get("stats", {}).get("volume"),
                "underlying_price": book.get("underlying_price"),
                "greeks": book.get("greeks"),
                "timestamp": now.isoformat(),
                "index_price": index_price,
            }
            records.append(record)
        except Exception as e:
            log.error(f"Failed to fetch {name}: {e}")

    # Save to file
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = OUTPUT_DIR / f"eth_options_{timestamp}.json"
    with open(output_file, "w") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    # Print summary
    calls = [r for r in records if r["option_type"] == "call"]
    puts = [r for r in records if r["option_type"] == "put"]
    log.info(
        f"Saved {len(records)} records ({len(calls)} calls, {len(puts)} puts) "
        f"to {output_file}"
    )

    # Print table
    print(f"\n{'─' * 90}")
    print(
        f"{'Instrument':<30} {'Type':<5} {'Strike':>8} "
        f"{'Mark Price':>10} {'IV%':>8} {'Bid':>10} {'Ask':>10}"
    )
    print(f"{'─' * 90}")
    for r in sorted(records, key=lambda x: (x["strike"], x["option_type"])):
        mark = r["mark_price"] or 0
        iv = r["mark_iv"] or 0
        bid = r["best_bid_price"] or 0
        ask = r["best_ask_price"] or 0
        # Convert BTC-denominated prices to USD
        usd_mark = mark * index_price if mark < 1 else mark
        usd_bid = bid * index_price if bid < 1 else bid
        usd_ask = ask * index_price if ask < 1 else ask
        print(
            f"{r['instrument_name']:<30} {r['option_type']:<5} "
            f"${r['strike']:>7.0f} "
            f"${usd_mark:>9.2f} {iv:>7.1f}% "
            f"${usd_bid:>9.2f} ${usd_ask:>9.2f}"
        )
    print(f"{'─' * 90}\n")


def main():
    log.info(
        f"Starting Deribit ETH options fetcher "
        f"(interval={FETCH_INTERVAL}s, strike_range=±{STRIKE_RANGE_PCT*100:.0f}%)"
    )
    while True:
        try:
            fetch_options_data()
        except Exception as e:
            log.error(f"Fetch cycle failed: {e}")
        log.info(f"Next fetch in {FETCH_INTERVAL // 60} minutes...")
        time.sleep(FETCH_INTERVAL)


if __name__ == "__main__":
    main()
