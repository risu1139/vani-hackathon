"""Score midcall_compare runs: option x signal table, tool-call stats from switch_log, latency.

Usage: python app/spike/midcall_analyze.py outputs/midcall_tests/O1-*.json [more files] [--label O1]
Writes <first-file-stem>-scored.json next to the input and prints the tables.
"""
import argparse
import glob
import json
import os
import re
import statistics
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import requests

import call_spike  # noqa: F401  (.env)
from midcall_compare import CHECKS

ORG, WS = os.environ["SARVAM_ORG_ID"], os.environ["SARVAM_WORKSPACE_ID"]
NEUTRAL_FALSE = ("frustrated", "opt_out", "confused")  # adaptation markers that should not appear on a neutral turn


def dedupe(reply):
    """Cut a restarted reply where its opening words repeat, then drop repeated sentences, so checks judge
    the intended reply. Returns (clean_reply, restarted?)."""
    w = reply.split()
    cut = False
    if len(w) >= 6:
        head = [re.sub(r"\W+", "", x) for x in w[:3]]
        for j in range(3, len(w) - 2):
            if [re.sub(r"\W+", "", x) for x in w[j:j + 3]] == head:
                reply, cut = " ".join(w[:j]), True
                break
    parts = [p.strip() for p in re.split(r"(?<=[।?!.])\s+", reply) if p.strip()]
    seen, out = set(), []
    for p in parts:
        k = re.sub(r"\W+", "", p.lower())
        if k in seen:
            continue
        seen.add(k)
        out.append(p)
    return " ".join(out), cut or len(out) < len(parts)


def fetch_vars(app, iids):
    now = datetime.now(timezone.utc)
    out, offset = {}, 0
    while True:
        r = requests.get(f"https://apps.sarvam.ai/api/analytics/v1/{ORG}/{WS}/{app}/interactions", timeout=30,
                         headers={"X-API-Key": os.environ["SARVAM_AGENTS_API_KEY"]},
                         params={"start_datetime": (now - timedelta(hours=6)).isoformat(),
                                 "end_datetime": (now + timedelta(minutes=5)).isoformat(), "limit": 100, "offset": offset})
        items = r.json().get("items", [])
        for it in items:
            if it.get("interaction_id") in iids:
                out[it["interaction_id"]] = dict(it.get("agent_variables") or {},
                                                 _avg_agent_rt=it.get("average_agent_response_time_in_seconds"))
        if len(items) < 100:
            return out
        offset += 100


def fill_from_transcript(app, run):
    """Calls the agent ends (opt-out) close the socket before the SDK delivers the last bot transcript; take it from
    the analytics transcript instead."""
    turns = run["turns"]
    if not any(not t.get("reply") and t.get("asr") for t in turns):
        return
    r = requests.get(f"https://apps.sarvam.ai/api/analytics/v1/{ORG}/{WS}/{app}/transcripts/{run['interaction_id']}",
                     headers={"X-API-Key": os.environ["SARVAM_AGENTS_API_KEY"]}, timeout=30)
    msgs = r.json().get("messages", []) if r.status_code == 200 else []
    for t in turns:
        if t.get("reply") or not t.get("asr"):
            continue
        a = norm(t["asr"][-1])
        idx = [i for i, m in enumerate(msgs) if m["role"] == "user" and norm(m["content"]) == a]
        if idx:
            out = []
            for m in msgs[idx[-1] + 1:]:
                if m["role"] == "user":
                    break
                out.append(m["content"])
            t["reply"] = " ".join(out)
            t["reply_from_transcript"] = True


def norm(s):
    return re.sub(r"[\W_]+", "", (s or "").lower())


def match_turn(utt, turns):
    """Index of the turn whose ASR text best matches a switch_log utterance."""
    u = norm(utt)
    best, score = None, 0
    for i, t in enumerate(turns):
        for a in t.get("asr") or []:
            a = norm(a)
            if not a or not u:
                continue
            common = len(set(u[k:k + 3] for k in range(len(u) - 2)) & set(a[k:k + 3] for k in range(len(a) - 2)))
            sc = common / max(1, min(len(u), len(a)) - 2)
            if sc > score:
                best, score = i, sc
    return best if score >= 0.5 else None


def main(files, label):
    runs = []
    for f in files:
        runs += json.load(open(f, encoding="utf-8"))
    by_app = defaultdict(set)
    for r in runs:
        if r.get("interaction_id"):
            by_app[r["app"]].add(r["interaction_id"])
    avs = {}
    if not os.environ.get("MIDCALL_OFFLINE"):  # offline = score from local files only (no Sarvam API calls)
        for app, ids in by_app.items():
            avs.update(fetch_vars(app, ids))
    table = defaultdict(lambda: {"n": 0, "same": 0, "next": 0, "either": 0, "replies": []})
    neutral = {"n": 0, "false": 0, "examples": []}
    onsets, tool_stats = [], {"turns": 0, "calls": 0, "dups": 0, "missed": 0, "double": 0, "wrong_mode": 0, "mode_checked": 0,
                              "relay_ms": [], "relay_err": 0, "relay_used": 0, "conn_new": 0,
                  "relay_called": 0, "relay_timeouts": 0, "rows": 0, "ms_new": [], "ms_reused": []}
    restarts, nturns = 0, 0
    server_rt = []
    per_run = []
    for r in runs:
        av = avs.get(r.get("interaction_id"), {})
        if av.get("_avg_agent_rt"):
            server_rt.append(av["_avg_agent_rt"])
        try:
            log = json.loads(av.get("switch_log") or "[]")
        except Exception:
            log = []
        turns = r["turns"]
        if not os.environ.get("MIDCALL_OFFLINE"):
            try:
                fill_from_transcript(r["app"], r)
            except Exception:
                pass
        for t in turns:
            t["reply_dd"], t["restarted"] = dedupe(t.get("reply") or "")
            t["checks_dd"] = {s: CHECKS[s](t["reply_dd"]) for s in CHECKS} if t.get("reply") else {}
        rows_by_turn = defaultdict(list)
        for row in log if isinstance(log, list) else []:
            k = match_turn(row.get("utt"), turns)
            if k is not None:
                rows_by_turn[k].append(row)
        for k, t in enumerate(turns):
            if not t.get("reply"):
                continue
            nturns += 1
            restarts += t["restarted"]
            if t.get("reply_onset_s") is not None and 0 < t["reply_onset_s"] < 15:
                onsets.append(t["reply_onset_s"])
            sig = t["signal"]
            rows = rows_by_turn.get(k, [])
            if log:
                tool_stats["turns"] += 1
                tool_stats["calls"] += len(rows)
                tool_stats["dups"] += sum(1 for x in rows if x.get("dup"))
                tool_stats["missed"] += not rows
                tool_stats["double"] += len(rows) > 1
                for x in rows:
                    if x.get("dup"):
                        continue
                    tool_stats["rows"] += 1
                    tool_stats["relay_called"] += bool(x.get("relay_called", "relay_ms" in x))
                    tool_stats["relay_timeouts"] += x.get("relay_err") == "timeout"
                    if "relay_ms" in x:
                        (tool_stats["ms_new"] if x.get("conn_new") else tool_stats["ms_reused"]).append(x["relay_ms"])
                    if "relay_ms" in x:
                        tool_stats["relay_ms"].append(x["relay_ms"])
                        tool_stats["relay_err"] += bool(x.get("relay_err"))
                        tool_stats["relay_used"] += x.get("relay_mode") is not None and not x.get("relay_err")
                        tool_stats["conn_new"] += bool(x.get("conn_new"))
                want = {"gujarati": None, "after": None, "after_gu": None}.get(sig, sig)
                if want and rows:
                    got = [x.get("to") for x in rows if not x.get("dup")] or [rows[-1].get("to")]
                    tool_stats["mode_checked"] += 1
                    tool_stats["wrong_mode"] += got[-1] != want
                t["tool_rows"] = rows
            if sig in CHECKS:
                same = t["checks_dd"].get(sig)
                nxt = turns[k + 1] if k + 1 < len(turns) else None
                nx = nxt["checks_dd"].get(sig) if nxt and nxt.get("reply") else None
                c = table[sig]
                c["n"] += 1
                c["same"] += bool(same)
                c["next"] += bool(nx) and not same
                c["either"] += bool(same or nx)
                c["replies"].append(t["reply_dd"][:140])
            elif sig == "neutral":
                neutral["n"] += 1
                bad = [s for s in NEUTRAL_FALSE if t["checks_dd"].get(s)]
                if bad:
                    neutral["false"] += 1
                    neutral["examples"].append((t["seller"][:40], bad, t["reply_dd"][:100]))
        per_run.append({"scen": r["scen"], "run": r["run"], "iid": r.get("interaction_id"), "switch_log": log,
                        "turns": [{k2: t.get(k2) for k2 in ("seller", "signal", "asr", "reply_dd", "restarted", "reply_onset_s",
                                                             "checks_dd", "jev", "tool_rows")} for t in turns]})
    summary = {
        "label": label, "files": files, "calls": len(runs), "turns": nturns,
        "signals": {s: {k: v for k, v in c.items() if k != "replies"} for s, c in table.items()},
        "neutral_false_switch": f"{neutral['false']}/{neutral['n']}", "neutral_examples": neutral["examples"],
        "reply_onset_median_s": round(statistics.median(onsets), 2) if onsets else None,
        "reply_onset_p90_s": round(sorted(onsets)[int(0.9 * (len(onsets) - 1))], 2) if onsets else None,
        "reply_onset_p95_s": round(sorted(onsets)[int(0.95 * (len(onsets) - 1))], 2) if onsets else None,
        "restarted_replies": f"{restarts}/{nturns}",
        "server_avg_agent_response_s_median": round(statistics.median(server_rt), 2) if server_rt else None,
        "tool": {**{k: v for k, v in tool_stats.items() if k not in ("relay_ms", "ms_new", "ms_reused")},
                 "relay_ms_p95": sorted(tool_stats["relay_ms"])[int(0.95 * (len(tool_stats["relay_ms"]) - 1))] if tool_stats["relay_ms"] else None,
                 "relay_ms_newconn_median": statistics.median(tool_stats["ms_new"]) if tool_stats["ms_new"] else None,
                 "relay_ms_reused_median": statistics.median(tool_stats["ms_reused"]) if tool_stats["ms_reused"] else None,
                 "n_newconn": len(tool_stats["ms_new"]), "n_reused": len(tool_stats["ms_reused"]),
                 "relay_ms_median": statistics.median(tool_stats["relay_ms"]) if tool_stats["relay_ms"] else None,
                 "relay_ms_max": max(tool_stats["relay_ms"]) if tool_stats["relay_ms"] else None},
    }
    print(json.dumps({k: v for k, v in summary.items() if k != "files"}, ensure_ascii=False, indent=1))
    for s, c in table.items():
        print(f"--- {s}: same {c['same']}/{c['n']}, next-only {c['next']}, either {c['either']}")
        for x in c["replies"]:
            print("     ", x)
    out = files[0].replace(".json", f"-scored-{label}.json")
    json.dump({"summary": summary, "runs": per_run}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("saved", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--label", default="run")
    a = ap.parse_args()
    files = [g for f in a.files for g in sorted(glob.glob(f)) if "-scored" not in g]
    main(files, a.label)
