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
# 3 seller turns per language: yes / "why a meeting, tell me on the phone" / "ok, tomorrow 5 pm" (picked from persona_language)
LINES = {
    "te-IN": ["అవును, చెప్పండి.", "ఫోన్ లోనే చెప్పండి, మీటింగ్ ఎందుకు?", "సరే, రేపు సాయంత్రం ఐదు గంటలకు రండి."],
    "hi-IN": ["हाँ, बोलिए।", "फ़ोन पर ही बता दीजिए, मीटिंग क्यों?", "ठीक है, कल शाम पाँच बजे आ जाइए।"],
    "gu-IN": ["હા, બોલો.", "ફોન પર જ કહી દો, મીટિંગ કેમ?", "સારું, કાલે સાંજે પાંચ વાગ્યે આવો."],
    "mr-IN": ["हो, बोला.", "फोनवरच सांगा, मीटिंग कशाला?", "ठीक आहे, उद्या संध्याकाळी पाच वाजता या."],
    "ta-IN": ["ஆமா, சொல்லுங்க.", "போன்லயே சொல்லுங்க, மீட்டிங் எதுக்கு?", "சரி, நாளைக்கு சாயங்காலம் அஞ்சு மணிக்கு வாங்க."],
    "kn-IN": ["ಹೌದು, ಹೇಳಿ.", "ಫೋನ್‌ನಲ್ಲೇ ಹೇಳಿ, ಮೀಟಿಂಗ್ ಯಾಕೆ?", "ಸರಿ, ನಾಳೆ ಸಂಜೆ ಐದು ಗಂಟೆಗೆ ಬನ್ನಿ."],
    "ml-IN": ["അതെ, പറയൂ.", "ഫോണിൽ തന്നെ പറയൂ, മീറ്റിംഗ് എന്തിനാ?", "ശരി, നാളെ വൈകുന്നേരം അഞ്ചു മണിക്ക് വരൂ."],
    "bn-IN": ["হ্যাঁ, বলুন।", "ফোনেই বলুন, মিটিং কেন?", "ঠিক আছে, কাল সন্ধ্যা পাঁচটায় আসুন।"],
    "pa-IN": ["ਹਾਂ ਜੀ, ਦੱਸੋ।", "ਫੋਨ 'ਤੇ ਹੀ ਦੱਸ ਦਿਓ, ਮੀਟਿੰਗ ਕਿਉਂ?", "ਠੀਕ ਹੈ, ਕੱਲ੍ਹ ਸ਼ਾਮ ਪੰਜ ਵਜੇ ਆ ਜਾਓ।"],
    "od-IN": ["ହଁ, କୁହନ୍ତୁ।", "ଫୋନରେ ହିଁ କୁହନ୍ତୁ, ମିଟିଂ କାହିଁକି?", "ଠିକ ଅଛି, କାଲି ସନ୍ଧ୍ୟା ପାଞ୍ଚଟାରେ ଆସନ୍ତୁ।"],
    "en-IN": ["Yes, tell me.", "Tell me on the phone, why a meeting?", "Okay, come tomorrow evening at five."],
}
# Plan 5f test loop: ~1 minute scripted sellers, one fix each (lines are (text, language code)); checked afterwards by
# verify_call.py (variables first) and app/loops/rule_checks.py
SCENARIOS = {
    "questions": [("हाँ बोलिए", "hi-IN"), ("किस तरह की requirements हैं?", "hi-IN"), ("और किस इलाके से आई हैं?", "hi-IN"),
                  ("अच्छा, ठीक है।", "hi-IN")],                      # R1 answer-first, R2 no ask after a question
    "handler": [("हाँ बोलिए", "hi-IN"), ("मेरा एग्जीक्यूटिव कौन है?", "hi-IN"), ("नाम बताओ उसका, कौन आएगा?", "hi-IN")],  # R4
    "decline_then_book": [("नहीं चाहिए, नहीं चाहिए।", "hi-IN"), ("अच्छा, कैसी requirement है?", "hi-IN"),
                          ("ठीक है, कल शाम चार बजे आ जाइए।", "hi-IN"), ("नहीं, बस इतना ही, धन्यवाद।", "hi-IN")],  # declined, booking, R5
    "explicit_end": [("हाँ बोलिए", "hi-IN"), ("मुझे कॉल मत करो, फोन काट दो।", "hi-IN")],  # only an explicit request ends it
    # mid-call switch scenarios (read_seller_signal modes); expected mode in app/sarvam/test_loop.py EXPECT
    "switch_rushed": [("हाँ बोलिए", "hi-IN"), ("अभी बहुत बिज़ी हूँ, जल्दी बोलो", "hi-IN"), ("बाद में कॉल करना, शाम को", "hi-IN")],
    "switch_frustrated": [("हाँ", "hi-IN"), ("लीड्स की क्वालिटी बहुत बेकार है, बार बार फोन करते हो", "hi-IN"),
                          ("तो क्या करोगे इसका?", "hi-IN")],
    "switch_confused": [("हाँ", "hi-IN"), ("समझ नहीं आया, क्या बोल रहे हो?", "hi-IN"), ("अच्छा, फिर से बताओ", "hi-IN")],
    "switch_bot": [("हाँ बोलिए", "hi-IN"), ("आप बॉट हो क्या? मशीन से बात हो रही है?", "hi-IN"), ("सच बताओ, आप इंसान हो?", "hi-IN")],
    "switch_language": [("हो, बोला.", "mr-IN"), ("आप हिंदी में बात करो", "hi-IN"), ("Can you speak in English please?", "en-IN"),
                        ("Okay, tell me about the leads.", "en-IN")],
    "emotion_pleased": [("हाँ बोलिए", "hi-IN"), ("अरे वाह, ये तो बहुत बढ़िया बात है, अच्छा लगा सुनकर!", "hi-IN"),
                        ("हाँ हाँ, और बताइए", "hi-IN")],
    "emotion_irritated": [("हाँ", "hi-IN"), ("उफ्फ, जल्दी काम की बात करो यार, दिमाग खराब मत करो", "hi-IN"),
                          ("ठीक है बोलो", "hi-IN")],
    "ask_more": [("हाँ बोलिए", "hi-IN"), ("बाय लीड्स के अलावा क्या दोगे हमें?", "hi-IN"), ("और क्या है इसके अलावा?", "hi-IN"),
                 ("चलो ठीक है, कॉल रखो।", "hi-IN")],                   # R7: next topic each time, never 'no other info'
    "telugu_questions": [("అవును చెప్పండి", "te-IN"), ("ఎన్ని లీడ్స్ వచ్చాయి?", "te-IN"), ("ఎక్కడి నుండి వచ్చాయి?", "te-IN")],
}
LANG_CODE = {"TELUGU": "te-IN", "HINDI": "hi-IN", "GUJARATI": "gu-IN", "MARATHI": "mr-IN", "TAMIL": "ta-IN", "KANNADA": "kn-IN",
             "MALAYALAM": "ml-IN", "BENGALI": "bn-IN", "PUNJABI": "pa-IN", "ODIA": "od-IN", "ENGLISH": "en-IN"}


# the committed template version (build_template.py); every seller arrives as per-call variables
TEMPLATE_VERSION = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent.json"), encoding="utf-8"))["template_version"]

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
    a.add_argument("--lang", default="auto", help="auto = from persona_language in 05_sarvam_vars.json")
    a.add_argument("--version", type=int, default=TEMPLATE_VERSION)
    a.add_argument("--scenario", default="", help=f"one of {sorted(SCENARIOS)} (plan 5f test loop)")
    a.add_argument("--switch-to", default="", help="e.g. hi-IN: turn 1 in the persona language, turns 2-3 in this one "
                                                     "(checks the mid-call language switch)")
    p = a.parse_args()
    avars = json.load(open(os.path.join(p.run, "05_sarvam_vars.json"), encoding="utf-8"))
    if p.lang == "auto":
        p.lang = LANG_CODE.get(str(avars.get("persona_language")).upper(), "hi-IN")
    plan = SCENARIOS[p.scenario] if p.scenario else         [(LINES[p.lang][0], p.lang)] + [(x, p.switch_to or p.lang) for x in LINES[p.switch_to or p.lang][1:]]
    audio = [tts(x, lg) for x, lg in plan]
    iid, heard = asyncio.run(call(avars, audio, p.version))
    json.dump({"interaction_id": iid, "heard": heard, "scenario": p.scenario, "seller_lines": [lg for _, lg in plan]}, open(os.path.join(p.run, "voice_smoke.json"), "w", encoding="utf-8"),
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
