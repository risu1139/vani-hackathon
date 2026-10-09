"""Offline latency/accuracy of the relay classifiers (Jev vs Sarvam LLM) on the comparison test lines (made-up).
Usage: RELAY_TOKEN=x python app/spike/midcall_clf_offline.py [sarvam_model]"""
import json, os, statistics, sys, time
os.environ.setdefault("RELAY_TOKEN", "offline")
if len(sys.argv) > 1:
    os.environ["SARVAM_CLF_MODEL"] = sys.argv[1]
import midcall_relay as R
from midcall_compare import SCEN, OUT

CASES = []
for scen, turns in SCEN.items():
    for text, lang, sig in turns:
        if sig in ("after", "after_gu"):
            continue
        CASES.append((text, "neutral" if sig == "gujarati" else sig))
CASES += [("फिर से बोलिए, आवाज़ नहीं आई", "confused"), ("पांच मिनट बाद कॉल करो, अभी कस्टमर है", "rushed"),
          ("हाँ हाँ बताइए, ऑर्डर कैसे आएंगे?", "interested"), ("भाई पहले भी बोला था मुझे नहीं चाहिए, फिर से कॉल क्यों किया?", "frustrated"),
          ("आप बॉट हो क्या? रिकॉर्डेड कॉल है?", "bot_question"), ("हाँ जी, मैं ही बोल रहा हूँ", "neutral")]
seen = set(); CASES = [c for c in CASES if not (c[0] in seen or seen.add(c[0]))]
res = {}
for name, fn in (("jev", R.clf_jev), ("sarvam:" + R.SARVAM_MODEL, R.clf_sarvam)):
    rows, lat = [], []
    for utt, exp in CASES:
        t = time.perf_counter()
        try:
            mode, scores, lang = fn(utt, "नमस्ते, मैं IndiaMART से बात कर रहा हूँ। क्या आपके पास दो मिनट हैं?")
            err = None
        except Exception as e:
            mode, scores, lang, err = None, {}, None, str(e)[:200]
        ms = round((time.perf_counter() - t) * 1000); lat.append(ms)
        rows.append({"utt": utt, "exp": exp, "got": mode, "ok": mode == exp, "ms": ms, "scores": scores, "lang": lang, "err": err})
    ok = sum(r["ok"] for r in rows)
    res[name] = {"acc": f"{ok}/{len(rows)}", "p50_ms": statistics.median(lat), "max_ms": max(lat), "rows": rows}
    print(f"{name}: {ok}/{len(rows)} p50 {statistics.median(lat)} ms max {max(lat)} ms")
    for r in rows:
        if not r["ok"]:
            print("   MISS", r["utt"][:45], "want", r["exp"], "got", r["got"], r["err"] or r["scores"] if not r["ok"] else "")
p = OUT / f"clf-offline-{time.strftime('%Y%m%d-%H%M%S')}.json"
p.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8"); print("saved", p)
