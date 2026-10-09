"""On-start code tool spike: set the voice, pace, pitch and opening line per call from agent variables.

Test only. The caller passes agent_variables {persona_voice_id, persona_pace, persona_pitch, persona_opening}
at session start. This tool copies them into the TTS config and the opening before the agent speaks.
The SDK requires the class to be named exactly `OnStart`.
"""
from sarvam_conv_ai_sdk import SarvamOnStartTool, SarvamOnStartToolContext
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
