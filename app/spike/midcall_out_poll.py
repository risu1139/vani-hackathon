"""Phone OUT half probe: during a live SDK voice session, poll the public analytics endpoints (transcripts/{id},
interactions list) every ~300 ms to see whether an in-progress interaction's transcript is visible from outside.
Usage: python app/spike/midcall_out_poll.py"""
import asyncio, json, os, time
from datetime import datetime, timedelta, timezone
import requests
from pydantic import SecretStr
from sarvam_conv_ai_sdk import AsyncSamvaadAgent, InteractionConfig, InteractionType
from sarvam_conv_ai_sdk.messages.config import UserIdentifierType
from call_spike import ROOT, SR, Line
from plan_stress import tts

APP = "VANI-midcal-506a41a2-0422"
ORG, WS = os.environ["SARVAM_ORG_ID"], os.environ["SARVAM_WORKSPACE_ID"]
H = {"X-API-Key": os.environ["SARVAM_AGENTS_API_KEY"]}
BASE = f"https://apps.sarvam.ai/api/analytics/v1/{ORG}/{WS}/{APP}"


def poll(iid):
    t = time.time()
    r1 = requests.get(f"{BASE}/transcripts/{iid}", headers=H, timeout=10)
    ms1 = round((time.time() - t) * 1000)
    now = datetime.now(timezone.utc)
    r2 = requests.get(f"{BASE}/interactions", headers=H, timeout=10, params={
        "start_datetime": (now - timedelta(minutes=15)).isoformat(), "end_datetime": (now + timedelta(minutes=2)).isoformat(), "limit": 50})
    ids = [i.get("interaction_id") for i in r2.json().get("items", [])] if r2.status_code == 200 else []
    return {"t": round(time.time(), 2), "transcript_status": r1.status_code, "transcript_ms": ms1, "transcript_body": r1.text[:200],
            "listed": iid in ids}


async def main():
    lines = ["हाँ जी बोलिए, कौन बोल रहा है?", "अच्छा, आगे बताइए क्या offer है?", "अभी बिज़ी हूँ यार, बाद में बात करते हैं"]
    audio = [tts(t, "hi-IN") for t in lines]
    sdk_user = []
    async def on_tr(m):
        if "user" in str(getattr(m.role, "value", m.role)).lower():
            sdk_user.append((time.time(), m.content))
    cfg = InteractionConfig(org_id=ORG, workspace_id=WS, app_id=APP, version=1, interaction_type=InteractionType.CALL,
                            user_identifier_type=UserIdentifierType.CUSTOM, user_identifier=f"outpoll-{int(time.time())}", sample_rate=SR)
    async def noop(m): pass
    agent = AsyncSamvaadAgent(api_key=SecretStr(os.environ["SARVAM_AGENTS_API_KEY"]), config=cfg, audio_callback=noop, transcript_callback=on_tr)
    await agent.start(); await agent.wait_for_connect(timeout=15)
    line = Line(agent); st = asyncio.create_task(line.run())
    await asyncio.sleep(8)
    iid = agent.get_interaction_id()
    rows = []
    for k, pcm in enumerate(audio):
        line.speaking_until = 0
        line.queue.put_nowait(pcm)
        tw = time.time()
        while line.speaking_until == 0 and agent.is_connected() and time.time() - tw < 20:
            await asyncio.sleep(0.02)
        if not agent.is_connected():
            print('disconnected at turn', k, flush=True); break
        t_end = line.speaking_until
        seen = None
        polls = 0
        while time.time() - t_end < 15:
            p_ = await asyncio.to_thread(poll, iid); polls += 1
            n_user = p_["transcript_body"].count('"role":"user"')
            try:
                full = requests.get(f"{BASE}/transcripts/{iid}", headers=H, timeout=10).json()["messages"]
                n_user = sum(1 for m in full if m["role"] == "user")
            except Exception:
                pass
            if n_user >= k + 1 and seen is None:
                seen = time.time()
                break
            await asyncio.sleep(0.3)
        sdk = [t for t, c in sdk_user]
        rows.append({"turn": k, "seller": lines[k], "poll_seen_after_end_s": round(seen - t_end, 2) if seen else None,
                     "sdk_callback_after_end_s": round(sdk[k] - t_end, 2) if len(sdk) > k else None, "polls": polls})
        print(rows[-1], flush=True)
        await asyncio.sleep(8)
    await agent.stop(); st.cancel()
    p = ROOT / "outputs" / "midcall_tests" / f"out-poll-timing-{time.strftime('%Y%m%d-%H%M%S')}.json"
    p.write_text(json.dumps({"interaction_id": iid, "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("saved", p)

asyncio.run(main())
