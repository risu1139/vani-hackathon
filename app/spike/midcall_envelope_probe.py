"""T1 envelope probe: one short SDK voice session per client-action variant; records whether the server keeps the
session, echoes an event, or closes it (close code + reason). Usage: python app/spike/midcall_envelope_probe.py"""
import asyncio, json, os, sys, time
from pydantic import SecretStr
from sarvam_conv_ai_sdk import AsyncSamvaadAgent, InteractionConfig, InteractionType
from sarvam_conv_ai_sdk.messages.config import UserIdentifierType
from call_spike import ROOT, SR, Line

APP = sys.argv[1] if len(sys.argv) > 1 else "VANI-midcal-506a41a2-0422"
V = [
    ("var_agent_variables", {"type": "client.action.variable_update", "agent_variables": {"seller_mode": "rushed"}}),
    ("var_variables", {"type": "client.action.variable_update", "variables": {"seller_mode": "rushed"}}),
    ("var_name_value", {"type": "client.action.variable_update", "variable_name": "seller_mode", "value": "rushed"}),
    ("var_data", {"type": "client.action.variable_update", "data": {"seller_mode": "rushed"}}),
    ("lang_language_name", {"type": "client.action.language_change", "language_name": "English"}),
    ("lang_language", {"type": "client.action.language_change", "language": "English"}),
    ("state_state_name", {"type": "client.action.state_transition", "state_name": "start"}),
    ("state_next_state", {"type": "client.action.state_transition", "next_state": "start"}),
    ("control_text", {"type": "client.media.text", "text": "हाँ बोलिए"}),
]


async def one(name, payload):
    frames = []
    cfg = InteractionConfig(org_id=os.environ["SARVAM_ORG_ID"], workspace_id=os.environ["SARVAM_WORKSPACE_ID"], app_id=APP,
                            version=1, interaction_type=InteractionType.CALL, user_identifier_type=UserIdentifierType.CUSTOM,
                            user_identifier=f"env-{name}-{int(time.time())}", sample_rate=SR,
                            agent_variables={"seller_mode": "neutral", "persona_directive": "Continue normally."})
    async def noop(m): pass
    agent = AsyncSamvaadAgent(api_key=SecretStr(os.environ["SARVAM_AGENTS_API_KEY"]), config=cfg, audio_callback=noop)
    orig = agent._route_message
    async def route(m):
        if m.get("type") not in ("server.media.audio_chunk", "server.media.text_chunk", "server.system.ping"):
            frames.append({k: v for k, v in m.items() if k != "audio_base64"})
        await orig(m)
    agent._route_message = route
    await agent.start(); await agent.wait_for_connect(timeout=15)
    line = Line(agent); st = asyncio.create_task(line.run())
    await asyncio.sleep(6)
    ws = agent._ws
    n0 = len(frames)
    await ws.send(json.dumps({"origin": "client", "timestamp": time.time(), **payload}, ensure_ascii=False))
    t = time.time()
    while time.time() - t < 5 and agent.is_connected():
        await asyncio.sleep(0.1)
    alive = agent.is_connected()
    res = {"variant": name, "alive_after_5s": alive, "close_code": getattr(ws, "close_code", None),
           "close_reason": getattr(ws, "close_reason", None), "frames_after": [f.get("type") for f in frames[n0:]],
           "frames_after_full": frames[n0:][:5]}
    try:
        await agent.stop()
    except Exception:
        pass
    st.cancel()
    return res


async def main():
    out = []
    for name, p in V:
        r = await one(name, p)
        print(json.dumps({k: r[k] for k in ("variant", "alive_after_5s", "close_code", "close_reason", "frames_after")}, ensure_ascii=False))
        out.append(r)
        await asyncio.sleep(1)
    path = ROOT / "outputs" / "midcall_tests" / f"t1-envelopes-{time.strftime('%Y%m%d-%H%M%S')}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("saved", path)

asyncio.run(main())
