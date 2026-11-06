#!/usr/bin/env python3
"""Render the public Panera promos site (index.html) from the private CSV.

Usage: python3 render.py [path/to/promos.csv] [output-dir]

The CSV is the private source of truth and is NOT committed to the repo.
Each card shows the full linked email address, at Andrew's explicit
request (2026-11-06) — the site is public, so the addresses are visible
to anyone who visits it.
"""
import csv
import html
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
    "~/workspace/panera_promos/promos.csv")
OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(
    os.path.abspath(__file__))


def fmt_date(iso: str) -> str:
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%b %-d, %Y")
    except ValueError:
        return iso


def main() -> None:
    with open(CSV_PATH, newline="") as f:
        rows = [r for r in csv.DictReader(f)
                if r["status"] == "active" and r.get("wanted", "yes") == "yes"]
    rows.sort(key=lambda r: (r["expires"], r["promo"]))
    updated = datetime.now(ZoneInfo("America/New_York")).strftime(
        "%B %-d, %Y at %-I:%M %p ET")

    if rows:
        cards = []
        for r in rows:
            cards.append(
                "<article class=\"card\">\n"
                f"  <h2>{html.escape(r['promo'])}</h2>\n"
                f"  <p class=\"expires\">Expires {fmt_date(r['expires'])}</p>\n"
                f"  <p class=\"fine\">{html.escape(r['fine_print'])}</p>\n"
                f"  <p class=\"account\">Account: {html.escape(r['linked_email'])}</p>\n"
                "</article>")
        body = (f"<p class=\"count\">{len(rows)} active "
                f"{'promo' if len(rows) == 1 else 'promos'}</p>\n"
                "<div class=\"grid\">\n" + "\n".join(cards) + "\n</div>")
    else:
        body = ("<div class=\"empty\">\n"
                "  <p>No active Panera promos right now.</p>\n"
                "  <p>New offers land here as soon as they arrive.</p>\n"
                "</div>")

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Panera Promos</title>
<style>
  :root {{ color-scheme: light; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 0; background: #faf7f2; color: #222; }}
  header {{ background: #004c3f; color: #fff; padding: 28px 20px 22px; }}
  header h1 {{ margin: 0 0 6px; font-size: 28px; }}
  header p {{ margin: 0; opacity: .85; }}
  main {{ max-width: 860px; margin: 0 auto; padding: 20px; }}
  .count {{ font-size: 18px; font-weight: 600; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; }}
  .card {{ background: #fff; border: 1px solid #e5ddd2; border-radius: 12px; padding: 16px; }}
  .card h2 {{ margin: 0 0 6px; font-size: 17px; }}
  .expires {{ margin: 0 0 8px; font-weight: 700; color: #b23a00; }}
  .fine {{ margin: 0 0 10px; font-size: 14px; line-height: 1.45; color: #555; }}
  .account {{ margin: 0; font-size: 13px; color: #888; }}
  .empty {{ background: #fff; border: 1px solid #e5ddd2; border-radius: 12px; padding: 28px 20px; text-align: center; }}
  .empty p:first-child {{ font-size: 19px; font-weight: 600; margin: 0 0 6px; }}
  .empty p:last-child {{ margin: 0; color: #666; }}
  footer {{ max-width: 860px; margin: 0 auto; padding: 0 20px 28px; font-size: 13px; color: #888; }}
</style>
</head>
<body>
<header>
  <h1>Panera Promos</h1>
  <p>Current offers, updated daily. Promos are one-time and tied to a MyPanera account.</p>
</header>
<main>
{body}
</main>
<footer>Last updated {updated}. Each card shows the full linked email for that offer.</footer>
</body>
</html>
"""
    out_path = os.path.join(OUT_DIR, "index.html")
    with open(out_path, "w") as out:
        out.write(page)
    print(f"wrote {out_path} ({len(rows)} active promos)")


if __name__ == "__main__":
    main()
