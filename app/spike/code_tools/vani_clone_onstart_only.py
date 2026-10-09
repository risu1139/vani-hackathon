"""CLONE ONLY - OnStart-only tool file (O1/O3 runs: no switch tool on the agent).

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
import hashlib
import json
import time
import unicodedata

from pydantic import Field
from sarvam_conv_ai_sdk import (SarvamOnStartTool, SarvamOnStartToolContext, SarvamTool, SarvamToolContext,
                                SarvamToolOutput)
from sarvam_conv_ai_sdk.tool import SpeechSettings, TextToSpeechConfig

LOG_ROWS = 25


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



class ReadSellerSignal(SarvamTool):
    """Disabled in this test agent. Never call this tool."""

    seller_utterance: str = Field(default="", description="Unused.")

    async def run(self, context: SarvamToolContext) -> SarvamToolOutput:
        return SarvamToolOutput(message_to_llm="Disabled. Continue without it.", context=context)
