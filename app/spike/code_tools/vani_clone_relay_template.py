"""CLONE ONLY - O2c / O6-via-relay variant of vani_onstart_test.py (test only).

ReadSellerSignal classifies with the keyword list, then asks the laptop relay (cloudflared quick tunnel ->
app/spike/midcall_relay.py -> Jev over VPN, or Sarvam LLM) with a 1.5 s timeout; on timeout/error the keyword
result stands. Only the utterance + a random shared relay token leave Sarvam; no model key is in this file.
The classifier is picked per call by the agent variable net_probe ("jev" default, or "sarvam").
__RELAY_URL__ is filled into a scratch copy at upload time; the relay token comes from a temporary workspace secret.


OnStart: set the voice, pace, pitch and opening per call from agent variables
(persona_voice_id, persona_pace, persona_pitch, persona_opening). The class must be named exactly `OnStart`.

ReadSellerSignal: an in-Sarvam switcher. It classifies the seller's latest utterance with a keyword list
(romanised + Devanagari, NFD), sets seller_mode and persona_directive, and appends a row to the switch_log
variable. No external host is needed.

2026-10-09 hardening (T4):
- switch_log keeps the last LOG_ROWS rows as a valid JSON list (the old `json.dumps(log)[-4000:]` cut the
  JSON in half once the log grew past 4000 chars).
- Per-turn dedupe: the hash of the normalised utterance is kept in an internal variable; a repeat call with
  the same utterance returns "no change" and is logged with dup=true (so double calls stay measurable).
- Added opt_out and interested cues, and the "warna phone rakh do" frustrated cue (lexicon gap seen earlier).
- Script of the utterance (deva / gujr / taml / latn) is logged, so language switches show in the log.
"""
import asyncio
import hashlib

import httpx
import json
import time
import unicodedata

from pydantic import Field
from sarvam_conv_ai_sdk import (SarvamOnStartTool, SarvamOnStartToolContext, SarvamTool, SarvamToolContext,
                                SarvamToolOutput)
from sarvam_conv_ai_sdk.tool import SpeechSettings, TextToSpeechConfig

LOG_ROWS = 25
RELAY_URL = "__RELAY_URL__"
RELAY_SECRET_NAME = "VANI_RELAY_TOKEN_TEST"  # temporary workspace secret holding the random relay token
RELAY_TIMEOUT = 1.5
_CLIENT = None
_CLIENT_NEW = None


def _client():
    # reuse one client (keep-alive) while the tool process lives; whether Sarvam keeps it between turns is measured via relay_ms
    global _CLIENT, _CLIENT_NEW
    _CLIENT_NEW = _CLIENT is None
    if _CLIENT is None:
        _CLIENT = httpx.AsyncClient(timeout=RELAY_TIMEOUT)
    return _CLIENT


def _var(context, name):
    try:
        return context.get_agent_variable(name)
    except Exception:
        return None


def _ivar(context, name):
    try:
        return context.get_internal_variable(name)
    except Exception:
        return None


def _num(value):
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


class OnStart(SarvamOnStartTool):
    """Apply the seller's VANI persona voice, pace, pitch and opening at call start."""

    async def run(self, context: SarvamOnStartToolContext) -> SarvamOnStartToolContext:
        voice_id = _var(context, "persona_voice_id")
        pace = _num(_var(context, "persona_pace"))
        pitch = _num(_var(context, "persona_pitch"))
        opening = _var(context, "persona_opening")
        if voice_id or pace is not None or pitch is not None:
            context.text_to_speech_config = TextToSpeechConfig(
                speaker_id=voice_id or None,
                speech_settings=SpeechSettings(pace=pace, pitch=pitch),
            )
        if opening:
            context.set_initial_bot_message(opening)
        return context


CUES = [
    ("opt_out", ("call mat karo", "call mat karna", "phone mat karo", "dobara call mat", "number hata", "do not call",
                 "don't call", "कॉल मत करो", "call मत करो", "कॉल मत करना", "फोन मत करो", "दोबारा कॉल मत", "नंबर हटा")),
    ("frustrated", ("kitni baar", "baar baar", "pareshan", "band karo", "disturb", "faltu", "warna phone", "phone rakh",
                    "कितनी बार", "बार बार", "परेशान", "बंद करो", "फालतू", "फ़ालतू", "वरना फोन", "फोन रख")),
    ("rushed", ("busy", "jaldi", "time nahi", "baad me", "abhi nahi", "driving", "meeting me",
                "बिज़ी", "बिजी", "जल्दी", "टाइम नहीं", "बाद में", "अभी नहीं", "ड्राइव", "मीटिंग में")),
    ("confused", ("samajh nahi", "samjha nahi", "kya matlab", "kya bol",
                  "समझ नहीं", "समझा नहीं", "क्या मतलब", "क्या बोल")),
    ("bot_question", ("bot", "robot", "machine", "recorded", "insaan",
                      "बॉट", "रोबोट", "मशीन", "रिकॉर्डेड", "इंसान")),
    ("interested", ("kitna charge", "kitne ka", "kab aayenge", "details bhej", "kaise milenge", "kaise aayenge",
                    "कितना चार्ज", "कितने का", "कब आएंगे", "डिटेल्स भेज", "कैसे मिलेंगे", "कैसे आएंगे", "कैसे मिलेंगे")),
]
DIRECTIVES = {
    "neutral": "Continue normally.",
    "rushed": "Seller is busy. Reply in ONE short sentence (max 12 words) and offer to call back at a time they choose.",
    "frustrated": "Seller is irritated. Apologise briefly, do not repeat the pitch, ask one yes/no question.",
    "confused": "Seller is confused. Slow down: re-explain in very simple Hindi, one idea only, written as very short phrases separated by commas (3-4 words per phrase), then check understanding.",
    "bot_question": "Seller asked if you are a bot. Honestly confirm you are IndiaMART's AI assistant, then continue.",
    "interested": "Seller is interested. Answer briefly and move straight to fixing a meeting day and time.",
    "opt_out": "Seller does not want calls. Apologise, confirm they will not be called again, thank them and end the call. Do not pitch.",
}


def _norm(s):
    return unicodedata.normalize("NFD", (s or "").lower())


def _classify(text):
    t = _norm(text)
    for mode, cues in CUES:
        if any(_norm(c) in t for c in cues):
            return mode
    return "neutral"


def _script(text):
    counts = {"deva": 0, "gujr": 0, "taml": 0, "latn": 0}
    for ch in text or "":
        o = ord(ch)
        if 0x0900 <= o <= 0x097F:
            counts["deva"] += 1
        elif 0x0A80 <= o <= 0x0AFF:
            counts["gujr"] += 1
        elif 0x0B80 <= o <= 0x0BFF:
            counts["taml"] += 1
        elif ch.isascii() and ch.isalpha():
            counts["latn"] += 1
    best = max(counts, key=counts.get)
    return best if counts[best] else "none"


def _append_log(context, row):
    try:
        log = json.loads(_var(context, "switch_log") or "[]")
        if not isinstance(log, list):
            log = []
    except Exception:
        log = []
    log.append(row)
    log = log[-LOG_ROWS:]
    context.set_agent_variable("switch_log", json.dumps(log, ensure_ascii=False))


class ReadSellerSignal(SarvamTool):
    """Reads the seller's latest words and returns how to adapt the conversation (seller_mode and a short persona_directive). Call this tool after EVERY seller turn, before you reply, passing the seller's last utterance exactly as spoken."""

    seller_utterance: str = Field(description="The seller's most recent utterance, copied word for word as spoken.")
    language: str = Field(default="", description="Language the seller just spoke in: hinglish, hindi, english, tamil, gujarati, other.")

    async def run(self, context: SarvamToolContext) -> SarvamToolOutput:
        t0 = time.perf_counter()
        prev = _var(context, "seller_mode") or "neutral"
        h = hashlib.sha256(_norm(self.seller_utterance).strip().encode("utf-8")).hexdigest()[:12]
        row = {"t": round(time.time(), 2), "utt": self.seller_utterance[:80], "lang": self.language,
               "script": _script(self.seller_utterance), "h": h}
        if h == _ivar(context, "last_utt_hash"):
            row.update({"from": prev, "to": prev, "switched": False, "dup": True,
                        "ms": round((time.perf_counter() - t0) * 1000, 2)})
            _append_log(context, row)
            return SarvamToolOutput(message_to_llm=f"No change. Seller mode: {prev} | Directive: {_var(context, 'persona_directive')}",
                                    context=context)
        context.set_internal_variable("last_utt_hash", h)
        kw_mode = _classify(self.seller_utterance)
        mode, relay = kw_mode, {}
        clf = (_var(context, "net_probe") or "jev").strip() or "jev"
        if clf not in ("jev", "sarvam"):
            clf = "jev"
        t1 = time.perf_counter()
        try:
            c = _client()
            r = await asyncio.wait_for(c.post(f"{RELAY_URL}/decide?clf={clf}", headers={"X-Relay-Token": context.get_secret(RELAY_SECRET_NAME)},
                                              json={"utt": self.seller_utterance,
                                                    "interaction_id": context.get_engagement_metadata().interaction_id}),
                                       RELAY_TIMEOUT)
            j = r.json()
            relay = {"relay_mode": j.get("mode"), "relay_clf_ms": j.get("ms"), "relay_err": j.get("err")}
            if r.status_code == 200 and j.get("mode") in DIRECTIVES and not j.get("err"):
                mode = j["mode"]
        except Exception as e:
            relay = {"relay_err": type(e).__name__}
        relay["relay_ms"] = round((time.perf_counter() - t1) * 1000)
        relay["clf"] = clf
        relay["conn_new"] = _CLIENT_NEW
        directive = DIRECTIVES[mode]
        context.set_agent_variable("seller_mode", mode)
        context.set_agent_variable("persona_directive", directive)
        row.update({"kw": kw_mode, **relay})
        row.update({"from": prev, "to": mode, "switched": mode != prev, "dup": False,
                    "ms": round((time.perf_counter() - t0) * 1000, 2)})
        _append_log(context, row)
        return SarvamToolOutput(
            message_to_llm=f"Seller mode: {mode} | Directive for your next reply: {directive}",
            context=context,
        )
