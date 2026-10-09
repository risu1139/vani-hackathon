"""Code tools spike (test only).

OnStart: set the voice, pace, pitch and opening per call from agent variables
(persona_voice_id, persona_pace, persona_pitch, persona_opening). The class must be named exactly `OnStart`.

ReadSellerSignal: an in-Sarvam switcher. It classifies the seller's latest utterance with a keyword list
(romanised + Devanagari, NFD), sets seller_mode and persona_directive, and appends a row to the switch_log
variable. No external host is needed.
"""
import json
import time
import unicodedata

from pydantic import Field
from sarvam_conv_ai_sdk import (SarvamOnStartTool, SarvamOnStartToolContext, SarvamTool, SarvamToolContext,
                                SarvamToolOutput)
from sarvam_conv_ai_sdk.tool import SpeechSettings, TextToSpeechConfig


def _var(context, name):
    try:
        return context.get_agent_variable(name)
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
    ("rushed", ("busy", "jaldi", "time nahi", "baad me", "abhi nahi", "driving", "meeting me",
                "बिज़ी", "बिजी", "जल्दी", "टाइम नहीं", "बाद में", "अभी नहीं", "ड्राइव", "मीटिंग में")),
    ("frustrated", ("kitni baar", "baar baar", "pareshan", "mat karo", "band karo", "disturb", "faltu",
                    "कितनी बार", "बार बार", "परेशान", "मत करो", "बंद करो", "फालतू", "फ़ालतू")),
    ("confused", ("samajh nahi", "samjha nahi", "kya matlab", "kya bol",
                  "समझ नहीं", "समझा नहीं", "क्या मतलब", "क्या बोल")),
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


def _norm(s):
    return unicodedata.normalize("NFD", (s or "").lower())


def _classify(text):
    t = _norm(text)
    for mode, cues in CUES:
        if any(_norm(c) in t for c in cues):
            return mode
    return "neutral"


class ReadSellerSignal(SarvamTool):
    """Reads the seller's latest words and returns how to adapt the conversation (seller_mode and a short persona_directive). Call this tool after EVERY seller turn, before you reply, passing the seller's last utterance exactly as spoken."""

    seller_utterance: str = Field(description="The seller's most recent utterance, copied word for word as spoken.")
    language: str = Field(default="", description="Language the seller just spoke in: hinglish, hindi, english, tamil, gujarati, other.")

    async def run(self, context: SarvamToolContext) -> SarvamToolOutput:
        t0 = time.perf_counter()
        prev = _var(context, "seller_mode") or "neutral"
        mode = _classify(self.seller_utterance)
        directive = DIRECTIVES[mode]
        context.set_agent_variable("seller_mode", mode)
        context.set_agent_variable("persona_directive", directive)
        try:
            log = json.loads(_var(context, "switch_log") or "[]")
        except Exception:
            log = []
        log.append({"t": round(time.time(), 2), "utt": self.seller_utterance[:120], "lang": self.language,
                    "from": prev, "to": mode, "switched": mode != prev, "ms": round((time.perf_counter() - t0) * 1000, 2)})
        context.set_agent_variable("switch_log", json.dumps(log, ensure_ascii=False)[-4000:])
        return SarvamToolOutput(
            message_to_llm=f"Seller mode: {mode} | Directive for your next reply: {directive}",
            context=context,
        )
