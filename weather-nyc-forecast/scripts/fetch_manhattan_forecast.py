#!/usr/bin/env python3
"""Generate a composite Manhattan 10-day forecast from several providers."""

import argparse
import datetime
import logging
import os
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional

import pytz
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

NY_LAT = 40.7831
NY_LON = -73.9712
NY_LOCATION = "Manhattan, New York, NY"
NY_TZ = pytz.timezone("America/New_York")
DEFAULT_OUTPUT = Path("./forecasts/manhattan-weather-forecast.md")
GOOGLE_URL = "https://www.google.com/search"
VISUAL_CROSSING_URL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{}"

HEADERS = {
    "User-Agent": os.environ.get(
        "GOOGLE_USER_AGENT",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/116.0.0.0 Safari/537.36",
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def safe_mean(values: List[float]) -> Optional[float]:
    cleaned = [v for v in values if v is not None]
    if not cleaned:
        return None
    return round(mean(cleaned), 1)


def safe_get(session: requests.Session, url: str, **kwargs: Any) -> Optional[requests.Response]:
    try:
        resp = session.get(url, timeout=20, **kwargs)
        resp.raise_for_status()
        return resp
    except requests.RequestException as exc:
        logging.warning("Request failed for %s: %s", url, exc)
        return None


def parse_temp_value(text: str) -> Optional[float]:
    match = re.search(r"-?\d+", text)
    if not match:
        return None
    return float(match.group())


def fetch_google_forecast(session: requests.Session, start_date: datetime.date) -> List[Dict[str, Any]]:
    cookies = {}
    consent = os.environ.get("GOOGLE_CONSENT_COOKIE")
    if consent:
        cookies["CONSENT"] = consent

    params = {
        "q": "Manhattan NYC 10 day weather",
        "hl": "en",
        "gl": "us",
        "pws": "0",
    }
    resp = safe_get(session, GOOGLE_URL, params=params, headers=HEADERS, cookies=cookies)
    if not resp:
        logging.info("Google weather fetch failed or was blocked.")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    container = soup.find("div", id="wob_dp")
    if not container:
        logging.info("Google weather container missing; check consent or locale.")
        return []

    cards = container.select(".wob_df")
    samples = []
    for idx, card in enumerate(cards[:10]):
        date = start_date + datetime.timedelta(days=idx)
        temps = [span.get_text(strip=True) for span in card.select("span.wob_t")]
        high = parse_temp_value(temps[0]) if temps else None
        low = parse_temp_value(temps[-1]) if len(temps) > 1 else None
        icon = card.select_one("img")
        summary = icon["alt"] if icon and icon.has_attr("alt") else None
        detail = card.get("aria-label") or summary
        samples.append(
            {
                "date": date,
                "source": "Google Weather",
                "summary": summary,
                "details": detail,
                "high": high,
                "low": low,
                "pop": None,
                "humidity": None,
            }
        )
    if not samples:
        logging.info("No Google weather cards found.")
    return samples


def fetch_openweather_forecast(session: requests.Session) -> List[Dict[str, Any]]:
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    if not api_key:
        logging.info("OPENWEATHER_API_KEY is unset; skipping OpenWeather.")
        return []

    params = {
        "lat": NY_LAT,
        "lon": NY_LON,
        "exclude": "current,minutely,hourly,alerts",
        "units": "imperial",
        "appid": api_key,
    }
    resp = safe_get(session, "https://api.openweathermap.org/data/2.5/onecall", params=params)
    if not resp:
        return []

    payload = resp.json()
    samples = []
    for daily in payload.get("daily", [])[:10]:
        date = datetime.datetime.fromtimestamp(daily["dt"], NY_TZ).date()
        weather = daily.get("weather")
        description = weather[0]["description"].capitalize() if weather else None
        pop = daily.get("pop")
        samples.append(
            {
                "date": date,
                "source": "OpenWeather",
                "summary": description,
                "details": description,
                "high": daily.get("temp", {}).get("max"),
                "low": daily.get("temp", {}).get("min"),
                "pop": round(pop * 100) if pop is not None else None,
                "humidity": daily.get("humidity"),
            }
        )
    return samples


def fetch_weatherapi_forecast(session: requests.Session) -> List[Dict[str, Any]]:
    api_key = os.environ.get("WEATHERAPI_KEY")
    if not api_key:
        logging.info("WEATHERAPI_KEY missing; skipping WeatherAPI.")
        return []

    params = {
        "key": api_key,
        "q": NY_LOCATION,
        "days": 10,
        "aqi": "no",
        "alerts": "no",
    }
    resp = safe_get(session, "https://api.weatherapi.com/v1/forecast.json", params=params)
    if not resp:
        return []

    payload = resp.json()
    samples = []
    for day in payload.get("forecast", {}).get("forecastday", []):
        date = datetime.datetime.fromisoformat(day["date"]).date()
        day_entry = day.get("day", {})
        condition = day_entry.get("condition", {})
        summary = condition.get("text")
        samples.append(
            {
                "date": date,
                "source": "WeatherAPI",
                "summary": summary,
                "details": summary,
                "high": day_entry.get("maxtemp_f"),
                "low": day_entry.get("mintemp_f"),
                "pop": round(day_entry.get("daily_chance_of_rain", 0)),
                "humidity": day_entry.get("avghumidity"),
            }
        )
    return samples


def fetch_visualcrossing_forecast(session: requests.Session) -> List[Dict[str, Any]]:
    api_key = os.environ.get("VISUALCROSSING_API_KEY")
    if not api_key:
        return []

    url = VISUAL_CROSSING_URL.format(quote_plus(NY_LOCATION))
    params = {
        "unitGroup": "us",
        "include": "days",
        "contentType": "json",
        "key": api_key,
        "forecastDays": 10,
    }
    resp = safe_get(session, url, params=params)
    if not resp:
        return []

    payload = resp.json()
    samples = []
    for day in payload.get("days", [])[:10]:
        date = datetime.datetime.fromisoformat(day["datetime"]).date()
        samples.append(
            {
                "date": date,
                "source": "Visual Crossing",
                "summary": day.get("conditions"),
                "details": day.get("description") or day.get("conditions"),
                "high": day.get("tempmax"),
                "low": day.get("tempmin"),
                "pop": round(day.get("precipprob", 0)),
                "humidity": day.get("humidity"),
            }
        )
    return samples


def aggregate_samples(samples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped = defaultdict(list)
    for sample in samples:
        grouped[sample["date"]].append(sample)

    aggregated = []
    for date in sorted(grouped):
        entries = grouped[date]
        highs = [e["high"] for e in entries if e.get("high") is not None]
        lows = [e["low"] for e in entries if e.get("low") is not None]
        pops = [e["pop"] for e in entries if e.get("pop") is not None]
        hums = [e["humidity"] for e in entries if e.get("humidity") is not None]
        aggregated.append(
            {
                "date": date,
                "sources": entries,
                "high": safe_mean(highs),
                "low": safe_mean(lows),
                "pop": safe_mean(pops),
                "humidity": safe_mean(hums),
            }
        )
    return aggregated


def render_markdown(aggregated: List[Dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = []
    lines.append("# Manhattan (New York City) 10-Day Composite Forecast")
    lines.append(f"*Generated on {datetime.datetime.now(NY_TZ).strftime('%Y-%m-%d %H:%M %Z')}*")
    lines.append("")
    lines.append("Every row blends every available source (Google, OpenWeather, WeatherAPI, Visual Crossing)." )
    lines.append("")
    lines.append("| Date | High (℉) | Low (℉) | Precip (%) | Sources | Summary |")
    lines.append("| --- | --- | --- | --- | --- | --- |")

    for entry in aggregated:
        date_str = entry["date"].strftime("%a %b %d")
        high = entry["high"] if entry["high"] is not None else "—"
        low = entry["low"] if entry["low"] is not None else "—"
        pop = f"{entry['pop']}%" if entry.get("pop") is not None else "—"
        source_list = ", ".join(sorted({sample["source"] for sample in entry["sources"]}))
        summary = ", ".join(
            sorted({sample.get("summary") or sample.get("details") or "" for sample in entry["sources"] if sample.get("summary") or sample.get("details")})
        )
        lines.append(f"| {date_str} | {high} | {low} | {pop} | {source_list} | {summary} |")

    lines.append("")
    lines.append("---")
    lines.append("")

    for entry in aggregated:
        header = entry["date"].strftime("### %A, %B %d")
        lines.append(header)
        lines.append("")
        if entry['high'] is not None and entry['low'] is not None:
            pop_display = f"{entry['pop']}%" if entry.get("pop") is not None else "—"
            humidity_display = f"{entry['humidity']}%" if entry.get("humidity") is not None else "—"
            lines.append(
                f"- **Aggregate:** High {entry['high']}℉, Low {entry['low']}℉, Rain chance {pop_display}, humidity ~{humidity_display}"
            )
        else:
            lines.append("- **Aggregate:** not enough numeric data to compute averages.")
        lines.append("")
        for sample in entry["sources"]:
            descriptor = sample.get("summary") or sample.get("details") or "forecast"
            components = []
            if sample.get("high") is not None and sample.get("low") is not None:
                components.append(f"{sample['high']}°/{sample['low']}°")
            if sample.get("pop") is not None:
                components.append(f"pop {sample['pop']}%")
            if sample.get("humidity") is not None:
                components.append(f"humidity {sample['humidity']}%")
            detail = " — ".join(components) if components else ""
            lines.append(f"  - **{sample['source']}**: {descriptor}{' | ' + detail if detail else ''}")
        lines.append("")

    with output_path.open("w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    logging.info("Forecast written to %s", output_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aggregate a 10-day Manhattan forecast from multiple APIs",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Markdown path for the compiled forecast",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce console logging",
    )
    args = parser.parse_args()

    level = logging.WARNING if args.quiet else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")

    session = requests.Session()
    today = datetime.datetime.now(NY_TZ).date()

    samples: List[Dict[str, Any]] = []
    samples.extend(fetch_google_forecast(session, today))
    samples.extend(fetch_openweather_forecast(session))
    samples.extend(fetch_weatherapi_forecast(session))
    samples.extend(fetch_visualcrossing_forecast(session))

    if not samples:
        logging.warning("No forecast samples collected from any source.")

    aggregated = aggregate_samples(samples)
    if not aggregated:
        logging.error("No aggregated data to render. Exiting.")
        return

    render_markdown(aggregated, args.output)


if __name__ == "__main__":
    main()
