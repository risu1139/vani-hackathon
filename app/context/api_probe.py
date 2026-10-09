"""Reachability probe for the seller-context APIs (production hosts, read-only calls).

The AK (JWT) is read from the VANI_AK environment variable and is never written to disk.
Prints status, latency and top-level JSON keys or error text. Full responses go to
data/api_cache/probe/ (git-ignored, may hold PII).
Usage:  VANI_AK=<ak> python app/context/api_probe.py --glid <GLID>
"""
import argparse, json, os, socket, ssl, sys, time, urllib.error, urllib.parse, urllib.request

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "data", "api_cache", "probe")
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE


def calls(g, ak):
    q = lambda d: urllib.parse.urlencode({k: v for k, v in d.items() if v is not None})
    dwh = lambda ep, body: (f"A2/A3 imdwh {ep}", "POST", f"https://imdwh.intermesh.net/api/go/{ep}",
                            json.dumps(body), "application/json")
    soa = {"glusrid": g, "modid": "MY", "AK": ak}
    return [
        ("A1 getContext (glid)", "GET", f"https://exchange.intermesh.net/go/api/globalcontext/v1/x/getContext?{q({'glid': g})}", None, None),
        dwh("cust_scorecard_api", {"in_glusr_usr_id": g, "in_rpt_type": "1"}),
        dwh("cust_wh_apiv2", {"in_glusr_usr_id": g, "in_rpt_type": "1"}),
        dwh("pns_chart_api", {"in_glusr_usr_id": g}),
        dwh("glmisccount", {"in_glusr_usr_id": g}),
        dwh("prd_mapping_api", {"in_glusr_usr_id": g}),
        dwh("gettopbarsmry", {"in_glusr_usr_id": g}),
        dwh("glusr_bl_summaryv2", {"in_glusr_usr_id": g}),
        dwh("nsdprepplus", {"in_glusr_usr_id": g}),
        dwh("getgldsrcount", {"in_glusr_usr_id": g}),
        ("A4 users/detail", "GET", f"https://users.imutils.com/wservce/users/detail/?{q(soa)}", None, None),
        ("A4 users/minidetail", "GET", f"https://users.imutils.com/wservce/users/minidetail/?{q(soa)}", None, None),
        ("A4 users/pnssetting", "GET", f"https://users.imutils.com/wservce/users/pnssetting/?{q(soa)}", None, None),
        ("A4 users/AccountManager", "GET", f"https://users.imutils.com/wservce/users/AccountManager/?{q(soa)}", None, None),
        ("A4 users/supplierrating", "GET", f"https://users.imutils.com/wservce/users/supplierrating/?{q(soa)}", None, None),
        ("A5 buyleads/seller_bl_count", "GET", f"http://leads.imutils.com/wservce/buyleads/seller_bl_count/?{q(soa)}", None, None),
        ("A5 buyleads/user_selling_mcat", "GET", f"http://leads.imutils.com/wservce/buyleads/user_selling_mcat/?{q(soa)}", None, None),
        ("A6 products/productfiltercount", "GET", f"https://users.imutils.com/wservce/products/productfiltercount/?{q(soa)}", None, None),
        ("A6 products/userlisting", "GET", f"https://seller.imutils.com/wservce/products/userlisting/?{q(soa)}", None, None),
        ("A7 bizfeed GetActivityStatus", "GET", f"https://bizfeed.imutils.com/MyActivity/GetActivityStatus?{q({'glid': g})}", None, None),
        ("A8 top_mcat prod_count", "GET", f"http://top_mcat.intermesh.net/prod_count?{q({'glid': g})}", None, None),
    ]


def summarize(body):
    try:
        o = json.loads(body)
    except Exception:
        return "non-JSON: " + " ".join(body[:160].split())
    if isinstance(o, dict):
        msg = {k: str(o[k])[:90] for k in o if k.lower() in ("message", "msg", "err_txt", "status", "status_code", "code", "error")}
        return f"keys={list(o)[:12]} {msg}"
    return f"{type(o).__name__} len={len(o)}"


def main():
    a = argparse.ArgumentParser(); a.add_argument("--glid", required=True); p = a.parse_args()
    ak = os.environ.get("VANI_AK")
    os.makedirs(OUT, exist_ok=True)
    for name, method, url, data, ctype in calls(p.glid, ak):
        host = urllib.parse.urlparse(url).hostname
        try:
            ip = socket.gethostbyname(host)
        except Exception:
            print(f"{name:34} DNS FAIL ({host})"); continue
        req = urllib.request.Request(url, data=data.encode() if data else None, method=method,
                                     headers={"Content-Type": ctype} if ctype else {})
        t = time.time()
        try:
            with urllib.request.urlopen(req, timeout=10, context=CTX) as r:
                code, body = r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            code, body = e.code, e.read().decode("utf-8", "replace")
        except Exception as e:
            print(f"{name:34} {ip:15} ERROR {type(e).__name__}: {str(e)[:90]}"); continue
        ms = int((time.time() - t) * 1000)
        fn = "".join(c if c.isalnum() else "_" for c in name) + ".txt"
        open(os.path.join(OUT, fn), "w", encoding="utf-8").write(body)
        print(f"{name:34} {ip:15} HTTP {code} {ms:5}ms {summarize(body)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8"); main()
