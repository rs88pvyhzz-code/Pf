"""Fetch latest closing prices from Yahoo Finance and write prices.json.
Run by the GitHub Action on weekdays. Holds tickers only - no amounts."""
import json, time, datetime, urllib.request

TICKERS = ["CSPX.L", "CUKX.L", "III.L", "RCP.L", "SHEL.L", "SIE.DE", "SKWD", "SMT.L",
           "VALL.L", "VAPX.L", "VBK", "VERX.L", "VHT", "VJPB.L", "VUAG.L", "VUKE.L",
           "VUSA.L", "VV", "XDEW.L", "XDEX.L", "XMJP.L", "VWRL.L"]
FX = ["GBPUSD=X", "EURGBP=X"]

def chart(sym):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=1mo&interval=1d"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    d = json.load(urllib.request.urlopen(req, timeout=20))["chart"]["result"][0]
    rows = [(t, c) for t, c in zip(d["timestamp"], d["indicators"]["quote"][0]["close"]) if c is not None]
    (t1, c1), (t0, c0) = rows[-1], rows[-2]
    return {"cur": d["meta"].get("currency"), "close": round(c1, 6), "prev": round(c0, 6),
            "date": datetime.datetime.fromtimestamp(t1, datetime.timezone.utc).date().isoformat()}

def main():
    out = {"updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
           "prices": {}, "fx": {}, "errors": []}
    for s in TICKERS + FX:
        try:
            (out["fx"] if s in FX else out["prices"])[s] = chart(s)
        except Exception as e:  # keep going; the app falls back to the last good price
            out["errors"].append(f"{s}: {e}")
        time.sleep(0.4)
    try:  # keep previous prices for anything that failed today
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
