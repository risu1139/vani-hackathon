"""Smoke test (2026-10-10): does a compiled per-seller persona drive the Sarvam agent? TEXT sessions only (cheapest).

The clone still has the 11-variable prompt, so the new prompt_* sections are sent through its existing variables:
persona_style <- persona + style, division_block <- objective (hook), call_plan <- phases,
verified_facts <- facts, guardrails_extra <- environment + guardrails.

Checks: long variables render (replies use the hook / facts / objection answers), same-turn switch on a rushed line,
bot-question sidestep, agent_variables + switch_log read back from analytics.
Writes <run>/smoke_text.json (holds names: data/ only). Prints replies with names masked.

Usage: python app/spike/persona_text_smoke.py --run data/runs/e2e1-csd
"""
import argparse
import asyncio
import json
import os
import time
from datetime import datetime, timedelta, timezone

import requests
from pydantic import SecretStr
from sarvam_conv_ai_sdk import AsyncSamvaadAgent, InteractionConfig, InteractionType
from sarvam_conv_ai_sdk.messages.config import UserIdentifierType

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
for line in open(os.path.join(ROOT, ".env"), encoding="utf-8"):
    if "=" in line and not line.lstrip().startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
ORG, WS, KEY = os.environ["SARVAM_ORG_ID"], os.environ["SARVAM_WORKSPACE_ID"], os.environ["SARVAM_AGENTS_API_KEY"]
APP = "VANI-person-b8c173ff-b272"

SESSIONS = {  # Telugu seller lines; each session at most 3 seller turns
    "S1_hook_objection": ["అవును, చెప్పండి.", "Phone lone cheppandi, meeting enduku?", "సరే, రేపు సాయంత్రం 5 గంటలకు రండి."],
    "S2_rushed_bot": ["ఇప్పుడు బిజీగా ఉన్నాను, త్వరగా చెప్పండి.", "మీరు bot ఆ? మనిషేనా?"],
}


def legacy_vars(v):
    """Map the new section variables onto the clone's existing 11-variable prompt."""
    out = {k: x for k, x in v.items() if not k.startswith("prompt_")}
    out["persona_style"] = v["prompt_persona"] + "\n" + v["prompt_style"]
    out["division_block"] = v["prompt_objective"]
    out["call_plan"] = v["prompt_phases"]
    out["verified_facts"] = v["prompt_facts"]
    out["guardrails_extra"] = v["prompt_environment"] + "\n" + v["prompt_guardrails"]
    return out


async def session(name, lines, avars):
    replies, events = [], []
    got = asyncio.Event()

    async def on_text(msg):
        replies.append({"t": round(time.time() - t0, 2), "text": msg.text})
        got.set()

    async def on_event(ev):
        events.append(getattr(ev, "type", str(ev)))

    cfg = InteractionConfig(org_id=ORG, workspace_id=WS, app_id=APP, version=1, interaction_type=InteractionType.CHAT,
                            user_identifier_type=UserIdentifierType.CUSTOM, user_identifier=f"smoke-{name}-{int(time.time())}",
                            agent_variables=avars, sample_rate=16000)
    agent = AsyncSamvaadAgent(api_key=SecretStr(KEY), config=cfg, text_callback=on_text, event_callback=on_event,
                              base_url="https://apps.sarvam.ai/api/app-runtime/")
    t0 = time.time()
    await agent.start()
    if not await agent.wait_for_connect(timeout=10):
        return {"name": name, "error": "no connect"}
    iid = agent.get_interaction_id()
    turns = []

    async def settle(quiet=4.0, cap=25):
        end = time.time() + cap
        while time.time() < end:
            got.clear()
            try:
                await asyncio.wait_for(got.wait(), timeout=quiet)
            except asyncio.TimeoutError:
                return

    await settle()  # opening
    turns.append({"seller": None, "agent": [r["text"] for r in replies]})
    for line in lines:
        n = len(replies)
        ts = time.time()
        await agent.send_text(line)
        await settle()
        turns.append({"seller": line, "agent": [r["text"] for r in replies[n:]],
                      "first_reply_s": round(replies[n]["t"] - (ts - t0), 2) if len(replies) > n else None})
    await agent.stop()
    return {"name": name, "interaction_id": iid, "turns": turns, "events": sorted(set(events))}


def analytics(iid):
    now = datetime.now(timezone.utc)
    for _ in range(6):
        r = requests.get(f"https://apps.sarvam.ai/api/analytics/v1/{ORG}/{WS}/{APP}/interactions", timeout=20,
                         headers={"X-API-Key": KEY},
                         params={"start_datetime": (now - timedelta(hours=1)).isoformat(),
                                 "end_datetime": (now + timedelta(minutes=10)).isoformat(), "limit": 50})
        for it in r.json().get("items", []):
            if it.get("interaction_id") == iid:
                return it.get("agent_variables") or {}
        time.sleep(10)
    return None


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--run", required=True)
    a.add_argument("--only")
    p = a.parse_args()
    v = json.load(open(os.path.join(p.run, "05_sarvam_vars.json"), encoding="utf-8"))
    avars = legacy_vars(v)
    names = [v.get("seller_name"), v.get("company_name")]

    def mask(s):
        for n in names:
            if n:
                s = (s or "").replace(n, "<NAME>")
        return s
    out = []
    for name, lines in SESSIONS.items():
        if p.only and name != p.only:
            continue
        res = asyncio.run(session(name, lines, avars))
        res["agent_variables"] = analytics(res["interaction_id"]) if res.get("interaction_id") else None
        out.append(res)
        print(f"== {name} {res.get('interaction_id')} events={res.get('events')}")
        for t in res.get("turns", []):
            print("  SELLER:", t["seller"])
            for x in t["agent"]:
                print("  VANI  :", mask(x))
        av = res.get("agent_variables") or {}
        sent = {k: avars[k] for k in avars}
        print("  vars back:", "none" if av is None else f"{sum(1 for k in sent if k in av)}/{len(sent)} present,"
              f" equal={sum(1 for k in sent if str(av.get(k)) == str(sent[k]))}, seller_mode={av.get('seller_mode')}")
        print("  switch_log:", str(av.get("switch_log"))[:600])
    json.dump(out, open(os.path.join(p.run, "smoke_text.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
