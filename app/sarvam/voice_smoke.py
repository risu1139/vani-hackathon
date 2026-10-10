"""voice_smoke.py: one short VOICE session on the published agent (SDK CALL route, API key), so the call lands in the
analytics feed with post-call labels. Then: python app/loops/close_loop.py --interaction-id <id> --names <map> --test

Seller audio is made with Sarvam TTS on SARVAM_STT_API_KEY only (never the main key, user rule).
Agent variables = <run>/05_sarvam_vars.json. 3 seller turns, then the session is stopped (ends the interaction).

Usage: python app/sarvam/voice_smoke.py --run data/runs/<id> [--lang te-IN] [--version 1]
"""
import argparse
import array
import asyncio
import base64
import io
import json
import os
import sys
import time
import wave

import requests
from pydantic import SecretStr
from sarvam_conv_ai_sdk import AsyncSamvaadAgent, InteractionConfig, InteractionType
from sarvam_conv_ai_sdk.messages.config import UserIdentifierType

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "app", "spike"))
from call_spike import SPEECH_RMS, SR, Line  # noqa: E402  (20 ms PCM "microphone")

APP = "VANI-person-b8c173ff-b272"
LINES = {"te-IN": ["అవును, చెప్పండి.", "ఫోన్ లోనే చెప్పండి, మీటింగ్ ఎందుకు?", "సరే, రేపు సాయంత్రం ఐదు గంటలకు రండి."]}


def tts(text, lang):
    r = requests.post("https://api.sarvam.ai/text-to-speech", timeout=60,
                      headers={"api-subscription-key": os.environ["SARVAM_STT_API_KEY"]},
                      json={"text": text, "target_language_code": lang, "model": "bulbul:v3", "speaker": "rahul",
                            "speech_sample_rate": SR})
    r.raise_for_status()
    with wave.open(io.BytesIO(base64.b64decode(r.json()["audios"][0]))) as w:
        return w.readframes(w.getnframes())


async def call(avars, audio, version):
    heard, last = [], {"t": 0.0}

    async def on_audio(msg):  # only real speech counts; the agent also streams background silence
        pcm = array.array("h", base64.b64decode(msg.audio_base64 or ""))
        if pcm and (sum(x * x for x in pcm) / len(pcm)) ** 0.5 > SPEECH_RMS:
            last["t"] = time.time()

    async def on_transcript(msg):
        heard.append({"t": round(time.time(), 2), "role": str(getattr(msg.role, "value", msg.role)), "text": msg.content})

    cfg = InteractionConfig(org_id=os.environ["SARVAM_ORG_ID"], workspace_id=os.environ["SARVAM_WORKSPACE_ID"], app_id=APP,
                            version=version, interaction_type=InteractionType.CALL, user_identifier_type=UserIdentifierType.CUSTOM,
                            user_identifier=f"voice-smoke-{int(time.time())}", sample_rate=SR, agent_variables=avars)
    agent = AsyncSamvaadAgent(api_key=SecretStr(os.environ["SARVAM_AGENTS_API_KEY"]), config=cfg,
                              audio_callback=on_audio, transcript_callback=on_transcript)
    await agent.start()
    await agent.wait_for_connect()
    line = Line(agent)
    streamer = asyncio.create_task(line.run())

    async def quiet(after, timeout=25, gap=1.8):
        t0 = time.time()
        while time.time() - t0 < timeout and agent.is_connected():
            if last["t"] > after and time.time() - last["t"] > gap:
                return
            await asyncio.sleep(0.05)

    await quiet(time.time() - 1)  # opening
    for pcm in audio:
        if not agent.is_connected():
            break
        t = time.time() + len(pcm) / (2 * SR)
        line.queue.put_nowait(pcm)
        await asyncio.sleep(len(pcm) / (2 * SR))
        await quiet(t)
    iid = agent.get_interaction_id()  # set by the server's interaction_connected event, not at connect time
    print(f"connected={agent.is_connected()} audio_seen={last['t'] > 0} transcripts={len(heard)}")
    await agent.stop()
    streamer.cancel()
    return iid, heard


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--run", required=True)
    a.add_argument("--lang", default="te-IN")
    a.add_argument("--version", type=int, default=2)
    p = a.parse_args()
    avars = json.load(open(os.path.join(p.run, "05_sarvam_vars.json"), encoding="utf-8"))
    audio = [tts(x, p.lang) for x in LINES[p.lang]]
    iid, heard = asyncio.run(call(avars, audio, p.version))
    json.dump({"interaction_id": iid, "heard": heard}, open(os.path.join(p.run, "voice_smoke.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    names = [avars.get("seller_name"), avars.get("company_name")]
    for h in heard:
        txt = h["text"] or ""
        for n in names:
            if n:
                txt = txt.replace(n, "<NAME>")
        print(f"{h['role']:9s} {txt[:150]}")
    print("INTERACTION", iid)


if __name__ == "__main__":
    main()
