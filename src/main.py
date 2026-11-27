from pathlib import Path
import csv
import json
from analytics import align_series
from analytics import index_by_date
from analytics import (calculate_period_return,calculate_relative_performance,calculate_base_100,)
from analytics import (
    align_series,
    calculate_base_100,
    calculate_period_return,
    calculate_relative_performance,
)
from providers.yahoo_provider import fetch_yahoo_prices

YAHOO_SYMBOLS = {
    "AAPL": "AAPL",
    "SP500": "^GSPC",
}

YAHOO_PERIOD = "1mo"
YAHOO_INTERVAL = "1d"
DATA_DIR = Path("data/sample")

# These starter values mirror config/settings.yml.
# settings.yml is a human-readable configuration contract in the CORE.
# Parsing YAML is optional and is not required by the 18-hour lab sequence.
LOOKBACK_LABEL = "1 month"
INTERVAL_LABEL = "Daily"


def load_instruments():
    with open(DATA_DIR / "instruments.json", encoding="utf-8") as file:
        return json.load(file)


def load_prices():
    with open(DATA_DIR / "prices.csv", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def filter_prices(prices, ticker):
    return [row for row in prices if row["ticker"] == ticker]

def get_first_close(prices):
    """
    Return the initial close price of a price series as a float.
    """
    if not prices:
        return 0.0
    return float(prices[0]["close"])

def get_last_close(prices):
    """
    Return the final close price of a price series as a float.
    """
    if not prices:
        return 0.0
    return float(prices[-1]["close"])

def display_market_summary(asset, prices, show_currency=True):
    """
    Display a standardized market summary for any instrument or benchmark.
    
    Args:
        asset (dict): Metadata dictionary (containing 'ticker', 'name', 'currency').
        prices (list): Filtered observation dictionaries.
        show_currency (bool): Whether to append the currency code to prices.
    """
    first_close = get_first_close(prices)
    last_close = get_last_close(prices)
    currency_suffix = f" {asset.get('currency', '')}" if show_currency else ""

    print(f"{asset['ticker']} - {asset['name']}")
    print(f"Observations : {len(prices)}")
    print(f"First close  : {first_close:.2f}{currency_suffix}")
    print(f"Last close   : {last_close:.2f}{currency_suffix}")

def normalize_price_row(row):
    return {
        "date": row["date"],
        "ticker": row["ticker"],
        "open": float(row["open"]),
        "high": float(row["high"]),
        "low": float(row["low"]),
        "close": float(row["close"]),
        "volume": int(row["volume"]),
    }


def fetch_remote_series(canonical_ticker):
    return fetch_yahoo_prices(
        symbol=YAHOO_SYMBOLS[canonical_ticker],
        canonical_ticker=canonical_ticker,
        period=YAHOO_PERIOD,
        interval=YAHOO_INTERVAL,
    )


def validate_alignment(aligned_instrument, aligned_benchmark):
    if not aligned_instrument:
        raise ValueError("Aligned instrument series is empty: no common dates.")
    if not aligned_benchmark:
        raise ValueError("Aligned benchmark series is empty: no common dates.")
    if len(aligned_instrument) != len(aligned_benchmark):
        raise ValueError("Aligned series do not have the same length.")

    for instrument_row, benchmark_row in zip(aligned_instrument, aligned_benchmark):
        if instrument_row["date"] != benchmark_row["date"]:
            raise ValueError(
                f"Misaligned dates: {instrument_row['date']} vs {benchmark_row['date']}"
            )


def main():
    instruments = load_instruments()

    instrument = instruments["instrument"]
    benchmark = instruments["benchmark"]

    instrument_prices = fetch_remote_series(instrument["ticker"])
    benchmark_prices = fetch_remote_series(benchmark["ticker"])

    print("=== MarketPulse ===")
    print()
    print(f"Period: {LOOKBACK_LABEL}")
    print(f"Interval: {INTERVAL_LABEL}")
    print()

    print("Instrument")
    display_market_summary(instrument, instrument_prices, show_currency=True)
    print()

    print("Benchmark")
    display_market_summary(benchmark, benchmark_prices, show_currency=False)

    aligned_instrument, aligned_benchmark = align_series(
        instrument_prices,
        benchmark_prices,
    )
    validate_alignment(aligned_instrument, aligned_benchmark)

    instrument_return = calculate_period_return(aligned_instrument)
    benchmark_return = calculate_period_return(aligned_benchmark)

    relative_performance = calculate_relative_performance(
        instrument_return,
        benchmark_return,
    )
    instrument_base_100 = calculate_base_100(aligned_instrument)
    benchmark_base_100 = calculate_base_100(aligned_benchmark)

    print()
    print(f"Instrument return : {instrument_return:+.2f}%")
    print(f"Benchmark return  : {benchmark_return:+.2f}%")
    print(f"Relative performance : {relative_performance:+.2f} percentage points")

    print()
    print("Base 100")
    print(f"{instrument['ticker']:<5} : {instrument_base_100[0]['value']:.2f} -> {instrument_base_100[-1]['value']:.2f}")
    print(f"{benchmark['ticker']:<5} : {benchmark_base_100[0]['value']:.2f} -> {benchmark_base_100[-1]['value']:.2f}")


if __name__ == "__main__":
    main()