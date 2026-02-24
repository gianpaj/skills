---
name: weather-nyc-forecast
description: Composite 10-day Manhattan weather report that scrapes the Google Weather card, calls OpenWeather, WeatherAPI, and optionally Visual Crossing, then writes a single markdown summary. Use when you need a multi-source picture of Manhattan/NYC weather and want the report generated automatically on a schedule (every 6h, cron, or a runner job).
---

# Weather NYC Forecast

## Overview
- Collects the Google Weather card, OpenWeather One Call, WeatherAPI forecast, and (if you supply it) Visual Crossing.
- Blends highs, lows, rain chances, and humidity to build a markdown table + per-day narrative.
- Designed to produce a reusable `forecasts/manhattan-weather-forecast.md` that you can push into dashboards, Telegram, or a status page.

## Quick start
1. Install runtime dependencies (inside the environment that will run the cron job):
   ```bash
   pip install requests beautifulsoup4 pytz
   ```
2. Export the API keys:
   ```bash
   export OPENWEATHER_API_KEY=...
   export WEATHERAPI_KEY=...
   export VISUALCROSSING_API_KEY=...  # optional but gives better 10-day coverage
   export GOOGLE_CONSENT_COOKIE=YES+1  # optional, allows scraping if Google redirects to consent
   ```
3. Run the script manually to verify:
   ```bash
   cd /home/gianpaj/github/openclaw
   python skills/weather-nyc-forecast/scripts/fetch_manhattan_forecast.py --output forecasts/manhattan-weather-forecast.md
   ```
   The file is created with a table plus per-day details; existing files are overwritten so the latest 10 days are always in one place.

## Scheduling (every 6 hours)
Use cron or your orchestration tool to run the script every six hours. Example cron entry:
```
0 */6 * * * cd /home/gianpaj/github/openclaw && /usr/bin/python skills/weather-nyc-forecast/scripts/fetch_manhattan_forecast.py --output /home/gianpaj/github/openclaw/forecasts/manhattan-weather-forecast.md >> /home/gianpaj/github/openclaw/logs/weather-nyc.log 2>&1
```
If you prefer systemd timers or a runner (GitHub Actions, CI, cron runner), schedule the same command on a 6-hour cadence and point `--output` to the canonical markdown path.

## Output and consumption
- The markdown file includes a header, summary table, and detailed bullet list per day.
- Use the table for quick ingestion (Slack/Telegram summary) and the per-day section for publishing long-form announcements.
- When integrating with other automation, read the table header to confirm the file was updated within the last 6 hours.

## Key variables
| Environment variable | Purpose | Required? |
| -------------------- | ------- | --------- |
| `OPENWEATHER_API_KEY` | OpenWeather One Call v3 credentials | ✅ |
| `WEATHERAPI_KEY` | WeatherAPI 10-day forecast access | ✅ |
| `VISUALCROSSING_API_KEY` | Optional cross-check for day-by-day conditions | ⚪️ |
| `GOOGLE_CONSENT_COOKIE` | Set to `YES+1` if Google redirects to consent; allows scraping the weather card | ⚪️ |
| `GOOGLE_USER_AGENT` | Override the UA string the scraper sends | ⚪️ |

## Troubleshooting
- Google often returns the consent gate (`/ml?continue=...`). If you continuously see `Google weather fetch failed`, set `GOOGLE_CONSENT_COOKIE=YES+1` (or copy the real consent cookie from the browser) and rerun.
- Missing API keys will skip each provider but the script still tries to aggregate whatever data is available.
- Logs are emitted at INFO level by default but you can pass `--quiet` to suppress them in the cron job.

## Script reference
- `scripts/fetch_manhattan_forecast.py`: fetches from every provider, normalizes temperatures to °F, averages highs/lows/pop/humidity, and writes `forecasts/manhattan-weather-forecast.md`. Read it if you want to add another provider, change formatting, or send the markdown to Slack/Telegram after generation.
