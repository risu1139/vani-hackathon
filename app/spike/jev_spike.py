"""Spike 5: Jev via OpenRouter Decisions API — latency and a labelled smoke test on romanized seller turns.

Usage: python app/spike/jev_spike.py [--repeat N]
"""
import argparse
import json
import os
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import socket

import requests
import urllib3.util.connection

# OpenRouter has an IP allowlist; only our IPv4 egress (via VPN) is allowed, IPv6 is not tunnelled.
urllib3.util.connection.allowed_gai_family = lambda: socket.AF_INET

ROOT = Path(__file__).resolve().parents[2]
for line in (ROOT / ".env").read_text().splitlines():
    if "=" in line and not line.lstrip().startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

URL = "https://openrouter.ai/api/alpha/decisions"
SESSION = requests.Session()  # keep-alive: a fresh TLS handshake per call adds ~270 ms
MODEL = os.environ.get("JEV_MODEL", "typesafe/jev-1.13")

QUESTIONS = {
    "rushed": {"type": "noul",
               "instructions": "In the latest seller turn, does the seller signal they are busy or short of time, or ask to finish quickly or call later?",
               "criteria": {"true": "Time pressure, e.g. 'jaldi bolo', 'busy hoon', 'baad mein call karo', 'time nahi hai', 'meeting mein hoon', 'driving', 'seekiram sollunga' (Tamil), 'pachhi vaat karu' (Gujarati).",
                            "false": "No time pressure; polite short answers like 'haan', 'ok', 'boliye' alone are not rushed."}},
    "frustrated": {"type": "noul",
                   "instructions": "In the latest seller turn, is the seller annoyed or angry with the call or the company?",
                   "criteria": {"true": "Complaints or irritation, e.g. 'kitni baar call karoge', 'pareshan kar diya', 'faltu call', 'dimag mat khao', abuse.",
                                "false": "Neutral, polite, or a calm 'not interested'."}},
    "confused": {"type": "noul",
                 "instructions": "In the latest seller turn, does the seller say they did not understand what the agent said or why it is calling?",
                 "criteria": {"true": "e.g. 'samjha nahi', 'kya bola', 'kya matlab', 'kis cheez ka call hai', 'phir se bolo', 'puriyala' (Tamil), 'samjanu nahi' (Gujarati).",
                              "false": "Asking for more details about the offer (that is interest), or any clear reply."}},
    "bot_question": {"type": "noul",
                     "instructions": "In the latest seller turn, is the seller asking whether they are talking to a recording, a machine or an AI instead of a human?",
                     "criteria": {"true": "e.g. 'robot ho kya', 'recording hai kya', 'insaan se baat karao', 'AI hai?', 'aap bot ho'.",
                                  "false": "Asking only the agent's name or company."}},
    "interested": {"type": "noul",
                   "instructions": "In the latest seller turn, does the seller show positive interest (asks price, benefits, next steps, or agrees to a meeting)?",
                   "criteria": {"true": "e.g. 'kitna charge hai', 'kab aayenge', 'theek hai bhej do', 'details batao'.",
                                "false": "No interest shown, refusal, or only a greeting."}},
    "language": {"type": "choice",
                 "instructions": "Which language is the latest seller turn mainly in? Text is romanized.",
                 "criteria": {"hinglish": "Hindi mixed with English words", "hindi": "Mostly Hindi", "english": "Mostly English",
                              "tamil": "Tamil words like 'illa', 'sollunga', 'enna', 'puriyala'",
                              "gujarati": "Gujarati words like 'che', 'nathi', 'tame', 'kem'",
                              "unclear": "Too short or unclear to tell"}},
}

# (latest seller turn, expected labels). Hand-written smoke set; not customer data.
CASES = [
    ("Abhi busy hoon yaar, jaldi bolo kya hai", {"rushed": 1, "language": "hinglish"}),
    ("Main driving kar raha hoon, baad mein call karo", {"rushed": 1, "language": "hinglish"}),
    ("Time nahi hai abhi, short mein batao", {"rushed": 1}),
    ("Meeting mein hoon, shaam ko baat karte hain", {"rushed": 1}),
    ("Seekiram sollunga, naan busy", {"rushed": 1, "language": "tamil"}),
    ("Hu atyare busy chhu, pachhi vaat karu", {"rushed": 1, "language": "gujarati"}),
    ("Kitni baar call karoge, pareshan kar diya hai", {"frustrated": 1, "language": "hindi"}),
    ("Faltu call mat karo bhai, dimag mat khao", {"frustrated": 1}),
    ("Yeh teesri baar call aa raha hai aaj, band karo yeh sab", {"frustrated": 1}),
    ("Samajh nahi aaya, kya matlab meeting?", {"confused": 1}),
    ("Kya bola aapne? Kis cheez ka call hai yeh?", {"confused": 1}),
    ("Enna sollureenga, puriyala", {"confused": 1, "language": "tamil"}),
    ("Aap bot ho kya? Recorded call hai?", {"bot_question": 1}),
    ("Kisi insaan se baat karao, machine se nahi", {"bot_question": 1}),
    ("Are you a robot or a real person?", {"bot_question": 1, "language": "english"}),
    ("Achha, kitna charge hai iska?", {"interested": 1}),
    ("Theek hai, kal 11 baje aa jaiye office", {"interested": 1}),
    ("Details WhatsApp pe bhej do, dekhta hoon", {"interested": 1}),
    ("Tame ketla paisa leso? Mane details moklo", {"interested": 1, "language": "gujarati"}),
    ("Haan boliye", {"rushed": 0, "frustrated": 0, "confused": 0, "bot_question": 0}),
    ("Haan ji, main hi bol raha hoon", {"rushed": 0, "frustrated": 0, "confused": 0}),
    ("Aapka naam kya hai aur kaunsi company se ho?", {"bot_question": 0, "confused": 0}),
    ("Nahi chahiye, interest nahi hai, thank you", {"frustrated": 0, "interested": 0}),
    ("Already IndiaMART wale sir se baat ho gayi hai", {"frustrated": 0, "confused": 0}),
    ("Ok ok", {"rushed": 0, "frustrated": 0, "confused": 0, "interested": 0}),
    ("Yes tell me, what is this about?", {"language": "english", "frustrated": 0}),
    ("Illa, venda", {"language": "tamil"}),
    ("Mane kai samjanu nahi, shu kaam che?", {"confused": 1, "language": "gujarati"}),
    ("Abhi nahi, mahine baad call karna", {"rushed": 1}),
    ("Bhai pehle bhi bola tha mujhe nahi chahiye, phir se call kyun kiya?", {"frustrated": 1}),
]


def decide(utterance, last_agent="Namaste, IndiaMART se baat kar raha hoon. Kya do minute baat kar sakte hain?"):
    body = {"model": MODEL,
            "state": {"agent_last_line": last_agent, "seller_latest_turn": utterance},
            "questions": QUESTIONS}
    t0 = time.perf_counter()
    r = SESSION.post(URL, headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"}, json=body, timeout=30)
    ms = (time.perf_counter() - t0) * 1000
    r.raise_for_status()
    return ms, r.json()


def main(repeat):
    rows, lat = [], []
    for rep in range(repeat):
        with ThreadPoolExecutor(max_workers=4) as ex:
            results = list(ex.map(lambda c: (c, decide(c[0])), CASES))
        for (utt, exp), (ms, js) in results:
            lat.append(ms)
            if rep == 0:
                rows.append((utt, exp, js))
    # sequential latency (no concurrency) for a cleaner per-call number
    seq = [decide(CASES[i % len(CASES)][0])[0] for i in range(15)]
    agree = {k: [0, 0] for k in QUESTIONS}
    print(f"{'utterance':58} | expected -> got")
    for utt, exp, js in rows:
        a = js["answers"]
        got = {k: (round(a[k]["noul"], 2) if a[k]["type"] == "noul" else a[k]["choice"]) for k in a}
        miss = []
        for k, v in exp.items():
            g = got[k]
            ok = (g >= 0.5) == bool(v) if isinstance(v, int) else g == v
            agree[k][0] += ok; agree[k][1] += 1
            if not ok:
                miss.append(f"{k}: want {v} got {g}")
        print(f"{utt[:58]:58} | {'OK' if not miss else '; '.join(miss)}")
    print("\nPer-signal agreement (threshold 0.5):", {k: f"{a}/{n}" for k, (a, n) in agree.items() if n})
    q = statistics.quantiles(seq, n=20)
    print(f"Sequential latency ms: p50 {statistics.median(seq):.0f}  p95 {q[18]:.0f}  (n={len(seq)})")
    q2 = statistics.quantiles(lat, n=20)
    print(f"Concurrent(4) latency ms: p50 {statistics.median(lat):.0f}  p95 {q2[18]:.0f}  (n={len(lat)})")
    print("Usage example:", rows[0][2].get("usage"), "model:", rows[0][2].get("model"))
    out = ROOT / "outputs" / f"spike-jev-{time.strftime('%Y%m%d-%H%M%S')}.json"
    out.write_text(json.dumps([{"utt": u, "exp": e, "resp": j} for u, e, j in rows], ensure_ascii=False, indent=1), encoding="utf-8")
    print("Saved", out.name)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeat", type=int, default=1)
    main(ap.parse_args().repeat)
