"""Test: can Sarvam's LLM use a SCRUBBER seller-context .md as the agent's context?

For each GLID: send data/contexts/<glid>.md to Sarvam chat completions and ask for a
persona plan (JSON) that cites catalogue IDs. Then check the plan:
  - JSON parses, required keys present
  - every cited ID exists in the catalogue and is filled for this seller (points.json)
  - latency, prompt / completion tokens
Key from env SARVAM_API_KEY (never written to disk). Output: data/contexts/sarvam_test/<glid>.json

Run: SARVAM_API_KEY=... python app/context/sarvam_context_test.py --glid G1 --glid G2 [--model sarvam-105b]
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "contexts"))
URL = "https://api.sarvam.ai/v1/chat/completions"

SYSTEM = """You are VANI's persona planner for IndiaMART outbound calls to sellers.
You receive one seller-context document. Use ONLY facts in it. Every choice must cite the data-point IDs
(e.g. B03, G03, D05) it is based on. Cite only IDs that appear as headings in the document.
If data is missing, say so and choose a safe default; never invent facts.
Section G is what VANI already knows from earlier calls: build on the last call, trust recent calls over older ones,
and never re-ask what was already answered. Do NOT decide call timing, retries or callbacks: scheduling is handled
by another agent.
Return ONLY a JSON object, no prose, with exactly these keys:
{
 "language": {"start": "...", "hinglish_mix": "low|medium|high", "reason": "...", "cites": ["..."]},
 "formality": {"level": "low|medium|high", "address_as": "...", "reason": "...", "cites": ["..."]},
 "pace": {"level": "slow|normal|fast", "reason": "...", "cites": ["..."]},
 "warmth_empathy": {"level": "low|medium|high", "reason": "...", "cites": ["..."]},
 "callee_check": {"ask_for_decision_maker_first": true, "reason": "...", "cites": ["..."]},
 "continue_from_last_call": {"what_was_discussed": "...", "do_not_reask": ["..."], "how_to_reference_it": "...", "cites": ["..."]},
 "opening_line": {"text_native_script": "...", "cites": ["..."]},
 "personalisation_hooks": [{"hook": "...", "cites": ["..."]}],
 "objection_playbook": [{"likely_objection": "...", "response": "...", "cites": ["..."]}],
 "escalation_and_guardrails": ["..."],
 "missing_data_noted": ["..."]
}"""

REQUIRED = ["language", "formality", "pace", "warmth_empathy", "callee_check", "continue_from_last_call", "opening_line",
            "personalisation_hooks", "objection_playbook"]


def ask(model, md, key, max_tokens, reasoning=None):
    # reasoning_effort must be sent as JSON null to switch reasoning off (else 105b spends the budget thinking)
    body = {"model": model, "temperature": 0.2, "max_tokens": max_tokens, "reasoning_effort": reasoning,
            "messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": "SELLER CONTEXT:\n\n" + md + "\n\nReturn the JSON persona plan now."}]}
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "api-subscription-key": key,
                                          "Authorization": f"Bearer {key}"})
    t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            code, text = r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        code, text = e.code, e.read().decode("utf-8", "replace")
    return code, text, round(time.time() - t, 1)


def extract_json(s):
    s = re.sub(r"<think>.*?</think>", "", s or "", flags=re.S).strip()
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", s, re.S)
    s = m.group(1) if m else s[s.find("{"): s.rfind("}") + 1]
    return json.loads(s)


def cites(o):
    out = []
    if isinstance(o, dict):
        for k, v in o.items():
            if k == "cites":  # model sometimes returns a list, sometimes a string like "['B03', 'G04']"
                out += re.findall(r"\b[A-K]\d{2}\b", v if isinstance(v, str) else " ".join(map(str, v)))
            else:
                out += cites(v)
    elif isinstance(o, list):
        for x in o:
            out += cites(x)
    return out


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--glid", action="append", required=True)
    a.add_argument("--model", default="sarvam-105b")
    a.add_argument("--max-tokens", type=int, default=3000)
    a.add_argument("--reasoning", choices=["low", "medium", "high"], default=None, help="default: off")
    p = a.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    key = os.environ.get("SARVAM_API_KEY")
    if not key:
        sys.exit("set SARVAM_API_KEY")
    os.makedirs(os.path.join(ROOT, "sarvam_test"), exist_ok=True)
    for g in [x.strip() for x in p.glid]:
        md = open(os.path.join(ROOT, f"{g}.md"), encoding="utf-8").read()
        points = json.load(open(os.path.join(ROOT, f"{g}.points.json"), encoding="utf-8"))
        filled = {k for k, v in points.items() if v["value"] not in (None, "", [], {})}
        code, text, sec = ask(p.model, md, key, p.max_tokens, p.reasoning)
        rec = {"glid": g, "model": p.model, "reasoning": p.reasoning, "http": code, "latency_sec": sec, "md_chars": len(md)}
        try:
            resp = json.loads(text)
            rec["usage"] = resp.get("usage")
            content = resp["choices"][0]["message"]["content"]
            rec["finish_reason"] = resp["choices"][0].get("finish_reason")
            plan = extract_json(content)
            c = cites(plan)
            ids = [x.strip().upper() for x in c]
            rec.update({"plan": plan, "json_ok": True,
                        "missing_keys": [k for k in REQUIRED if k not in plan],
                        "cited_ids": sorted(set(ids)),
                        "cited_unknown": sorted({x for x in ids if x not in points}),
                        "cited_but_empty": sorted({x for x in ids if x in points and x not in filled})})
        except Exception as e:
            rec.update({"json_ok": False, "error": f"{type(e).__name__}: {e}", "raw": text[:3000]})
        with open(os.path.join(ROOT, "sarvam_test", f"{g}.json"), "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, indent=1)
        print(json.dumps({k: rec.get(k) for k in ("glid", "model", "http", "latency_sec", "md_chars", "usage", "finish_reason",
                                                  "json_ok", "missing_keys", "cited_ids", "cited_unknown", "cited_but_empty", "error")},
                         ensure_ascii=False))


if __name__ == "__main__":
    main()
