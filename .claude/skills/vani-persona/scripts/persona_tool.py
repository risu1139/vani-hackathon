"""persona_tool.py: the ONLY way the persona is written (enforcement plan §5a, reviewed and approved 2026-10-10).

The agent keeps the judgement (which value, which evidence). This script makes the order and the format mechanical,
and checks every decision at write time. The agent never writes 04_persona.json or 02_review.json itself (the
PreToolUse gate denies it; a Bash bypass is caught after the turn by the sha check and the validator).

Commands (all need $VANI_RUN; run them with "$VANI_PY" <skill>/scripts/persona_tool.py ...):
  status                                  what is done, what is left (start here)
  select --persona P2 --reason "..."      choose 1 of the top-2 personas in 03_prior.json (the base)
  probe  --field pace | --hook <id>       search that field's / hook's probe sections; hits ranked by the script
  decide --field pace --value 1.05 --type seller_evidence --reason "..." --cite <id> --quote "..." [--cite --quote]...
         --type hierarchy     --level L4 --group 0.95-1.05 --searched "..." --answer <hit id>="why not" (top-3 hits)
         --type start_persona --searched "..." --answer <hit id>="why not" (top-3 hits; the value = the card's value)
  hook   --id hook.money_lead --decision primary|backup|rejected --reason "..." [--cite --quote]...
         [--counter "..." --counter-cite <id> --counter-quote "..."]
  text   --file <run>/draft_text.json        the spoken parts (see references/formats/persona.json "text")
  finalize                                writes 02_review.json + 04_persona.json, runs the validator, logs the sha

Hit ranking (top-3), stated so it can be checked: score = number of distinct search terms on the line; ties go to the
newer call file, then to the order of probe_files, then to the line number. Section hits (core.md#B03 ...) have no
date, so with the same score they rank AFTER every dated call hit: what the seller did on a call outranks profile text.

Trust: the ledger is agent-writable through Bash. The finalize sha means "the tool was used", not a security
boundary; the validator re-checks every content rule from 04/02 + the frozen inputs. Parity is a rule: any
write-time check that matters must also be in validate_persona.py.
"""
import argparse
import datetime
import glob
import hashlib
import json
import os
import re
import sys
import time
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.abspath(os.path.join(HERE, "..", "references"))
CALL_DAYS = 90
SPECIAL = {"hook", "opening"}            # hook: the hook command; opening: the text file
TEXT_KEYS = {"personalisation", "hook", "opening", "identity_line", "call_plan", "objection_playbook", "escalation_rules",
             "guardrails", "verified_facts", "switch_sensitivity", "guards_ack", "new_persona_suggestion",
             "overall_confidence", "completeness", "traits_states_review"}
GRADE = {"seller_evidence": "SELLER", "hierarchy": "WEAK", "start_persona": "GUESS"}
CONF = {"seller_evidence": 0.7, "hierarchy": 0.5, "start_persona": 0.3}
MAX_SHOW = 12


# ---------------------------------------------------------------- shared helpers (the validator imports these)
def load_hierarchy():
    p = os.environ.get("VANI_HIERARCHY") or os.path.join(REF, "hierarchy.json")
    if p == "none" or not os.path.exists(p):
        return None
    return json.load(open(p, encoding="utf-8"))


def decide_fields(h):
    """Fields the agent must decide with this tool (reason required, list of probe sections, not hook/opening)."""
    return [f for f, s in (h.get("fields") or {}).items()
            if s.get("reason_required") and isinstance(s.get("probe_files"), list) and f not in SPECIAL]


def nq(t):
    """Normalise text for quote matching: NFC, casefold, straight quotes, plain dashes and ellipsis, no zero-width
    characters, no markdown emphasis (* _ `), one space, no line breaks."""
    t = unicodedata.normalize("NFC", t or "").casefold()
    t = t.replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')
    t = re.sub("[‐‑‒–—−]", "-", t).replace("…", "...")
    t = re.sub("[​‌‍﻿]", "", t)
    t = re.sub(r"[*_`]", "", t)
    return re.sub(r"\s+", " ", t).strip()


MIN_WORDS, MIN_CHARS = 4, 15


def span_lines(folder, cite):
    """The lines a cite points at (review fix 1): '<cite>:L<n>' = that line; 'calls/Cnn#Cnn.Tk' = that turn (to the
    next turn); 'file#SEC' = that section; another '#ID' = from the line with the id to the next heading;
    'calls/Cnn#Cnn' = the whole call file. Returns (path, [(line_no, text)]) or (None, [])."""
    m = re.match(r"^(.*):L(\d+)$", cite or "")
    base, line = (m.group(1), int(m.group(2))) if m else (cite or "", None)
    f = file_for(folder, base)
    if not f:
        return None, []
    lines = list(enumerate(read(f).splitlines(), 1))
    if line is not None:
        return f, [x for x in lines if x[0] == line]
    anchor = base.split("#", 1)[1] if "#" in base else None
    if not anchor:
        return f, lines
    tm = re.match(r"^(C\d+)\.T\d+$", anchor)
    if tm:
        out, on = [], False
        for ln, t in lines:
            if re.search(rf"\b{re.escape(anchor)}\b", t):
                on = True
            elif on and re.search(rf"\b{tm.group(1)}\.T\d+\b", t):
                break
            if on:
                out.append((ln, t))
        return f, out
    if base.startswith("calls/") and re.fullmatch(r"C\d+", anchor):
        return f, lines
    sec = section_lines(f, anchor)
    if sec:
        return f, sec
    out, on = [], False
    for ln, t in lines:
        if not on and anchor in t:
            on = True
        elif on and re.match(r"^#{1,6}\s", t):
            break
        if on:
            out.append((ln, t))
    return f, out


def read(path):
    return open(path, encoding="utf-8", errors="replace").read()


def file_for(folder, cite):
    path = cite.split("#")[0]
    if path.startswith("calls/") and not path.endswith(".md"):
        m = glob.glob(os.path.join(folder, "calls", os.path.basename(path) + "_*.md"))
        return m[0] if m else None
    p = os.path.join(folder, path)
    return p if os.path.isfile(p) else None


def quote_ok(folder, cite, quote, strict=True):
    """'' if the quote is inside the span the cite points at, else the problem. strict (hierarchy mode): the quote has
    >= 4 words (or >= 15 characters in an Indic script) unless it is a whole line of the span (review fix 2).
    strict=False keeps the earlier whole-file rule for the pre-hierarchy tests."""
    f, span = span_lines(folder, cite or "")
    if not f:
        return f"cite '{cite}' does not exist in the seller folder"
    if not quote:
        return f"cite '{cite}' has no quote"
    if len(quote.split()) > 20:
        return f"cite '{cite}': quote is longer than 20 words"
    if not strict:
        text = read(f)
        anchor = cite.split(":L")[0].split("#", 1)[1] if "#" in cite else None
        if anchor and anchor not in text:
            return f"cite '{cite}': id '{anchor}' not found in {os.path.basename(f)}"
        return "" if nq(quote) in nq(text) else f"cite '{cite}': quote not found in {os.path.basename(f)} (copy the words exactly)"
    if not span:
        return f"cite '{cite}': the id was not found in {os.path.basename(f)}"
    if nq(quote) not in nq("\n".join(t for _, t in span)):
        return f"cite '{cite}': quote not found in that turn/section/line (copy the words exactly from the cited place)"
    q = nq(quote)
    whole_line = any(nq(t).strip(" -:") == q.strip(" -:") for _, t in span)
    if not whole_line and len(q.split()) < MIN_WORDS and (q.isascii() or len(q) < MIN_CHARS):
        return f"cite '{cite}': quote too short (at least {MIN_WORDS} words, or a whole line)"
    return ""


def quote_in_hit(quote, hits, cites):
    """seller_evidence: the quote must sit on a line the field's search hit (review fix 1)."""
    q = nq(quote)
    return any(q in nq(x.get("full") or x["text"]) for x in hits if x["cite"] in cites or x["id"] in cites)


def section_lines(path, section):
    if not os.path.isfile(path):
        return []
    out, level = [], None
    for i, ln in enumerate(read(path).splitlines(), 1):
        m = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if m:
            if level is not None and len(m.group(1)) <= level:
                break
            first = re.split(r"[\s:]", m.group(2).strip(), maxsplit=1)[0]
            if level is None and first == section:
                level = len(m.group(1))
                continue
        if level is not None:
            out.append((i, ln))
    return out


def _date(name):
    m = re.search(r"(\d{4}-\d{2}-\d{2})", name)
    return datetime.date.fromisoformat(m.group(1)) if m else None


def sources(folder, spec, as_of):
    out = []
    for pf in spec.get("probe_files") or []:
        if pf.rstrip("/") == "calls":
            for f in sorted(glob.glob(os.path.join(folder, "calls", "*.md"))):
                d = _date(os.path.basename(f))
                if d and (as_of - d).days > CALL_DAYS:
                    continue
                cid = os.path.basename(f).split("_")[0]
                out.append(("calls", f"calls/{cid}", d, list(enumerate(read(f).splitlines(), 1))))
        elif "#" in pf:
            fn, sec = pf.split("#", 1)
            out.append(("section", pf, None, section_lines(os.path.join(folder, fn), sec)))
    return out


def _term_re(t):
    if t.startswith("re:"):
        return re.compile(t[3:], re.I)
    t = unicodedata.normalize("NFC", t).casefold()
    return re.compile(r"(?<![a-z0-9])" + re.escape(t) + r"(?![a-z0-9])" if t.isascii() else re.escape(t), re.I)


def search(folder, spec, as_of):
    """Deterministic, ranked hits: [{id, cite, line, terms, score, text}], best first (see the module doc)."""
    pats = [(t, _term_re(t)) for t in spec.get("search_terms") or []]
    hits = []
    for order, (kind, base, d, lines) in enumerate(sources(folder, spec, as_of)):
        for ln, text in lines:
            low = unicodedata.normalize("NFC", text).casefold()
            matched = [t for t, rx in pats if rx.search(low)]
            if not matched:
                continue
            if kind == "calls":
                tid = re.search(r"\b(C\d+\.T\d+)\b", text)
                cite = f"{base}#{tid.group(1) if tid else base.split('/')[1]}"
            else:
                cite = base
            hits.append({"id": f"{cite}:L{ln}", "cite": cite, "line": ln, "terms": matched, "score": len(matched),
                         "text": text.strip()[:200], "full": text.strip(), "_rank": (-len(matched), -(d.toordinal() if d else 0), order, ln)})
    hits.sort(key=lambda x: x.pop("_rank"))
    return hits


# Start values for fields the cards do not define (review fix 3: start_persona never accepts a free value).
# voice_gender starts from the voice scoreboard's draw (03_prior.json voice.chosen); the rest from VANI's current default.
START_DEFAULTS = {"language_start": "HINDI", "empathy": "plain courtesy: thank the seller for their time"}


def start_value(field, card, prior_doc):
    """The value a start_persona decision must keep, or None if there is none."""
    if field in (card or {}):
        return card[field]
    if field == "voice_gender":
        v = ((prior_doc or {}).get("voice") or {}).get("chosen")
        return {"female": "F", "male": "M"}.get(str(v).lower(), v)
    return START_DEFAULTS.get(field)


def card_of(persona_id):
    lib = json.load(open(os.path.join(REF, "persona_library.json"), encoding="utf-8"))
    return next((c for c in lib.get("personas", []) if c.get("id") == persona_id), None)


def parse_group(g):
    m = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*(?:\.\.|-)\s*(-?\d+(?:\.\d+)?)\s*$", str(g))
    return (float(m.group(1)), float(m.group(2))) if m else None


def group_of(spec, value):
    """The value group a value falls in, or None."""
    groups = spec.get("value_groups")
    if not isinstance(groups, list):
        return None
    for g in groups:
        rg = parse_group(g)
        if rg and isinstance(value, (int, float)) and rg[0] - 1e-9 <= value <= rg[1] + 1e-9:
            return g
        if not rg and value == g:
            return g
    return None


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest() if os.path.exists(path) else None


# ---------------------------------------------------------------- run state
def run_dir():
    r = os.environ.get("VANI_RUN")
    if not r or not os.path.isfile(os.path.join(r, "turn.json")):
        sys.exit("persona_tool: $VANI_RUN with turn.json is required (the launcher sets it)")
    return r


def turn(run):
    return json.load(open(os.path.join(run, "turn.json"), encoding="utf-8"))


def as_of(run):
    try:
        return datetime.date.fromisoformat(turn(run)["as_of"])
    except (KeyError, ValueError, OSError):
        return datetime.date.today()


def ledger(run):
    p = os.path.join(run, "ledger.jsonl")
    rows = []
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            try:
                rows.append(json.loads(line))
            except ValueError:
                pass
    return rows


def log(run, row):
    row["t"] = round(time.time(), 2)
    with open(os.path.join(run, "ledger.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def last(rows, kind, key=None, val=None):
    for r in reversed(rows):
        if r.get("kind") == kind and (key is None or r.get(key) == val):
            return r
    return None


def prior(run):
    return json.load(open(os.path.join(run, "03_prior.json"), encoding="utf-8"))


def facts(run):
    return json.load(open(os.path.join(run, "01_facts.json"), encoding="utf-8"))


def refuse(problems, fixes=None):
    print("REFUSED (" + str(len(problems)) + "):")
    for p in problems[:6]:
        print("- " + p)
    if len(problems) > 6:
        print(f"- ... and {len(problems) - 6} more")
    for f in fixes or []:
        print("FIX: " + f)
    sys.exit(1)


def tool_cmd():
    return f"\"$VANI_PY\" {os.path.abspath(__file__)}"


# ---------------------------------------------------------------- commands
def cmd_status(a, run, h):
    rows = ledger(run)
    sel = last(rows, "select")
    print(f"selected persona: {sel['persona'] if sel else 'NOT YET (select --persona, from ' + str(prior(run)['persona']['top2']) + ')'}")
    for f in decide_fields(h):
        pr, de = last(rows, "probe", "target", f"field:{f}"), last(rows, "decide", "field", f)
        print(f"  field {f:15s} probe={'yes' if pr else 'NO'} decision={(de['type'] + ' ' + str(de['value'])) if de else 'NO'}")
    for hid in facts(run).get("eligible_hooks", []):
        pr, de = last(rows, "probe", "target", f"hook:{hid}"), last(rows, "hook", "id", hid)
        print(f"  hook  {hid:24s} probe={'yes' if pr else 'NO'} decision={de['decision'] if de else 'NO'}")
    print(f"text: {'yes' if last(rows, 'text') else 'NO'}   finalized: {'yes' if last(rows, 'finalize') else 'no'}")


def cmd_select(a, run, h):
    p = prior(run)["persona"]
    allowed = ["P0"] if p.get("holdout") else p.get("top2") or []
    if a.persona not in allowed:
        refuse([f"persona {a.persona} is not one of {allowed} (03_prior.json)"])
    if not a.reason:
        refuse(["--reason is required: why this persona fits this seller (cite facts in words)"])
    log(run, {"kind": "select", "persona": a.persona, "reason": a.reason, "card": card_of(a.persona)})
    print(f"OK selected {a.persona}. Next: probe every field and eligible hook (status shows the list).")


def cmd_probe(a, run, h):
    folder = turn(run)["folder"]
    if a.field:
        spec, target = (h.get("fields") or {}).get(a.field), f"field:{a.field}"
        if a.field not in decide_fields(h):
            refuse([f"'{a.field}' is not a field you decide with this tool: {decide_fields(h)}"])
    else:
        spec, target = (h.get("hooks") or {}).get(a.hook), f"hook:{a.hook}"
        if not spec:
            refuse([f"no hook '{a.hook}' in hierarchy.json"])
    hits = search(folder, spec, as_of(run))
    log(run, {"kind": "probe", "target": target, "n_hits": len(hits), "hits": [{k: x[k] for k in ("id", "cite", "score")} for x in hits[:50]]})
    if a.json:
        print(json.dumps({"target": target, "hits": hits[:50]}, ensure_ascii=False))
        return
    print(f"probe {target}: {len(hits)} hits. Evidence rule: {spec.get('evidence_rule') or '-'}")
    for i, x in enumerate(hits[:MAX_SHOW], 1):
        print(f"  {'TOP' if i <= 3 else '   '} {x['id']}  [{', '.join(x['terms'])}]  {x['text']}")
    if len(hits) > MAX_SHOW:
        print(f"  ... {len(hits) - MAX_SHOW} more (all ids are in ledger.jsonl)")
    if hits:
        print("Use a hit as --cite (the part before ':L') with an exact --quote, or answer the TOP-3 with --answer if you use hierarchy/start_persona.")


def _answers(a):
    out = {}
    for s in a.answer or []:
        if "=" not in s:
            refuse([f"--answer must be <hit id>=\"why it does not count\", not '{s}'"])
        k, v = s.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def check_decision(run, h, field, value, rtype, cites, answers, level, group, searched, rows=None):
    """All write-time checks for one field decision. Returns a list of problems (empty = ok)."""
    rows = rows if rows is not None else ledger(run)
    spec = (h.get("fields") or {}).get(field) or {}
    folder = turn(run)["folder"]
    probs = []
    sel = last(rows, "select")
    if not sel:
        probs.append("select a persona first (select --persona)")
    if not last(rows, "probe", "target", f"field:{field}"):
        probs.append(f"probe the field first: probe --field {field}")
    types = list((h.get("reason_types") or {}).get("order") or ["seller_evidence", "hierarchy", "start_persona"])
    if rtype not in types:
        probs.append(f"--type must be one of {types}")
    rng = spec.get("hard_range")
    if isinstance(rng, list) and len(rng) == 2:
        if not isinstance(value, (int, float)) or not rng[0] <= value <= rng[1]:
            probs.append(f"value {value!r} outside {rng}")
    groups = spec.get("value_groups")
    if isinstance(groups, list) and groups and group_of(spec, value) is None:
        probs.append(f"value {value!r} is in no value group {groups}")
    hits = search(folder, spec, as_of(run))
    hit_cites = {x["cite"] for x in hits} | {x["id"] for x in hits}
    if rtype == "seller_evidence":
        if not cites:
            probs.append("seller_evidence needs at least one --cite with --quote")
        for c, q in cites:
            e = quote_ok(folder, c, q)
            if e:
                probs.append(e)
        if cites and not any(c in hit_cites and quote_in_hit(q, hits, {c}) for c, q in cites):
            probs.append(f"at least one cite must be a hit of probe --field {field} AND quote that hit's line "
                         f"(hits: {sorted(x['id'] for x in hits)[:6]})")
    elif rtype in ("hierarchy", "start_persona"):
        if not searched:
            probs.append("--searched is required: what you looked for in the probe hits and why it is not evidence")
        for x in hits[:3]:
            if not (answers.get(x["id"]) or "").strip():
                probs.append(f"answer the top hit {x['id']} (--answer {x['id']}=\"why it does not count\")")
        if rtype == "hierarchy":
            b = ((prior(run).get("brief") or {}).get(field) or {})
            g = (b.get("value_groups") or {}).get(group) or {}
            if not b.get("level_used") or level != b.get("level_used") or not g.get("n"):
                probs.append(f"hierarchy data must match the brief in 03_prior.json for {field}: "
                             f"level_used={b.get('level_used')!r}, groups={list((b.get('value_groups') or {}).keys())}")
            elif group_of(spec, value) != group:
                probs.append(f"value {value!r} is not in the group {group!r} you cite")
        if rtype == "start_persona" and sel:
            sv = start_value(field, sel.get("card") or {}, prior(run))
            if sv is None:
                probs.append(f"no start value for {field}: use seller_evidence or hierarchy")
            elif value != sv:
                probs.append(f"start_persona keeps the start value: {field} = {sv!r} (card {sel.get('persona')}, voice draw or default)")
    return probs


def _num(v):
    try:
        return float(v) if re.fullmatch(r"-?\d+(\.\d+)?", str(v)) else v
    except ValueError:
        return v


def cmd_decide(a, run, h):
    if len(a.cite or []) != len(a.quote or []):
        refuse(["give one --quote for each --cite"])
    value = _num(a.value)
    if a.field in ("words_per_turn",) and isinstance(value, float):
        value = int(value)
    cites, answers = list(zip(a.cite or [], a.quote or [])), _answers(a)
    if not a.reason:
        refuse(["--reason is required"])
    probs = check_decision(run, h, a.field, value, a.type, cites, answers, a.level, a.group, a.searched)
    if probs:
        refuse(probs)
    row = {"kind": "decide", "field": a.field, "value": value, "type": a.type, "reason": a.reason,
           "cites": [{"id": c, "quote": q} for c, q in cites], "answers": answers, "searched": a.searched,
           "hierarchy": {"level": a.level, "value_group": a.group} if a.type == "hierarchy" else None,
           "confidence": min(1.0, max(0.0, a.confidence)) if a.confidence is not None else CONF[a.type]}
    log(run, row)
    print(f"OK {a.field} = {value!r} ({a.type})")


def cmd_hook(a, run, h):
    rows = ledger(run)
    f = facts(run)
    folder = turn(run)["folder"]
    probs = []
    if a.id not in f.get("eligible_hooks", []):
        probs.append(f"{a.id} is not eligible for this seller: {f.get('eligible_hooks')}")
    if a.id in (h.get("hooks") or {}) and not last(rows, "probe", "target", f"hook:{a.id}"):
        probs.append(f"probe the hook first: probe --hook {a.id}")
    if len(a.cite or []) != len(a.quote or []) or len(a.counter_cite or []) != len(a.counter_quote or []):
        probs.append("give one quote for each cite")
    cites = list(zip(a.cite or [], a.quote or []))
    for c, q in cites + list(zip(a.counter_cite or [], a.counter_quote or [])):
        e = quote_ok(folder, c, q)
        if e:
            probs.append(e)
    if a.decision == "primary":
        files = {c.split("#")[0] for c, _ in cites}
        if len(cites) < 3 or len(files) < 2:
            probs.append("primary needs >= 3 cites from >= 2 files")
        if not (a.counter and a.counter_cite):
            probs.append("primary needs --counter text with --counter-cite/--counter-quote")
        spec = (h.get("hooks") or {}).get(a.id)
        if spec:
            hc = {x["cite"] for x in search(folder, spec, as_of(run))}
            if hc and not any(c in hc for c, _ in cites):
                probs.append(f"at least one cite must be a hit of probe --hook {a.id}")
    if not a.reason:
        probs.append("--reason is required")
    if probs:
        refuse(probs)
    log(run, {"kind": "hook", "id": a.id, "decision": a.decision, "reason": a.reason,
              "cites": [{"id": c, "quote": q} for c, q in cites],
              "counter": {"text": a.counter, "cites": [{"id": c, "quote": q} for c, q in zip(a.counter_cite or [], a.counter_quote or [])]}
              if a.counter else None})
    print(f"OK {a.id}: {a.decision}")


def cmd_text(a, run, h):
    try:
        doc = json.load(open(a.file, encoding="utf-8"))
    except (OSError, ValueError) as e:
        refuse([f"cannot read {a.file}: {e}"])
    extra = sorted(set(doc) - TEXT_KEYS)
    if extra:
        refuse([f"the text file may hold only {sorted(TEXT_KEYS)}; remove {extra} (fields are set with decide)"])
    rows = ledger(run) + [{"kind": "text", "doc": doc}]
    persona, _ = assemble(run, h, rows)
    sys.path.insert(0, HERE)
    import validate_persona as V
    probs = []
    V.check_text(turn(run)["folder"], persona, probs)
    if probs:
        refuse(probs, ["fix draft_text.json and run text again (decide the fields first, so the caps and scripts apply)"])
    log(run, {"kind": "text", "doc": doc, "sha": hashlib.sha256(json.dumps(doc, sort_keys=True).encode()).hexdigest()})
    print("OK text stored")


def assemble(run, h, rows):
    f, p = facts(run), prior(run)
    sel = last(rows, "select") or {}
    text = (last(rows, "text") or {}).get("doc") or {}
    dims = {}
    for fld in decide_fields(h):
        d = last(rows, "decide", "field", fld)
        if not d:
            continue
        dims[fld] = {"value": d["value"], "reason_type": d["type"], "reason": d["reason"], "cites": d["cites"],
                     "answers": d["answers"], "searched": d["searched"], "hierarchy": d["hierarchy"],
                     "confidence": d["confidence"], "evidence": GRADE[d["type"]]}
    if "voice_gender" in dims:
        dims["voice_id"] = {"value": dims["voice_gender"]["value"], "reason_type": "derived",
                            "reason": "follows voice_gender through the voice catalogue (compile_vars)", "cites": [],
                            "confidence": dims["voice_gender"]["confidence"], "evidence": dims["voice_gender"]["evidence"]}
    persona = {"decision_id": turn(run)["decision_id"], "division": f.get("division"),
               "prior": {"top2": p["persona"].get("top2"), "holdout": p["persona"].get("holdout"),
                         "chosen": sel.get("persona"), "chosen_reason": sel.get("reason"), "override": False},
               "dimensions": dims, "hierarchy_version": (h or {}).get("version")}
    persona.update({k: v for k, v in text.items() if k != "traits_states_review"})
    review = {"hooks": [{"id": r["id"], "B_agent": {"decision": r["decision"], "reason": r["reason"],
                                                     "probe": {"cites": r["cites"]}, "counter_evidence": r["counter"]}}
                        for r in [last(rows, "hook", "id", hid) for hid in f.get("eligible_hooks", [])] if r]}
    review.update(text.get("traits_states_review") or {})
    return persona, review


def cmd_finalize(a, run, h):
    rows = ledger(run)
    f = facts(run)
    missing = []
    if not last(rows, "select"):
        missing.append("select --persona")
    missing += [f"decide --field {x}" for x in decide_fields(h) if not last(rows, "decide", "field", x)]
    missing += [f"hook --id {x}" for x in f.get("eligible_hooks", []) if not last(rows, "hook", "id", x)]
    if not last(rows, "text"):
        missing.append("text --file <run>/draft_text.json")
    if missing:
        refuse([f"not done yet: {m}" for m in missing], [f"{tool_cmd()} status"])
    persona, review = assemble(run, h, rows)
    p04, p02 = os.path.join(run, "04_persona.json"), os.path.join(run, "02_review.json")
    json.dump(review, open(p02, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(persona, open(p04, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    sys.path.insert(0, HERE)
    import validate_persona as V
    fails = V.validate(turn(run)["folder"], run)
    if fails:
        os.remove(p04)
        os.remove(p02)
        refuse(fails, ["fix the decision or the text with this tool, then run finalize again"])
    log(run, {"kind": "finalize", "sha04": sha(p04), "sha02": sha(p02)})
    print("OK finalized: 02_review.json and 04_persona.json written and validated. Stop now.")


def main():
    a = argparse.ArgumentParser(prog="persona_tool.py")
    sp = a.add_subparsers(dest="cmd", required=True)
    sp.add_parser("status")
    s = sp.add_parser("select")
    s.add_argument("--persona", required=True)
    s.add_argument("--reason")
    s = sp.add_parser("probe")
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument("--field")
    g.add_argument("--hook")
    s.add_argument("--json", action="store_true")
    s = sp.add_parser("decide")
    s.add_argument("--field", required=True)
    s.add_argument("--value", required=True)
    s.add_argument("--type", required=True)
    s.add_argument("--reason")
    s.add_argument("--cite", action="append")
    s.add_argument("--quote", action="append")
    s.add_argument("--answer", action="append")
    s.add_argument("--level")
    s.add_argument("--group")
    s.add_argument("--searched")
    s.add_argument("--confidence", type=float)
    s = sp.add_parser("hook")
    s.add_argument("--id", required=True)
    s.add_argument("--decision", required=True, choices=["primary", "backup", "rejected"])
    s.add_argument("--reason")
    s.add_argument("--cite", action="append")
    s.add_argument("--quote", action="append")
    s.add_argument("--counter")
    s.add_argument("--counter-cite", action="append")
    s.add_argument("--counter-quote", action="append")
    s = sp.add_parser("text")
    s.add_argument("--file", required=True)
    sp.add_parser("finalize")
    args = a.parse_args()
    run = run_dir()
    h = load_hierarchy()
    if not h:
        sys.exit("persona_tool: references/hierarchy.json is missing (fail closed)")
    {"status": cmd_status, "select": cmd_select, "probe": cmd_probe, "decide": cmd_decide, "hook": cmd_hook,
     "text": cmd_text, "finalize": cmd_finalize}[args.cmd](args, run, h)


if __name__ == "__main__":
    main()
