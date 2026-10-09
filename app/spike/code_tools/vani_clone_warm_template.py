"""CLONE ONLY - warm-relay test (W1 / W2 / W3) variant of vani_onstart_test.py (test only).

ReadSellerSignal classifies with the keyword list, then (by variant, from agent variable net_probe):
  w1: always asks the laptop relay (cloudflared -> app/spike/midcall_relay.py -> Jev, kept warm), 1.5 s cap, keyword fallback
  w3: hybrid - keyword decides; relay only if keyword finds nothing and the turn has >= 6 words, or the turn is an
      ambiguous short reply (ok ok / haan / theek hai); 0.4 s cap, keyword result stands on timeout
W2 = the w1 file with a pre_run_message filler (built from this file at upload time).
Auth: HMAC-SHA256 over "{ts}.{interaction_id}.{utterance}" with a workspace secret read via context.get_secret;
no key or token is in this file. __RELAY_URL__ is filled in a scratch copy at upload time.
"""
import asyncio
import hashlib
import hmac

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
RELAY_SECRET_NAME = "VANI_RELAY_HMAC_TEST"  # temporary workspace secret (HMAC key for the relay)
HYBRID_TIMEOUT = 0.4
AMBIGUOUS = ("ok ok", "okay", "ओके", "हाँ", "हां", "haan", "theek hai", "ठीक है", "हम्म")
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
        variant = (_var(context, "net_probe") or "w1").strip() or "w1"
        words = len(self.seller_utterance.split())
        ambiguous = words <= 4 and any(_norm(a) in _norm(self.seller_utterance) for a in AMBIGUOUS)
        call_relay = variant != "w3" or (kw_mode == "neutral" and words >= 6) or ambiguous
        timeout = HYBRID_TIMEOUT if variant == "w3" else RELAY_TIMEOUT
        relay = {"variant": variant, "relay_called": call_relay}
        if call_relay:
            t1 = time.perf_counter()
            try:
                iid = context.get_engagement_metadata().interaction_id
                ts = str(int(time.time()))
                sig = hmac.new(context.get_secret("VANI_RELAY_HMAC_TEST").encode(),
                               f"{ts}.{iid}.{self.seller_utterance}".encode("utf-8"), hashlib.sha256).hexdigest()
                c = _client()
                r = await asyncio.wait_for(c.post(f"{RELAY_URL}/decide?clf=jev", headers={"X-Ts": ts, "X-Sig": sig},
                                                  json={"utt": self.seller_utterance, "interaction_id": iid}), timeout)
                j = r.json()
                relay.update({"relay_mode": j.get("mode"), "relay_clf_ms": j.get("ms"), "relay_err": j.get("err") or (None if r.status_code == 200 else r.status_code)})
                if r.status_code == 200 and j.get("mode") in DIRECTIVES and not j.get("err"):
                    mode = j["mode"]
            except asyncio.TimeoutError:
                relay["relay_err"] = "timeout"
            except Exception as e:
                relay["relay_err"] = type(e).__name__
            relay["relay_ms"] = round((time.perf_counter() - t1) * 1000)
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
