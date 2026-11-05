# Panera Promos

A public page showing the Panera Bread promo offers currently available on my
MyPanera accounts: [alin5647.github.io/panera-promos](https://alin5647.github.io/panera-promos/)

## What it shows

Only the offers I actually want: flat $ / % discounts and freebies. No delivery
offers, no bonus points, no Sip Club, no conditional with-purchase add-ons.
Each card shows the offer, its expiry, the fine print, and a short account tag
identifying which linked email holds it.

## Privacy

No email addresses are published here. The account tags (e.g. `pan21`, `pn12`)
are just labels for matching an offer to an account in my private table.

## How it updates

`index.html` is generated daily from a private promo table by `render.py`:

```bash
python3 render.py [path/to/promos.csv] [output-dir]
```

The source CSV is not in this repo — it holds the linked email addresses and
is the private source of truth. The page refreshes whenever a new promo wave
lands or offers expire.
