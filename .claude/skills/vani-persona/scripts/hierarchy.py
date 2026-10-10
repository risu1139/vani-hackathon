"""hierarchy.py: the ONE place that turns references/hierarchy.json into scoreboard keys.

prior.py (reads cells) and loop2_update.py (writes cells) both import this module, so the keys they use cannot drift:
no level list lives in either script. Nothing here reads a scoreboard or a seller file by itself.

Persona keys (nested, one chain): L0 'all' -> L1 'div=NSD' -> L2 'div=NSD|band=..' -> L3 '..|aov=..' -> L4 '..|zone=..' -> L5 '..|state=..'.
L6 (category group) is a branch under L1: 'div=NSD|catgroup=..'. A level whose value is unknown is skipped
(that level is skipped: no part is added to the key; deeper known levels still count).
Voice keys: 'all' plus '<key>=<value>' for each voice level (flat offsets; the Hindi belt is one of them, so it is learned).
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
HIER = os.path.join(HERE, "..", "references", "hierarchy.json")
UNKNOWN = (None, "", "unknown", "None")


def load(path=None):
    return json.load(open(path or HIER, encoding="utf-8"))


# ---------------------------------------------------------------- reading seller facts
def _dig(obj, name):
    """Value of 'a.b.c' inside nested dicts; a bare name is searched anywhere (first match)."""
    if "." in name:
        for part in name.split("."):
            obj = obj.get(part) if isinstance(obj, dict) else None
        return obj
    if isinstance(obj, dict):
        if name in obj:
            return obj[name]
        for v in obj.values():
            r = _dig(v, name)
            if r is not None:
                return r
    return None


def fact_value(fact, facts_by_id, points):
    """Resolve {'id': 'trait.city_tier', 'field': 'detail.state'} against facts.json (traits/states) or context.json points."""
    if not fact:
        return None
    fid, field = fact.get("id"), fact.get("field") or "value"
    if fid in facts_by_id:
        return _dig(facts_by_id[fid], field)
    pt = (points or {}).get(fid) or {}
    return _dig(pt.get("value"), field)


def zone_of(h, state):
    s = (state or "").strip().lower()
    for zone, states in h["state_to_zone"].items():
        if s in states:
            return zone
    return "Other"


def division_of(raw):
    return raw if raw in ("NSD", "CSD") else ("CSD" if raw in ("TMW", "KCD") else "NSD")


def resolve_path(h, facts_by_id, points):
    """{path_key: value} for every persona level, e.g. {'division': 'NSD', 'band': '0 - 40 L', ..., 'state': 'telangana'}."""
    path = {}
    for lv in h["persona_levels"]:
        if lv["id"] == "L0":
            continue
        raw = fact_value(lv.get("fact"), facts_by_id, points)
        if lv["id"] == "L1":
            v = division_of(raw)
        elif lv["id"] == "L2":
            v = (lv.get("map") or {}).get(raw, raw)
        elif lv["id"] == "L4":
            v = zone_of(h, fact_value(lv["fact"], facts_by_id, points))
        elif lv["id"] == "L5":
            v = (str(raw).strip().lower() if raw not in UNKNOWN else None)
        else:
            v = raw
        path[lv["path_key"]] = "unknown" if v in UNKNOWN else str(v)
    return path


# ---------------------------------------------------------------- keys
def chain(h, path):
    """[(level_id, cell_key)] along the nested chain L0..L5; a level with an unknown value is skipped."""
    out, key = [("L0", "all")], None
    for lv in h["persona_levels"]:
        if lv["id"] in ("L0", "L6"):
            continue
        v = path.get(lv["path_key"], "unknown")
        if v in UNKNOWN:
            continue                                   # an unknown level is skipped; deeper known levels still count
        part = f"{lv['key']}={v}"
        key = part if key is None else f"{key}|{part}"
        out.append((lv["id"], key))
    return out


def branch_keys(h, path):
    """Levels that hang under a parent other than the previous level (L6 under L1): [(level_id, cell_key)]."""
    out = []
    ch = dict(chain(h, path))
    for lv in h["persona_levels"]:
        if lv["id"] == "L6":
            v = path.get(lv["path_key"], "unknown")
            parent = ch.get(lv["parent"])
            if v not in UNKNOWN and parent:
                out.append((lv["id"], f"{parent}|{lv['key']}={v}"))
    return out


def persona_keys(h, path):
    """Every persona cell key the seller's path touches (what loop2 writes and what prior reads)."""
    return [k for _, k in chain(h, path)] + [k for _, k in branch_keys(h, path)]


def voice_keys(h, vin):
    return ["all"] + [f"{lv['key']}={vin.get(lv['key'])}" for lv in h["voice_levels"] if lv["id"] != "V0"]


# ---------------------------------------------------------------- value groups
def group_of(h, field, value):
    """The value group a final value falls in ('0.85-0.95', 'medium', 'F' ...), or None."""
    groups = (h["fields"].get(field) or {}).get("value_groups")
    if not isinstance(groups, list) or value in (None, ""):
        return None
    for g in groups:
        if str(g).lower() == str(value).lower():
            return g
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    best, best_d = None, None
    for g in groups:
        m = re.match(r"^(-?\d+(?:\.\d+)?)(?:\.\.|-)(-?\d+(?:\.\d+)?)$", str(g))
        if not m:
            continue
        lo, hi = float(m.group(1)), float(m.group(2))
        d = 0.0 if lo <= v <= hi else min(abs(v - lo), abs(v - hi))
        if best_d is None or d < best_d:
            best, best_d = g, d
    return best


def learned_fields(h):
    """Fields whose value groups are counted: reason required and a list of groups (voice_id, hook, opening, free text excluded)."""
    return [f for f, c in h["fields"].items() if c.get("reason_required") and isinstance(c.get("value_groups"), list)]
