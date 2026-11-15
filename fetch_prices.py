"""Fetch closing prices from Yahoo Finance and write prices.json.
Run by the GitHub Action. Holds tickers and prices only - no amounts.
For each symbol: latest close, previous close, and closes 1 week, 1 month,
1 year ago and at the last year end (for week / month / year moves)."""
import json, time, datetime, urllib.request

TICKERS = ["CSPX.L", "CUKX.L", "III.L", "RCP.L", "SHEL.L", "SIE.DE", "SKWD", "SMT.L",
           "VALL.L", "VAPX.L", "VBK", "VERX.L", "VHT", "VJPB.L", "VUAG.L", "VUKE.L",
           "VUSA.L", "VV", "XDEW.L", "XDEX.L", "XMJP.L", "VWRL.L"]
FX = ["GBPUSD=X", "EURGBP=X"]
D = datetime.date


def back(day, months=0, days=0, years=0):
    if days:
        return day - datetime.timedelta(days=days)
    y, m = day.year - years, day.month - months
    while m < 1:
        m += 12; y -= 1
    for dd in (day.day, 30, 29, 28):
        try:
            return D(y, m, dd)
        except ValueError:
            pass


def close_on_or_before(rows, target):
    best = None
    for d, c in rows:
        if d <= target:
            best = c
        else:
            break
    return best


def chart(sym):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=13mo&interval=1d"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    r = json.load(urllib.request.urlopen(req, timeout=25))["chart"]["result"][0]
    byday = {}
    for t, c in zip(r["timestamp"], r["indicators"]["quote"][0]["close"]):
        if c is not None:  # keep the last bar for each date (Yahoo sometimes repeats today)
            byday[datetime.datetime.fromtimestamp(t, datetime.timezone.utc).date()] = c
    rows = sorted(byday.items())
    last_d, last_c = rows[-1]
    live = r["meta"].get("regularMarketPrice")
    if live and abs(live / last_c - 1) < 0.2:
        last_c = live
    prev = rows[-2][1] if len(rows) > 1 else None
    rnd = lambda v: None if v is None else round(v, 6)
    return {"cur": r["meta"].get("currency"), "date": last_d.isoformat(),
            "close": rnd(last_c), "prev": rnd(prev),
            "w": rnd(close_on_or_before(rows, back(last_d, days=7))),
            "m": rnd(close_on_or_before(rows, back(last_d, months=1))),
            "y": rnd(close_on_or_before(rows, back(last_d, years=1))),
            "ytd": rnd(close_on_or_before(rows, D(last_d.year - 1, 12, 31)))}


def main():
    out = {"updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
           "prices": {}, "fx": {}, "errors": []}
    for s in TICKERS + FX:
        try:
            (out["fx"] if s in FX else out["prices"])[s] = chart(s)
        except Exception as e:  # keep going; old prices are kept below
            out["errors"].append(f"{s}: {e}")
        time.sleep(0.4)
    try:
        old = json.load(open("prices.json"))
        for k in ("prices", "fx"):
            for s, v in old.get(k, {}).items():
                out[k].setdefault(s, v)
    except FileNotFoundError:
        pass
    json.dump(out, open("prices.json", "w"), indent=1)
    print(f"{len(out['prices'])} prices, {len(out['errors'])} errors")


if __name__ == "__main__":
    main()
