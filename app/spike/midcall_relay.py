"""Laptop relay for mid-call classification (O2c / O5 / O6-via-relay). Test only.

Runs on this laptop behind a temporary `cloudflared` quick tunnel. Sarvam code/API tools send ONLY the seller
utterance (or @Call Transcript) plus a random shared token; every model key stays on the laptop.

  POST /decide?clf=jev|sarvam   {"utt": "...", "last_agent": "..."}          -> {"mode","directive","scores","ms"}
  POST /decide_transcript?clf=  {"transcript": <@Call Transcript>, ...}      -> same (last user turn is classified)
Header: X-Relay-Token: <token> on every request. Every request is appended to outputs/midcall_tests/relay-log-<date>.jsonl
(utterance text is made-up test speech only).

Usage: RELAY_TOKEN=... python app/spike/midcall_relay.py [port]
"""
import json
import os
import re
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import requests

import jev_spike  # loads .env, IPv4-only session for the OpenRouter allowlist
from midcall_compare import DIRECTIVES, PRIORITY, QUESTIONS

ROOT = jev_spike.ROOT
LOG = ROOT / "outputs" / "midcall_tests" / f"relay-log-{time.strftime('%Y%m%d')}.jsonl"
TOKEN = os.environ["RELAY_TOKEN"]
SARVAM_MODEL = os.environ.get("SARVAM_CLF_MODEL", "sarvam-105b")
SARVAM_SESSION = requests.Session()
LABELS = ["neutral", "rushed", "frustrated", "confused", "interested", "opt_out", "bot_question"]
SARVAM_PROMPT = (
    "You label one seller turn from an Indian B2B sales call. Reply with exactly one label and nothing else, from: "
    + ", ".join(LABELS) + ". rushed = busy / call later / hurry. frustrated = irritated, complains about calls, threatens to hang up. "
    "confused = did not understand what was said. interested = asks how it works, price, details, or agrees to meet; a bare 'ok ok' is neutral. "
    "opt_out = asks not to be called again / remove number. bot_question = asks if this is a bot or recording. Otherwise neutral. "
    "If several apply, prefer: opt_out > frustrated > rushed > confused > bot_question > interested.")


def clf_jev(utt, last_agent):
    body = {"model": jev_spike.MODEL, "state": {"agent_last_line": (last_agent or "")[-300:], "seller_latest_turn": utt},
            "questions": QUESTIONS}
    r = jev_spike.SESSION.post(jev_spike.URL, json=body, timeout=5,
                               headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"})
    r.raise_for_status()
    a = r.json()["answers"]
    scores = {k: round(v["noul"], 2) for k, v in a.items() if v.get("type") == "noul"}
    mode = next((k for k in PRIORITY if scores.get(k, 0) >= 0.5), "neutral")
    return mode, scores, a.get("language", {}).get("choice")


def clf_sarvam(utt, last_agent):
    r = SARVAM_SESSION.post("https://api.sarvam.ai/v1/chat/completions", timeout=5,
                            headers={"api-subscription-key": os.environ["SARVAM_API_KEY"]},
                            json={"model": SARVAM_MODEL, "temperature": 0, "max_tokens": 20,
                                  "reasoning_effort": None,  # explicit null = no reasoning (461 ms vs 2-4 s)
                                  "messages": [{"role": "system", "content": SARVAM_PROMPT},
                                               {"role": "user", "content": f"Agent said: {last_agent or '-'}\nSeller turn: {utt}\nLabel:"}]})
    r.raise_for_status()
    txt = (r.json()["choices"][0]["message"].get("content") or "").strip().lower()
    txt = re.sub(r"<think>.*?</think>", "", txt, flags=re.S).strip()
    mode = next((l for l in LABELS if re.search(rf"\b{l}\b", txt)), "neutral")
    return mode, {"raw": txt[:80]}, None


def last_user_turn(transcript):
    """@Call Transcript arrives as text or JSON; take the last user/seller line."""
    if isinstance(transcript, list):
        users = [t.get("content") or t.get("text") or "" for t in transcript if str(t.get("role", "")).lower() in ("user", "seller")]
        return users[-1] if users else "", ""
    s = str(transcript or "")
    try:
        return last_user_turn(json.loads(s))
    except Exception:
        pass
    lines = [l.strip() for l in s.splitlines() if l.strip()]
    users = [re.sub(r"^(user|seller|customer)\s*[:\-]\s*", "", l, flags=re.I) for l in lines if re.match(r"^(user|seller|customer)\s*[:\-]", l, re.I)]
    agents = [re.sub(r"^(assistant|agent|bot)\s*[:\-]\s*", "", l, flags=re.I) for l in lines if re.match(r"^(assistant|agent|bot)\s*[:\-]", l, re.I)]
    return (users[-1] if users else (lines[-1] if lines else "")), (agents[-1] if agents else "")


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        self._send(200, {"ok": True})

    def do_POST(self):
        t_in = time.time()
        u = urlparse(self.path)
        if self.headers.get("X-Relay-Token") != TOKEN:
            return self._send(401, {"error": "bad token"})
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        except Exception:
            body = {}
        clf = (parse_qs(u.query).get("clf") or ["jev"])[0]
        if u.path == "/decide_transcript":
            utt, last_agent = last_user_turn(body.get("transcript"))
        else:
            utt, last_agent = body.get("utt", ""), body.get("last_agent", "")
        t0 = time.perf_counter()
        try:
            mode, scores, lang = (clf_sarvam if clf == "sarvam" else clf_jev)(utt, last_agent)
            err = None
        except Exception as e:
            mode, scores, lang, err = "neutral", {}, None, f"{type(e).__name__}: {str(e)[:150]}"
        ms = round((time.perf_counter() - t0) * 1000)
        out = {"mode": mode, "directive": DIRECTIVES.get(mode, DIRECTIVES["neutral"]), "scores": scores, "lang": lang,
               "ms": ms, "err": err}
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"t": round(t_in, 3), "path": u.path, "clf": clf, "utt": utt[:120], "iid": body.get("interaction_id"),
                                "transcript_chars": len(str(body.get("transcript") or "")),
                                "transcript_tail": str(body.get("transcript") or "")[-160:], **out}, ensure_ascii=False) + "\n")
        self._send(200, out)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8787
    print(f"relay on 127.0.0.1:{port}, log {LOG}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
