#!/usr/bin/env python3
"""Render the public Panera promos site (index.html) from the private CSV.

Usage: python3 render.py [path/to/promos.csv] [output-dir]

The CSV is the private source of truth and is NOT committed to the repo.
Each card shows the full linked email address, at Andrew's explicit
request (2026-11-06) — the site is public, so the addresses are visible
to anyone who visits it.

Interaction (added 2026-11-06, at Andrew's request):
- Tapping an active card slides it left to reveal two buttons:
  "Promo used" and "Doesn't work".
- Each button opens a pre-filled email to Andrew himself with a
  machine-readable subject ("PANERA USED <source_id>" or
  "PANERA BROKEN <source_id>"). A 30-minute cron (panera-used-check)
  watches Gmail for those marker emails and applies them to the CSV:
  used -> status=used, broken -> status=broken. The card is also
  hidden immediately on the device (localStorage, 6h) so the site
  feels instant while the cron confirms it.
- Used and broken promos are removed from the active grid and shown
  in their own sections below, so there is a visible record.
- The site is static (GitHub Pages, no backend), so the email is the
  report channel — the buttons cannot write to the CSV directly.
"""
import csv
import html
import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
    "~/workspace/panera_promos/promos.csv")
OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(
    os.path.abspath(__file__))

REPORT_EMAIL = "alin5647@gmail.com"


def fmt_date(iso: str) -> str:
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%b %-d, %Y")
    except ValueError:
        return iso


def active_card(r: dict) -> str:
    return (
        f"<div class=\"swipe\" data-source=\"{html.escape(r['source_id'])}\" "
        f"data-email=\"{html.escape(r['linked_email'])}\" "
        f"data-promo=\"{html.escape(r['promo'])}\">\n"
        "  <div class=\"actions\">\n"
        "    <button class=\"btn-used\" type=\"button\">Promo used</button>\n"
        "    <button class=\"btn-broken\" type=\"button\">Doesn't work</button>\n"
        "  </div>\n"
        "  <article class=\"card\">\n"
        f"    <h2>{html.escape(r['promo'])}</h2>\n"
        f"    <p class=\"expires\">Expires {fmt_date(r['expires'])}</p>\n"
        f"    <p class=\"fine\">{html.escape(r['fine_print'])}</p>\n"
        f"    <p class=\"account\">Account: {html.escape(r['linked_email'])}</p>\n"
        "  </article>\n"
        "</div>")


def record_card(r: dict, label: str) -> str:
    return (
        "<article class=\"card record\">\n"
        f"  <h2>{html.escape(r['promo'])}</h2>\n"
        f"  <p class=\"expires\">Expired {fmt_date(r['expires'])}</p>\n"
        f"  <p class=\"fine\">{html.escape(r['fine_print'])}</p>\n"
        f"  <p class=\"account\">Account: {html.escape(r['linked_email'])}"
        f" &middot; {label}</p>\n"
        "</article>")


def section(title: str, cards: list, cls: str) -> str:
    if not cards:
        return ""
    return (f"<h2 class=\"section-title\">{title}</h2>\n"
            f"<div class=\"grid {cls}\">\n" + "\n".join(cards) + "\n</div>\n")


def main() -> None:
    with open(CSV_PATH, newline="") as f:
        rows = list(csv.DictReader(f))
    active = sorted(
        [r for r in rows if r["status"] == "active"
         and r.get("wanted", "yes") == "yes"],
        key=lambda r: (r["expires"], r["promo"]))
    used = sorted(
        [r for r in rows if r["status"] == "used"],
        key=lambda r: (r["expires"], r["promo"]), reverse=True)
    broken = sorted(
        [r for r in rows if r["status"] == "broken"],
        key=lambda r: (r["expires"], r["promo"]), reverse=True)
    updated = datetime.now(ZoneInfo("America/New_York")).strftime(
        "%B %-d, %Y at %-I:%M %p ET")

    if active:
        body = (f"<p class=\"count\">{len(active)} active "
                f"{'promo' if len(active) == 1 else 'promos'}</p>\n"
                "<p class=\"hint\">Tap a card to mark it used or report "
                "it as not working.</p>\n"
                "<div class=\"grid\" id=\"active-grid\">\n"
                + "\n".join(active_card(r) for r in active)
                + "\n</div>")
    else:
        body = ("<div class=\"empty\">\n"
                "  <p>No active Panera promos right now.</p>\n"
                "  <p>New offers land here as soon as they arrive.</p>\n"
                "</div>")

    body += section("Used", [record_card(r, "Used") for r in used], "used")
    body += section("Doesn't work", [record_card(r, "Reported broken")
                                     for r in broken], "broken")

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
  .count {{ font-size: 18px; font-weight: 600; margin: 0 0 4px; }}
  .hint {{ margin: 0 0 14px; font-size: 13px; color: #888; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; }}
  .card {{ background: #fff; border: 1px solid #e5ddd2; border-radius: 12px; padding: 16px; }}
  .card h2 {{ margin: 0 0 6px; font-size: 17px; }}
  .expires {{ margin: 0 0 8px; font-weight: 700; color: #b23a00; }}
  .fine {{ margin: 0 0 10px; font-size: 14px; line-height: 1.45; color: #555; }}
  .account {{ margin: 0; font-size: 13px; color: #888; }}
  .record {{ opacity: .75; }}
  .section-title {{ margin: 28px 0 12px; font-size: 19px; }}
  .empty {{ background: #fff; border: 1px solid #e5ddd2; border-radius: 12px; padding: 28px 20px; text-align: center; }}
  .empty p:first-child {{ font-size: 19px; font-weight: 600; margin: 0 0 6px; }}
  .empty p:last-child {{ margin: 0; color: #666; }}
  .swipe {{ position: relative; overflow: hidden; border-radius: 12px; }}
  .swipe .card {{ position: relative; z-index: 1; transition: transform .25s ease; cursor: pointer; height: 100%; box-sizing: border-box; }}
  .swipe.revealed .card {{ transform: translateX(-172px); }}
  .actions {{ position: absolute; top: 0; right: 0; bottom: 0; width: 172px; display: flex; z-index: 0; }}
  .actions button {{ flex: 1; border: 0; color: #fff; font-size: 13px; font-weight: 700; line-height: 1.25; padding: 8px 6px; cursor: pointer; }}
  .btn-used {{ background: #1e7d32; }}
  .btn-broken {{ background: #b3261e; }}
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
<footer>Last updated {updated}. Each card shows the full linked email for that offer. Tapping a card reveals "Promo used" and "Doesn't work" — both send a report email that is applied within about 30 minutes.</footer>
<script>
(function () {{
  var EMAIL = {json.dumps(REPORT_EMAIL)};
  var KEY = "panera-reported";
  function loadReported() {{
    try {{ return JSON.parse(localStorage.getItem(KEY) || "{{}}"); }}
    catch (e) {{ return {{}}; }}
  }}
  function saveReported(m) {{
    try {{ localStorage.setItem(KEY, JSON.stringify(m)); }} catch (e) {{}}
  }}
  function applyReported() {{
    var m = loadReported(), now = Date.now(), changed = false;
    Object.keys(m).forEach(function (sid) {{
      if (now - (m[sid].ts || 0) > 6 * 3600 * 1000) {{ delete m[sid]; changed = true; return; }}
      var el = document.querySelector('.swipe[data-source="' + sid + '"]');
      if (el) {{ el.style.display = "none"; }}
    }});
    if (changed) saveReported(m);
  }}
  function report(swipe, action) {{
    var sid = swipe.getAttribute("data-source");
    var email = swipe.getAttribute("data-email");
    var promo = swipe.getAttribute("data-promo");
    var m = loadReported();
    m[sid] = {{ action: action, ts: Date.now() }};
    saveReported(m);
    swipe.style.display = "none";
    var subject = (action === "used" ? "PANERA USED " : "PANERA BROKEN ") + sid;
    var body = "Promo: " + promo + "\\nAccount: " + email + "\\nSource: " + sid
      + "\\nReported from the Panera promos site.";
    window.location.href = "mailto:" + EMAIL
      + "?subject=" + encodeURIComponent(subject)
      + "&body=" + encodeURIComponent(body);
  }}
  document.querySelectorAll(".swipe").forEach(function (swipe) {{
    var card = swipe.querySelector(".card");
    card.addEventListener("click", function () {{
      swipe.classList.toggle("revealed");
    }});
    swipe.querySelector(".btn-used").addEventListener("click", function (e) {{
      e.stopPropagation();
      report(swipe, "used");
    }});
    swipe.querySelector(".btn-broken").addEventListener("click", function (e) {{
      e.stopPropagation();
      report(swipe, "broken");
    }});
  }});
  applyReported();
}})();
</script>
</body>
</html>
"""
    out_path = os.path.join(OUT_DIR, "index.html")
    with open(out_path, "w") as out:
        out.write(page)
    print(f"wrote {out_path} ({len(active)} active, {len(used)} used, "
          f"{len(broken)} broken)")


if __name__ == "__main__":
    main()
