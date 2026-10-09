"""Simulated voice call with Sarvam APIs only: seller TTS -> STT -> sarvam-105b (VANI) -> TTS.

Not the Sarvam Agents platform (that needs org / workspace / app ids). This tests that the
SCRUBBER seller context + persona plan drive VANI's spoken replies, and how VANI adapts when
the seller rushes, gets confused or asks if it is a bot.

Inputs: data/contexts/<glid>.md and data/contexts/sarvam_test/<glid>.json (persona plan).
Outputs (git-ignored): data/calls/<glid>/call.wav, turn audio, transcript.md, result.json
Key from env SARVAM_API_KEY only.

Run: SARVAM_API_KEY=... python app/context/voice_call_sim.py --glid G [--glid G2]
"""
import argparse
import base64
import io
import json
import os
import re
import sys
import time
import wave

import requests

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
API = "https://api.sarvam.ai"
SR = 16000
SELLER_SCRIPT = [  # (seller line, signal being tested)
    ("हाँ जी, बोलिए, कौन बोल रहा है?", "neutral"),
    ("अच्छा IndiaMART से। पहले भी आपके लोगों का फ़ोन आया था, अब क्या काम है?", "neutral / memory"),
    ("देखिए अभी थोड़ा जल्दी में हूँ, जल्दी बताइए क्या बात है।", "rush"),
    ("समझ नहीं आया, कौन सी enquiry की बात कर रहे हैं आप?", "confusion"),
    ("आप कोई मशीन हो क्या? recorded call है ये?", "bot question"),
    ("ठीक है, बताइए आगे क्या करना है।", "interest"),
]
VANI_VOICES = ["priya", "ritu", "neha", "kavya", "anushka"]
SELLER_VOICES = ["rahul", "aditya", "amit"]


def hdr(key):
    return {"api-subscription-key": key}


def tts(key, text, speaker, pace=1.0):
    r = requests.post(f"{API}/text-to-speech", headers=hdr(key), timeout=60,
                      json={"text": text, "target_language_code": "hi-IN", "model": "bulbul:v3", "speaker": speaker,
                            "pace": pace, "speech_sample_rate": SR})
    if r.status_code != 200:
        raise RuntimeError(f"TTS {r.status_code}: {r.text[:200]}")
    with wave.open(io.BytesIO(base64.b64decode(r.json()["audios"][0]))) as w:
        return w.readframes(w.getnframes())


def pick_voice(key, names):
    for n in names:
        try:
            tts(key, "नमस्ते", n)
            return n
        except Exception:
            continue
    raise RuntimeError(f"no working voice among {names}")


def wav_bytes(pcm):
    b = io.BytesIO()
    with wave.open(b, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm)
    return b.getvalue()


def stt(key, pcm):
    r = requests.post(f"{API}/speech-to-text", headers=hdr(key), timeout=60,
                      files={"file": ("turn.wav", wav_bytes(pcm), "audio/wav")},
                      data={"model": "saarika:v2.5", "language_code": "unknown"})
    if r.status_code != 200:
        raise RuntimeError(f"STT {r.status_code}: {r.text[:200]}")
    j = r.json()
    return j.get("transcript", ""), j.get("language_code")


def llm(key, messages, max_tokens=220):
    r = requests.post(f"{API}/v1/chat/completions", headers={**hdr(key), "Content-Type": "application/json"}, timeout=120,
                      json={"model": "sarvam-105b", "temperature": 0.3, "max_tokens": max_tokens,
                            "reasoning_effort": None, "messages": messages})
    if r.status_code != 200:
        raise RuntimeError(f"LLM {r.status_code}: {r.text[:200]}")
    c = r.json()["choices"][0]["message"]["content"] or ""
    return re.sub(r"<think>.*?</think>", "", c, flags=re.S).strip()


def system_prompt(md, plan):
    return f"""You are VANI, a female voice assistant calling from IndiaMART (use feminine Hindi verb forms: "बोल रही हूँ").
This is a live phone call with a seller. Speak natural Hindi in Devanagari script (English words like IndiaMART,
enquiry, buyer may stay in Latin). Each reply: 1-2 short sentences, under 30 words, no lists, no markdown.
You are an AI assistant: never claim to be human; if asked, say so honestly and continue politely.
Use ONLY facts from the seller context. Previous conversations (section G) are things you already know: build on
them and do not re-ask. Never fix call times or callbacks (another agent handles scheduling).
Adapt live: if the seller is in a hurry, be very short and get to the point; if confused, explain simply in one
idea; if irritated, apologise briefly; if interested, move to the next step (connect with an IndiaMART executive).

PERSONA PLAN (from the planner):
{json.dumps(plan, ensure_ascii=False)}

SELLER CONTEXT:
{md}"""


def run(glid, key):
    out = os.path.join(ROOT, "calls", glid)
    os.makedirs(out, exist_ok=True)
    md = open(os.path.join(ROOT, "contexts", f"{glid}.md"), encoding="utf-8").read()
    plan = json.load(open(os.path.join(ROOT, "contexts", "sarvam_test", f"{glid}.json"), encoding="utf-8"))["plan"]
    vani_v, seller_v = pick_voice(key, VANI_VOICES), pick_voice(key, SELLER_VOICES)
    opening = plan.get("opening_line", {}).get("text_native_script") or "नमस्ते, मैं IndiaMART से VANI बोल रही हूँ।"
    msgs = [{"role": "system", "content": system_prompt(md, plan)}, {"role": "assistant", "content": opening}]
    gap = b"\x00\x00" * int(SR * 0.4)
    audio, turns = [tts(key, opening, vani_v), gap], [{"speaker": "VANI", "text": opening, "note": "opening (from plan)"}]
    for i, (line, signal) in enumerate(SELLER_SCRIPT, 1):
        s_pcm = tts(key, line, seller_v)
        t0 = time.time()
        heard, lang = stt(key, s_pcm)
        t1 = time.time()
        msgs.append({"role": "user", "content": heard})
        reply, retries = llm(key, msgs), []
        if not reply:
            retries.append("empty")
            reply = llm(key, msgs, max_tokens=400)
        if len(reply.split()) > 35:
            retries.append(f"too_long:{len(reply.split())}")
            reply = llm(key, msgs + [{"role": "assistant", "content": reply},
                                     {"role": "user", "content": "(निर्देश: यही बात 25 शब्दों से कम में, एक-दो छोटे वाक्यों में कहिए।)"}]) or reply
        t2 = time.time()
        v_pcm = tts(key, reply, vani_v, pace=1.15 if signal == "rush" else 1.0)
        t3 = time.time()
        msgs.append({"role": "assistant", "content": reply})
        audio += [s_pcm, gap, v_pcm, gap]
        with open(os.path.join(out, f"turn{i}_seller.wav"), "wb") as f:
            f.write(wav_bytes(s_pcm))
        with open(os.path.join(out, f"turn{i}_vani.wav"), "wb") as f:
            f.write(wav_bytes(v_pcm))
        turns += [{"speaker": "SELLER", "text": line, "stt": heard, "stt_lang": lang, "signal_tested": signal},
                  {"speaker": "VANI", "text": reply, "words": len(reply.split()), "retries": retries or None,
                   "latency_sec": {"stt": round(t1 - t0, 2), "llm": round(t2 - t1, 2), "tts": round(t3 - t2, 2),
                                   "total": round(t3 - t0, 2)}}]
        print(f"turn {i} [{signal}] stt {t1-t0:.1f}s llm {t2-t1:.1f}s tts {t3-t2:.1f}s words {len(reply.split())} retries {retries}", file=sys.stderr)
    with open(os.path.join(out, "call.wav"), "wb") as f:
        f.write(wav_bytes(b"".join(audio)))
    res = {"glid": glid, "voices": {"vani": vani_v, "seller": seller_v}, "turns": turns,
           "call_seconds": round(len(b"".join(audio)) / 2 / SR, 1)}
    json.dump(res, open(os.path.join(out, "result.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    lines = [f"# Simulated VANI call: {glid}", "",
             f"Voices: VANI = {vani_v}, seller = {seller_v} (bulbul:v3). STT saarika:v2.5. LLM sarvam-105b (reasoning off). "
             f"Call length {res['call_seconds']} s. Audio: `call.wav`.", "",
             "| # | Speaker | Text | Signal / STT / latency |", "|---|---|---|---|"]
    n = 0
    for t in turns:
        n += t["speaker"] == "SELLER"
        meta = (f"{t['signal_tested']}; STT: {t['stt']}" if t["speaker"] == "SELLER"
                else (f"{t['words']} words; STT+LLM+TTS {t['latency_sec']['total']} s (LLM {t['latency_sec']['llm']} s)"
                      if "latency_sec" in t else t.get("note", "")))
        lines.append(f"| {n} | {t['speaker']} | {t['text']} | {meta} |")
    open(os.path.join(out, "transcript.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return out


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--glid", action="append", required=True)
    p = a.parse_args()
    key = os.environ.get("SARVAM_API_KEY") or sys.exit("set SARVAM_API_KEY")
    for g in p.glid:
        print(run(g.strip(), key))
