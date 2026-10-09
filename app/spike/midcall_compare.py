"""Head-to-head mid-call switching harness (2026-10-09). SDK voice sessions, Sarvam-TTS seller audio, made-up lines.

Options (--opt):
  probe  T1: push raw client actions mid-call (variable_update / language_change / state_transition), log raw frames
  O1     Sarvam by itself: no switch tool; persona_directive carries the adaptation rules (LLM decides live)
  O2     in-Sarvam code tool with the keyword classifier (whatever ReadSellerSignal is uploaded on --app)
  O3     Jev on the laptop on each user transcript -> push seller_mode/persona_directive ONLY on change
         (channel: client.action.variable_update over the session websocket = T1 route)
  O4     like O3 but pushes client.action.state_transition / language_change instead of variables

Per turn we log: seller line, ASR text, reply text, reply onset after the seller stopped, raw server events,
Jev scores/decision/push timing (O3/O4), reply checks for the signal on the same turn and the next turn.

Usage: python app/spike/midcall_compare.py --opt O3 --app VANI-midcal-506a41a2-0422 --scen rushed,frustrated --runs 2
"""
import argparse
import array
import asyncio
import base64
import copy
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import requests
from pydantic import SecretStr
from sarvam_conv_ai_sdk import AsyncSamvaadAgent, InteractionConfig, InteractionType
from sarvam_conv_ai_sdk.messages.config import UserIdentifierType

from call_spike import ROOT, SPEECH_RMS, SR, Line
from plan_stress import tts
import jev_spike
from jev_devanagari import questions_native

OUT = ROOT / "outputs" / "midcall_tests"
OUT.mkdir(parents=True, exist_ok=True)
ORG, WS = os.environ["SARVAM_ORG_ID"], os.environ["SARVAM_WORKSPACE_ID"]
MAIN_APP = os.environ["SARVAM_AGENT_APP_ID"]

OPENER = ("हाँ जी बोलिए, कौन बोल रहा है?", "hi-IN", "neutral")
SCEN = {
    "rushed": [OPENER, ("अभी बिज़ी हूँ यार, जल्दी बोलो क्या है", "hi-IN", "rushed"), ("हम्म, ठीक है", "hi-IN", "after")],
    "frustrated": [OPENER, ("कितनी बार कॉल करोगे, परेशान कर दिया है", "hi-IN", "frustrated"), ("हम्म, ठीक है", "hi-IN", "after")],
    "confused": [OPENER, ("समझ नहीं आया, क्या मतलब मीटिंग?", "hi-IN", "confused"), ("हम्म, ठीक है", "hi-IN", "after")],
    "interested": [OPENER, ("ओके ओके", "hi-IN", "neutral"), ("अच्छा, ये कैसे काम करता है? कितना चार्ज है?", "hi-IN", "interested")],
    "gujarati": [OPENER, ("ગુજરાતીમાં વાત કરો ને, મને હિન્દી ઓછું ફાવે છે.", "gu-IN", "gujarati"), ("સારું, આગળ બોલો.", "gu-IN", "after_gu")],
    "optout": [OPENER, ("मुझे कॉल मत करो, मेरा नंबर हटा दो", "hi-IN", "opt_out")],
    "A_hostile": [
        ("पहले ये बताओ आप कौन हो और कहाँ से बोल रहे हो?", "hi-IN", "neutral"),
        ("मैं owner नहीं हूँ, manager हूँ. Owner बाहर गए हैं.", "hi-IN", "neutral"),
        ("अच्छा ठीक है, पर exact price बताओ, कितने का plan है?", "hi-IN", "interested"),
        ("फिर से पूछ रहा हूँ, प्राइस बताओ वरना फोन रख दो", "hi-IN", "frustrated"),
        ("अभी बिज़ी हूँ यार, बाद में बात करते हैं", "hi-IN", "rushed"),
    ],
}

SCEN["A_coop"] = [("Haan ji, main hi owner hoon. Boliye.", "hi-IN", "neutral"),
                  ("Achha haan yaad aaya. Par paise kitne lagenge? Aapka plan bahut mehnga hai.", "hi-IN", "interested"),
                  ("Theek hai, mil lete hain.", "hi-IN", "interested"), ("Kal shaam paanch baje aa jaiye.", "hi-IN", "neutral")]
SCEN["B_gujarati"] = [("Leads ki zarurat nahi hai, pehle se bahut aa rahi hain.", "hi-IN", "neutral"),
                      ("Aur aapka plan mehnga bhi hai.", "hi-IN", "neutral"),
                      ("ગુજરાતીમાં વાત કરો ને, મને હિન્દી ઓછું ફાવે છે.", "gu-IN", "gujarati"),
                      ("સારું, બલ્ક બાયર્સ જોઈએ છે. મીટિંગ ક્યારે કરશો?", "gu-IN", "interested"),
                      ("કાલે સવારે દસ વાગ્યે.", "gu-IN", "after_gu")]

SCEN["MIN"] = [OPENER, ("ओके ओके", "hi-IN", "neutral"),
               ("अच्छा, ये कैसे काम करता है? कितना चार्ज है?", "hi-IN", "interested"),
               ("समझ नहीं आया, क्या मतलब मीटिंग?", "hi-IN", "confused"),
               ("कितनी बार कॉल करोगे, परेशान कर दिया है", "hi-IN", "frustrated"),
               ("ગુજરાતીમાં વાત કરો ને, મને હિન્દી ઓછું ફાવે છે.", "gu-IN", "gujarati"),
               ("अभी बिज़ी हूँ यार, जल्दी बोलो क्या है", "hi-IN", "rushed")]

GUJ = r"[઀-૿]"
CHECKS = {  # does a reply show the adaptation for this signal?
    "rushed": lambda r: len(r.split()) <= 16 and bool(re.search(r"बाद|baad|later|call|कॉल|समय|time|कब|बजे|मिनट", r, re.I)),
    "frustrated": lambda r: bool(re.search(r"माफ़|माफ|sorry|क्षमा|maaf|मुआफ", r, re.I)),
    "confused": lambda r: r.count(",") + r.count("…") >= 3 or bool(re.search(r"समझ (आया|गए|पाए)|clear", r, re.I)),
    "interested": lambda r: bool(re.search(r"मीटिंग|meeting|कब|समय|time|दिन|बजे|executive|एग्ज़ीक्यूटिव|एग्जीक्यूटिव", r, re.I)),
    "gujarati": lambda r: bool(re.search(GUJ, r)),
    "opt_out": lambda r: bool(re.search(r"नंबर हटा|number हटा|हटा दे|दोबारा (कॉल|call)|(कॉल|call) नहीं (आएगा|करेंगे|करेंगी)|won't call|not call you", r, re.I)),
}
SIGNALS = list(CHECKS)

DIRECTIVES = {
    "neutral": "Continue normally.",
    "rushed": "Seller is busy. Reply in ONE short sentence (max 12 words) and offer to call back at a time they choose.",
    "frustrated": "Seller is irritated. Apologise briefly, do not repeat the pitch, ask one yes/no question.",
    "confused": "Seller is confused. Slow down: re-explain in very simple Hindi, one idea only, written as very short phrases separated by commas (3-4 words per phrase), then check understanding.",
    "bot_question": "Seller asked if you are a bot. Honestly confirm you are IndiaMART's AI assistant, then continue.",
    "interested": "Seller is interested. Answer briefly and move straight to fixing a meeting day and time.",
    "opt_out": "Seller does not want calls. Apologise, confirm they will not be called again, thank them and end the call. Do not pitch.",
}
O1B_PLAYBOOK = ("SWITCH PLAYBOOK for this seller (Shree Ganesh Pipes, PVC pipes, Indore; owner prefers short calls). Decide yourself which block applies on each turn and follow it: "
                "[RUSHED] 'Koi baat nahi ji, PVC buyers wali baat 2 minute ki hai - kab call karun?' style: max 12 words, offer a callback time. "
                "[FRUSTRATED] Say sorry for the repeated calls in one line, do not repeat the PVC pitch, ask one yes/no question. "
                "[CONFUSED] Slow down, short comma phrases (3-4 words each): who we are, why we call (more PVC buyers in Indore), then ask 'samajh aaya?'. "
                "[INTERESTED] One line answer, then fix a day and time for the IndiaMART executive to visit the Indore shop. A bare 'ok ok' is not interest. "
                "[OPT-OUT] Apologise, confirm the number will not be called again, thank them, end the call; no pitch. "
                "[LANGUAGE] If the seller switches language, continue in that language. Otherwise continue normally.")
O1_RULES = ("ADAPT TO THE SELLER, decide yourself on every turn: "
            "RUSHED (busy, 'jaldi', 'baad mein'): reply in ONE short sentence (max 12 words) and offer to call back at a time they choose. "
            "FRUSTRATED (irritated, 'kitni baar', 'pareshan', threatens to hang up): apologise briefly, do not repeat the pitch, ask one yes/no question. "
            "CONFUSED ('samajh nahi aaya', 'kya matlab'): slow down, very short phrases separated by commas (3-4 words each), one idea, then check understanding. "
            "INTERESTED (asks how it works, price, details): answer briefly and move straight to fixing a meeting day and time. A bare 'ok ok' is NOT interest. "
            "OPT-OUT ('call mat karo', 'number hata do'): apologise, confirm they will not be called again, thank them and end the call, no pitch. "
            "LANGUAGE: if the seller switches language, reply in that language. Otherwise continue normally.")

# --- Jev ---------------------------------------------------------------------------------------------------
QUESTIONS = questions_native()
QUESTIONS["opt_out"] = {"type": "noul",
                        "instructions": "In the latest seller turn, does the seller ask not to be called again or to remove their number?",
                        "criteria": {"true": "e.g. 'call mat karo', 'मुझे कॉल मत करो', 'नंबर हटा दो', 'dobara phone mat karna', 'do not call me'.",
                                     "false": "Only busy now / call later, or merely not interested in the offer."}}
QUESTIONS["language"]["criteria"]["gujarati"] = "Gujarati, in Gujarati script or romanized"
PRIORITY = ["opt_out", "frustrated", "rushed", "confused", "bot_question", "interested"]
POOL = ThreadPoolExecutor(max_workers=4)


def jev(utterance, last_agent):
    body = {"model": jev_spike.MODEL, "state": {"agent_last_line": last_agent[-300:], "seller_latest_turn": utterance},
            "questions": QUESTIONS}
    t0 = time.perf_counter()
    r = jev_spike.SESSION.post(jev_spike.URL, json=body, timeout=10,
                               headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"})
    ms = (time.perf_counter() - t0) * 1000
    r.raise_for_status()
    a = r.json()["answers"]
    scores = {k: round(v["noul"], 2) for k, v in a.items() if v.get("type") == "noul"}
    lang = a.get("language", {}).get("choice")
    mode = next((k for k in PRIORITY if scores.get(k, 0) >= 0.5), "neutral")
    return round(ms), scores, lang, mode


# --- helpers -----------------------------------------------------------------------------------------------
def analytics_vars(app, iid):
    now = datetime.now(timezone.utc)
    r = requests.get(f"https://apps.sarvam.ai/api/analytics/v1/{ORG}/{WS}/{app}/interactions", timeout=20,
                     headers={"X-API-Key": os.environ["SARVAM_AGENTS_API_KEY"]},
                     params={"start_datetime": (now - timedelta(hours=2)).isoformat(), "end_datetime": (now + timedelta(minutes=5)).isoformat(),
                             "limit": 50})
    for it in r.json().get("items", []):
        if it.get("interaction_id") == iid:
            return it.get("agent_variables") or {}, it
    return None, None


async def run_call(opt, app, scen, idx, audio, probe_plan=None):
    turns = SCEN[scen]
    frames, events, onsets, bursts = [], [], [], []
    state = {"last": 0.0, "mode": "neutral", "agent_text": "", "lang": "hindi"}
    decisions, push_tasks = [], []
    t0 = time.time()

    agent_box = {}

    async def push(payload):
        msg = {"origin": "client", "timestamp": time.time(), **payload}
        await agent_box["a"]._ws.send(json.dumps(msg, ensure_ascii=False))
        frames.append({"t": round(time.time() - t0, 3), "dir": "out", "type": payload["type"], "msg": msg})
        return time.time()

    async def decide_and_push(text, t_heard):
        loop = asyncio.get_running_loop()
        try:
            ms, scores, lang, mode = await loop.run_in_executor(POOL, jev, text, state["agent_text"])
        except Exception as e:
            decisions.append({"utt": text, "err": str(e)[:200], "t_heard": t_heard})
            return
        t_dec = time.time()
        d = {"utt": text, "t_heard": t_heard, "jev_ms": ms, "scores": scores, "lang": lang,
             "from": state["mode"], "to": mode, "pushed": False}
        if mode != state["mode"]:
            if opt == "O3":
                tp = await push({"type": "client.action.variable_update",
                                 "agent_variables": {"seller_mode": mode, "persona_directive": DIRECTIVES[mode]}})
            elif opt == "O3t":
                tp = await push({"type": "client.media.text",
                                 "text": f"[SYSTEM NOTE from the call monitor, not spoken by the seller; do not answer this note] "
                                         f"Seller mode is now {mode}. Directive for your replies: {DIRECTIVES[mode]}"})
            else:  # O4: state / language actions
                tp = await push({"type": "client.action.state_transition", "state_name": mode})
            d.update(pushed=True, t_push=tp, push_ms=round((tp - t_heard) * 1000))
            state["mode"] = mode
        if opt == "O4" and lang == "gujarati" and state["lang"] != "gujarati":
            tp = await push({"type": "client.action.language_change", "language_name": "Gujarati"})
            d.update(lang_pushed=True, t_lang_push=tp)
            state["lang"] = "gujarati"
        d["t_decided"] = t_dec
        decisions.append(d)

    async def on_audio(msg):
        pcm = array.array("h", base64.b64decode(msg.audio_base64 or ""))
        if pcm and (sum(x * x for x in pcm) / len(pcm)) ** 0.5 > SPEECH_RMS:
            now = time.time()
            if now - state["last"] > 0.6:
                onsets.append(now)
                bursts.append([now, now])
            elif bursts:
                bursts[-1][1] = now
            state["last"] = now

    async def on_transcript(msg):
        role = str(getattr(msg.role, "value", msg.role))
        now = time.time()
        events.append((now, role, msg.content))
        if "user" in role.lower():
            if opt in ("O3", "O3t", "O4"):
                push_tasks.append(asyncio.create_task(decide_and_push(msg.content, now)))
        else:
            state["agent_text"] = msg.content

    init_vars = {"seller_mode": "neutral",
                 "persona_directive": O1_RULES if opt == "O1" else O1B_PLAYBOOK if opt == "O1b" else "Continue normally.",
                 "switch_log": "[]"}
    if opt in ("O2c", "O6"):  # relay copy: the tool reads the classifier choice from net_probe
        init_vars["net_probe"] = "sarvam" if opt == "O6" else "jev"
    if opt in ("W1", "W2", "W3"):  # warm-relay test: the tool reads the variant from net_probe
        init_vars["net_probe"] = "w3" if opt == "W3" else "w1"
    cfg = InteractionConfig(org_id=ORG, workspace_id=WS, app_id=app, version=1, interaction_type=InteractionType.CALL,
                            user_identifier_type=UserIdentifierType.CUSTOM,
                            user_identifier=f"cmp-{opt}-{scen}-{int(time.time())}-{idx}", sample_rate=SR,
                            agent_variables=init_vars)
    agent = AsyncSamvaadAgent(api_key=SecretStr(os.environ["SARVAM_AGENTS_API_KEY"]), config=cfg,
                              audio_callback=on_audio, transcript_callback=on_transcript)
    agent_box["a"] = agent
    orig = agent._route_message

    async def route(message):
        typ = message.get("type", "?")
        if typ != "server.media.audio_chunk":
            frames.append({"t": round(time.time() - t0, 3), "dir": "in", "type": typ,
                           "msg": {k: v for k, v in message.items() if k != "audio_base64"}})
        await orig(message)

    agent._route_message = route
    await agent.start()
    await agent.wait_for_connect(timeout=15)
    line = Line(agent)
    streamer = asyncio.create_task(line.run())

    async def wait_done(after, timeout=25, quiet=1.8):
        ts, first = time.time(), None
        while time.time() - ts < timeout and agent.is_connected():
            if state["last"] > after and first is None:
                first = state["last"]
            if first and time.time() - state["last"] > quiet:
                return first
            await asyncio.sleep(0.05)
        return first

    await wait_done(time.time() - 1, timeout=20)
    marks, ends = [time.time()], []
    for k, pcm in enumerate(audio):
        if not agent.is_connected():
            break
        if probe_plan and k in probe_plan:
            for p in probe_plan[k]:
                await push(p)
            await asyncio.sleep(1.0)
        line.speaking_until = 0
        line.queue.put_nowait(pcm)
        while line.speaking_until == 0 and agent.is_connected():
            await asyncio.sleep(0.02)
        ends.append(line.speaking_until)
        await wait_done(line.speaking_until)
        marks.append(time.time())
    await asyncio.sleep(1)
    iid = agent.get_interaction_id()
    if push_tasks:
        await asyncio.gather(*push_tasks, return_exceptions=True)
    await agent.stop()
    streamer.cancel()

    out = {"opt": opt, "app": app, "scen": scen, "run": idx, "interaction_id": iid, "turns": [],
           "ended_early": len(marks) - 1 < len(turns)}
    for k, (text, lang, sig) in enumerate(turns):
        if k + 1 >= len(marks):
            out["turns"].append({"seller": text, "signal": sig, "reply": "", "note": "call ended"})
            continue
        a, b = marks[k] + 0.3, marks[k + 1] + 0.3
        reply = " ".join(c for ts, r, c in events if "user" not in r.lower() and a <= ts < b)
        heard = [c for ts, r, c in events if "user" in r.lower() and a <= ts < b]
        on = [o for o in onsets if ends[k] - 0.5 <= o < b]
        ev = [f["type"] for f in frames if f["dir"] == "in" and a - t0 <= f["t"] < b - t0
              and f["type"] not in ("server.media.text_chunk", "server.event.transcription", "server.system.ping")]
        dec = [d for d in decisions if a <= d.get("t_heard", 0) < b]
        tr = {"seller": text, "signal": sig, "asr": heard, "reply": reply, "words": len(reply.split()),
              "reply_onset_s": round(on[0] - ends[k], 2) if on else None, "server_events": ev,
              "bursts_rel": [[round(b0 - ends[k], 2), round(b1 - ends[k], 2)] for b0, b1 in bursts if ends[k] - 0.5 <= b0 < b],
              "checks": {s: CHECKS[s](reply) for s in SIGNALS}}
        if dec:
            tr["jev"] = [{"utt": d["utt"], "jev_ms": d.get("jev_ms"), "scores": d.get("scores"), "lang": d.get("lang"),
                          "from": d.get("from"), "to": d.get("to"), "pushed": d.get("pushed"),
                          "push_ms_after_transcript": d.get("push_ms"),
                          "push_after_seller_end_s": round(d["t_push"] - ends[k], 2) if d.get("t_push") else None,
                          "push_before_reply_onset": (d["t_push"] < on[0]) if d.get("t_push") and on else None,
                          "transcript_after_seller_end_s": round(d["t_heard"] - ends[k], 2)} for d in dec]
        out["turns"].append(tr)
    for k, tr in enumerate(out["turns"]):  # was the signal applied on this turn or the next?
        s = tr["signal"]
        if s in CHECKS:
            tr["applied_same_turn"] = tr.get("checks", {}).get(s)
            nxt = out["turns"][k + 1] if k + 1 < len(out["turns"]) else None
            tr["applied_next_turn"] = nxt.get("checks", {}).get(s) if nxt and nxt.get("reply") else None
        elif s == "neutral":
            tr["false_switch_checks"] = [x for x, v in tr.get("checks", {}).items() if v and x not in ("interested",)]
    out["frames"] = [f for f in frames if f["type"] not in ("server.media.text_chunk",)]
    await asyncio.sleep(4)
    try:
        av, meta = analytics_vars(app, iid)
        out["agent_variables_after"] = av
        out["analytics_meta"] = {k: meta.get(k) for k in ("duration_in_seconds", "language_name", "num_messages")} if meta else None
    except Exception as e:
        out["analytics_err"] = str(e)[:200]
    return out


PROBE_PLAN = {  # before seller turn k, push these raw client actions
    1: [{"type": "client.action.variable_update",
         "agent_variables": {"call_plan": "STRICT FORMAT RULE: every reply must be exactly 5 words and end with 'ठीक है?'",
                             "seller_mode": "probe_var"}}],
    2: [{"type": "client.action.language_change", "language_name": "English"}],
    3: [{"type": "client.action.state_transition", "state_name": "start"}],
}
PROBE_TURNS = [OPENER, ("अच्छा, आगे बताइए क्या offer है?", "hi-IN", "after"), ("ठीक है, और क्या?", "hi-IN", "after"),
               ("हम्म, और कुछ?", "hi-IN", "after")]


async def main(opt, app, scens, runs):
    res = []
    if opt == "probe":
        SCEN["probe"] = PROBE_TURNS
        scens = ["probe"]
    for scen in scens:
        cache = OUT / f"tts-cache-{scen}.pcm.json"  # reuse seller audio across variants (saves TTS calls)
        if cache.exists():
            audio = [base64.b64decode(a) for a in json.loads(cache.read_text())]
        else:
            audio = [tts(t, lang) for t, lang, _ in SCEN[scen]]
            if scen == "MIN":
                cache.write_text(json.dumps([base64.b64encode(a).decode() for a in audio]))
        for i in range(runs):
            r = await run_call(opt, app, scen, i, audio, PROBE_PLAN if opt == "probe" else None)
            res.append(r)
            print(f"\n=== {opt} {scen} run {i} iid={r['interaction_id']}{' ENDED EARLY' if r['ended_early'] else ''}")
            for t in r["turns"]:
                j = t.get("jev") or []
                print(f"  [{t['signal']:>10}] same={t.get('applied_same_turn')} next={t.get('applied_next_turn')} "
                      f"fs={t.get('false_switch_checks')} onset={t.get('reply_onset_s')} ev={sorted(set(t.get('server_events', [])))}\n"
                      f"      jev={[(x['to'], x['pushed'], x['push_after_seller_end_s'], x['push_before_reply_onset']) for x in j]}\n"
                      f"      reply: {t['reply'][:160]}")
            av = r.get("agent_variables_after") or {}
            print("  vars:", {k: (str(v)[:300]) for k, v in av.items() if k in ("seller_mode", "persona_directive", "call_plan", "net_probe", "switch_log")})
            await asyncio.sleep(2)
    path = OUT / f"{opt}-{'_'.join(scens)[:60]}-{time.strftime('%Y%m%d-%H%M%S')}.json"
    path.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nSaved", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--opt", required=True)
    ap.add_argument("--app", default="VANI-midcal-506a41a2-0422")
    ap.add_argument("--scen", default="rushed,frustrated,confused,interested,gujarati,optout")
    ap.add_argument("--runs", type=int, default=1)
    a = ap.parse_args()
    asyncio.run(main(a.opt, a.app, a.scen.split(","), a.runs))
