"""Signal server, spike version.

Spike 2/4: log every `read_seller_signal` tool call from the Sarvam agent (arrival time,
payload shape, transcript format) and return a neutral persona. Jev comes in later.
Run: uvicorn main:app --host 0.0.0.0 --port 8000
"""
import json
import os
import time
import unicodedata
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request

LOG = Path(os.environ.get("SIGNAL_LOG", "calls.jsonl"))
TOKEN = os.environ.get("SIGNAL_TOKEN", "")

app = FastAPI()


def check(token):
    if TOKEN and token != TOKEN:
        raise HTTPException(status_code=401, detail="bad token")


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/read_seller_signal")
async def read_seller_signal(request: Request, x_signal_token: str = Header(default="")):
    check(x_signal_token)
    t0 = time.time()
    raw = await request.body()
    try:
        body = json.loads(raw or b"{}")
    except json.JSONDecodeError:
        body = {"_raw": raw.decode("utf-8", "replace")}
    entry = {"ts": t0, "headers": {k: v for k, v in request.headers.items() if k.lower() not in ("authorization", "x-signal-token")},
             "query": dict(request.query_params), "body": body}
    mode = classify_stub(str(body.get("seller_utterance", "")))
    entry["mode"] = mode
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    directive = f"{PLAN['text']} | Right now: {DIRECTIVES[mode]}" if PLAN["text"] else DIRECTIVES[mode]
    return {"seller_mode": mode, "persona_directive": directive, "server_ms": round((time.time() - t0) * 1000, 1)}


# Plan spike: the active call's conversation plan, prefixed to every directive so the per-turn
# tool response does not overwrite it. One call at a time (spike only; real design keys by call).
PLAN = {"text": ""}


@app.post("/plan")
async def set_plan(request: Request, x_signal_token: str = Header(default="")):
    check(x_signal_token)
    PLAN["text"] = (await request.json()).get("plan", "")
    return {"ok": True, "chars": len(PLAN["text"])}


# Keyword stand-in for Jev (spike 3 only): proves a returned directive changes the next reply.
# Sarvam's ASR hands the tool Devanagari for Hindi/Hinglish, so cues cover both scripts.
STUB = [
    ("rushed", ("busy", "jaldi", "time nahi", "baad me", "abhi nahi", "driving", "meeting me",
                "बिज़ी", "बिजी", "जल्दी", "टाइम नहीं", "बाद में", "अभी नहीं", "ड्राइव", "मीटिंग में")),
    ("frustrated", ("kitni baar", "baar baar", "pareshan", "mat karo", "band karo", "disturb", "faltu",
                    "कितनी बार", "बार बार", "परेशान", "मत करो", "बंद करो", "फालतू", "फ़ालतू")),
    ("confused", ("samajh nahi", "samjha nahi", "kya matlab", "phir se", "kya bol",
                  "समझ नहीं", "समझा नहीं", "क्या मतलब", "फिर से", "क्या बोल")),
    ("bot_question", ("bot", "robot", "machine", "recorded", "insaan",
                      "बॉट", "रोबोट", "मशीन", "रिकॉर्डेड", "इंसान")),
]
DIRECTIVES = {
    "neutral": "Continue normally.",
    "rushed": "Seller is busy. Reply in ONE short sentence (max 12 words) and offer to call back at a time they choose.",
    "frustrated": "Seller is irritated. Apologise briefly, do not repeat the pitch, ask one yes/no question.",
    "confused": "Seller is confused. Re-explain in very simple Hindi, one idea only, then check understanding.",
    "bot_question": "Seller asked if you are a bot. Honestly confirm you are IndiaMART's AI assistant, then continue.",
}


def norm(s):
    # ASR and our cue list may encode nukta letters (ज़) differently; NFD makes them comparable.
    return unicodedata.normalize("NFD", s.lower())


def classify_stub(text):
    t = norm(text)
    for mode, cues in STUB:
        if any(norm(c) in t for c in cues):
            return mode
    return "neutral"


@app.get("/log")
def log(n: int = 50, x_signal_token: str = Header(default="")):
    check(x_signal_token)
    if not LOG.exists():
        return []
    return [json.loads(l) for l in LOG.read_text(encoding="utf-8").splitlines()[-n:]]
