"""Spikes 2+3+7 in CALL mode: a simulated seller (Sarvam TTS audio) talks to the Sarvam agent over the SDK.

Measures per seller turn: did the agent call read_seller_signal, reply latency after the seller stops,
and what the agent said (transcript) — so we can see whether a returned directive changes the reply.
Doubles as the core loop of the autonomous demo harness.

Usage: python app/spike/call_spike.py [--runs N] [--version 1]
"""
import argparse
import array
import asyncio
import base64
import inspect
import io
import json
import os
import time
import wave
from pathlib import Path

import requests
from pydantic import SecretStr
from sarvam_conv_ai_sdk import AsyncSamvaadAgent, InteractionConfig, InteractionType
from sarvam_conv_ai_sdk.messages.config import UserIdentifierType

ROOT = Path(__file__).resolve().parents[2]
for line in (ROOT / ".env").read_text().splitlines():
    if "=" in line and not line.lstrip().startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

SR = 16000
FRAME = SR * 2 // 50  # 20 ms of 16-bit mono PCM
SPEECH_RMS = 700  # int16 RMS above which an agent audio chunk counts as speech (above background ambience)
RMS_SEEN = []
SCRIPT = [  # (seller line, expected stub mode)
    ("Haan boliye, kaun bol raha hai?", "neutral"),
    ("Achha IndiaMART se. Kya kaam hai?", "neutral"),
    ("Abhi busy hoon yaar, jaldi bolo kya hai", "rushed"),
    ("Samajh nahi aaya, kya matlab meeting?", "confused"),
    ("Aap bot ho kya? Recorded call hai?", "bot_question"),
    ("Theek hai, kal gyarah baje aa jaiye", "neutral"),
]


def tts_pcm(text, speaker="rahul"):
    r = requests.post("https://api.sarvam.ai/text-to-speech", timeout=60,
                      headers={"api-subscription-key": os.environ["SARVAM_API_KEY"]},
                      json={"text": text, "target_language_code": "hi-IN", "model": "bulbul:v3",
                            "speaker": speaker, "speech_sample_rate": SR})
    r.raise_for_status()
    with wave.open(io.BytesIO(base64.b64decode(r.json()["audios"][0]))) as w:
        assert w.getframerate() == SR and w.getsampwidth() == 2 and w.getnchannels() == 1
        return w.readframes(w.getnframes())


def server_log(n=300):
    r = requests.get(os.environ["SIGNAL_SERVER_URL"] + f"/log?n={n}",
                     headers={"x-signal-token": os.environ["SIGNAL_TOKEN"]}, timeout=20)
    return r.json()


class Line:
    """Continuous 'microphone': streams silence, or seller speech when queued."""

    def __init__(self, agent):
        self.agent, self.queue, self.speaking_until = agent, asyncio.Queue(), 0.0

    async def send(self, chunk):
        res = self.agent.send_audio(chunk)
        if inspect.isawaitable(res):
            await res

    async def run(self):
        silence = b"\x00" * FRAME
        nxt = time.perf_counter()
        buf = b""
        while self.agent.is_connected():
            if not buf and not self.queue.empty():
                buf = self.queue.get_nowait()
            if buf:
                chunk, buf = buf[:FRAME], buf[FRAME:]
                chunk = chunk.ljust(FRAME, b"\x00")
                if not buf:
                    self.speaking_until = time.time()
            else:
                chunk = silence
            await self.send(chunk)
            nxt += 0.02
            await asyncio.sleep(max(0, nxt - time.perf_counter()))


async def run_once(idx, version, seller_audio):
    events, last_agent_audio = [], {"t": 0.0, "first_after": None}

    async def on_audio(msg):
        # Background ambience streams continuously, so only loud chunks count as agent speech.
        pcm = array.array("h", base64.b64decode(msg.audio_base64 or ""))
        rms = (sum(s * s for s in pcm) / len(pcm)) ** 0.5 if pcm else 0
        RMS_SEEN.append(rms)
        if rms > SPEECH_RMS:
            last_agent_audio["t"] = time.time()

    async def on_transcript(msg):
        events.append((time.time(), str(getattr(msg.role, "value", msg.role)), msg.content))

    cfg = InteractionConfig(
        org_id=os.environ["SARVAM_ORG_ID"], workspace_id=os.environ["SARVAM_WORKSPACE_ID"],
        app_id=os.environ["SARVAM_AGENT_APP_ID"], version=version, interaction_type=InteractionType.CALL,
        user_identifier_type=UserIdentifierType.CUSTOM, user_identifier=f"spike-{int(time.time())}-{idx}",
        sample_rate=SR)
    agent = AsyncSamvaadAgent(api_key=SecretStr(os.environ["SARVAM_AGENTS_API_KEY"]), config=cfg,
                              audio_callback=on_audio, transcript_callback=on_transcript)
    await agent.start()
    await agent.wait_for_connect()
    line = Line(agent)
    streamer = asyncio.create_task(line.run())

    async def wait_agent_done(after, timeout=30, quiet=1.6):
        t0 = time.time()
        first = None
        while time.time() - t0 < timeout and agent.is_connected():
            la = last_agent_audio["t"]
            if la > after and first is None:
                first = la
            if first and time.time() - la > quiet:
                return first
            await asyncio.sleep(0.05)
        return first

    await wait_agent_done(time.time() - 1, timeout=20)  # greeting
    t_start = time.time()
    turns = []
    for (text, expected), pcm in zip(SCRIPT, seller_audio):
        if not agent.is_connected():
            print("call ended early by the agent")
            break
        t_sent = time.time()
        line.speaking_until = 0
        line.queue.put_nowait(pcm)
        while line.speaking_until == 0 and agent.is_connected():
            await asyncio.sleep(0.02)
        t_end_speech = line.speaking_until
        first = await wait_agent_done(t_end_speech)
        turns.append({"seller": text, "expected": expected, "t_sent": t_sent, "t_end_speech": t_end_speech,
                      "reply_latency_s": round(first - t_end_speech, 2) if first else None})
    await asyncio.sleep(1)
    await agent.stop()
    streamer.cancel()
    return {"interaction_id": agent.get_interaction_id(), "t_start": t_start, "turns": turns, "events": events}


async def main(runs, version):
    seller_audio = [tts_pcm(t) for t, _ in SCRIPT]
    out = []
    for i in range(runs):
        res = await run_once(i, version, seller_audio)
        await asyncio.sleep(2)
        log = [e for e in server_log() if e["ts"] >= res["t_start"] - 1]
        for k, t in enumerate(res["turns"]):
            t_next = res["turns"][k + 1]["t_sent"] if k + 1 < len(res["turns"]) else 1e18
            hits = [e for e in log if t["t_sent"] <= e["ts"] < t_next]
            t["tool_calls"] = len(hits)
            t["tool_after_speech_s"] = round(hits[0]["ts"] - t["t_end_speech"], 2) if hits else None
            modes = [h.get("mode") for h in hits]
            t["mode"] = next((m for m in modes if m and m != "neutral"), modes[0] if modes else None)
            t["sent_utterance"] = hits[0]["body"].get("seller_utterance") if hits else None
            t["agent_said"] = " ".join(c for ts, role, c in res["events"]
                                       if "user" not in role.lower() and t["t_sent"] <= ts < t_next)
            t["asr_heard"] = " ".join(c for ts, role, c in res["events"]
                                      if "user" in role.lower() and t["t_sent"] <= ts < t_next)
        out.append(res)
        for t in res["turns"]:
            print(f"[run {i}] {t['expected']:>12} | tool={t['tool_calls']} mode={t['mode']} "
                  f"tool@+{t['tool_after_speech_s']}s reply@+{t['reply_latency_s']}s | "
                  f"heard='{t['asr_heard'][:45]}' | said({len(t['agent_said'].split())}w)='{t['agent_said'][:110]}'")
    path = ROOT / "outputs" / f"spike-call-{time.strftime('%Y%m%d-%H%M%S')}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    turns = [t for r in out for t in r["turns"]]
    called = sum(1 for t in turns if t["tool_calls"] > 0)
    lat = sorted(t["reply_latency_s"] for t in turns if t["reply_latency_s"] is not None)
    if RMS_SEEN:
        s = sorted(RMS_SEEN)
        print(f"agent-audio RMS: n={len(s)} p10={s[len(s) // 10]:.0f} p50={s[len(s) // 2]:.0f} p90={s[9 * len(s) // 10]:.0f} max={s[-1]:.0f}")
    print(f"\nTool called on {called}/{len(turns)} seller turns. Reply latency after seller stops: "
          f"median {lat[len(lat) // 2] if lat else None}s, max {lat[-1] if lat else None}s. Saved {path.name}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--version", type=int, default=1)
    a = ap.parse_args()
    asyncio.run(main(a.runs, a.version))
