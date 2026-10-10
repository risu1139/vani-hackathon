"""compile_vars.py: validated persona → Sarvam agent variables (S5). Contract: app/contracts/sarvam_vars.contract.json.

Refuses unless <run>/validation.json says pass (review B5: Sarvam variables are written only from a validated persona).
Fills name tokens ({SELLER_NAME}, {COMPANY}) on premises from the export map (never sent to the frontier model).
Range and catalogue checks (review m3). The prompt text is built by render_prompt.py as section variables prompt_*;
writes 06_sarvam_prompt.md (the full prompt this seller's call will use).

Usage: python3 compile_vars.py --run <run dir> [--names <map json>] [--city <city>]
Writes <run>/05_sarvam_vars.json.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_prompt as R  # noqa: E402
import seller_block as SB  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.abspath(os.path.join(HERE, "..", "references"))
VOICES = {  # proven in the 2026-10-09 OnStart spike; all Bulbul v4 voices speak 12 languages
    "F": {"id": "01a0cf16-90ae-7470-941d-2c1f17b37528", "name": "Aarti"},
    "M": {"id": "01a0e8fc-8a76-72d3-ae24-89b4688928eb", "name": "Anand"},
}
LANGS = {"hi": "HINDI", "hindi": "HINDI", "gu": "GUJARATI", "gujarati": "GUJARATI", "mr": "MARATHI", "marathi": "MARATHI",
         "ta": "TAMIL", "tamil": "TAMIL", "te": "TELUGU", "telugu": "TELUGU", "kn": "KANNADA", "kannada": "KANNADA",
         "ml": "MALAYALAM", "malayalam": "MALAYALAM", "bn": "BENGALI", "bengali": "BENGALI", "pa": "PUNJABI", "punjabi": "PUNJABI",
         "or": "ODIA", "odia": "ODIA", "en": "ENGLISH", "english": "ENGLISH"}
def val(p, d):
    return ((p.get("dimensions") or {}).get(d) or {}).get("value")


KNOWN_TOKEN = re.compile(r"\{(SELLER_NAME|COMPANY|SALES_EXEC|AGENT_NAME|COMPETITOR_\d+)\}")
ANY_TOKEN = re.compile(r"\{\s*[A-Za-z][A-Za-z0-9_ ]*\}")  # case-insensitive, spaces allowed: '{ competitor_1 }' is caught too
NAME_TOKEN = re.compile(r"\{(COMPETITOR_\d+(_ID)?|BUYER_COMPANY|EXEC_NAME|SALES_EXEC|TELE_EXEC)\}")
PHONE_EMAIL = re.compile(r"(\+?\d[\d\s-]{8,}\d)|([\w.+-]+@[\w-]+\.[\w.]+)")
SUFFIX = re.compile(r"\s*\b(pvt\.?|private|ltd\.?|limited|llp|inc\.?|co\.)(\s|$).*$", re.I)


def load_names(path):
    """Export map {tokens: {token: [variants]}} -> {token: the one spoken form}. On premises only."""
    m = json.load(open(path, encoding="utf-8"))
    out = {}
    for tok, vs in (m.get("tokens") or m).items():
        vs = [v for v in (vs if isinstance(vs, list) else [vs]) if isinstance(v, str) and v.strip()]
        if not vs:
            continue
        longest = max(vs, key=len)
        if tok == "{SELLER_NAME}":
            out[tok] = longest.split()[0].title()  # first name + "ji" in speech
        elif tok in ("{COMPANY}",) or tok.startswith("{COMPETITOR_") and not tok.endswith("_ID}"):
            out[tok] = SUFFIX.sub("", longest).strip() or longest
        else:
            out[tok] = longest
    if "spoken" in m:  # export maps from a6b5ba5 on: the safe spoken first name, never a company word; {} = say no name
        out["{SELLER_NAME}"] = (m["spoken"] or {}).get("{SELLER_NAME}", "")
    return out


TEAM_HANDLER_LINE = "our IndiaMART team handles your account; the executive will introduce themselves when they call"


def handler_line(facts, names):
    """R4 (plan 5f): the sentence VANI says when asked who handles the account. A person only through the {SALES_EXEC}
    token (so the unknown/unfilled-token checks cover it); anything else, or no data, is the team sentence, never empty."""
    st = {x["id"]: (x.get("A_script") or {}).get("value") for x in facts.get("states") or []}
    if st.get("state.handler") == "person":
        return fill("our IndiaMART executive {SALES_EXEC} handles your account and will meet you", names)
    return TEAM_HANDLER_LINE


def fill(text, names):
    for k, v in (names or {}).items():
        text = text.replace(k, v)
    return re.sub(r"[ 	]{2,}", " ", text) if names and not (names or {}).get("{SELLER_NAME}", "x") else text


def seller_city(run):
    """City is not PII: from the seller folder named in turn.json (B01, else X05)."""
    try:
        t = json.load(open(os.path.join(run, "turn.json"), encoding="utf-8"))
        folder = t["folder"]
        if not os.path.isfile(os.path.join(folder, "context.json")) and t.get("source"):
            # a run fetched from Daytona: its folder path is the sandbox's; use the local export with the same pseudonym
            folder = os.path.join(R.REPO, "data", "agent_export", os.path.basename(t["source"].rstrip("/\\")))
        pts = json.load(open(os.path.join(folder, "context.json"), encoding="utf-8"))["points"]
        b1, x5 = (pts.get("B01") or {}).get("value") or {}, (pts.get("X05") or {}).get("value") or {}
        return str(b1.get("city_name") or b1.get("seller_city") or x5.get("city") or "").strip().title()
    except (OSError, KeyError, ValueError, AttributeError):
        return ""


def compile_vars(run, names=None, city=None):
    city = city or seller_city(run)
    v = json.load(open(os.path.join(run, "validation.json"), encoding="utf-8"))
    if not v.get("pass"):
        raise SystemExit("REFUSED: persona not validated (validation.json pass=false)")
    p = json.load(open(os.path.join(run, "04_persona.json"), encoding="utf-8"))
    g = val(p, "voice_gender")
    if g not in VOICES:
        raise SystemExit(f"REFUSED: voice_gender {g} not in catalogue")
    pace, pitch = float(val(p, "pace")), float(val(p, "pitch"))
    if not (0.85 <= pace <= 1.25 and -0.3 <= pitch <= 0.3):
        raise SystemExit(f"REFUSED: pace {pace} / pitch {pitch} out of range")
    lang = LANGS.get(str(val(p, "language_start") or "hi").lower().split("-")[0], None) or \
        (str(val(p, "language_start")).upper() if str(val(p, "language_start")).upper() in LANGS.values() else None)
    if not lang:
        raise SystemExit(f"REFUSED: language {val(p, 'language_start')} not supported")
    names = dict(names) if names is not None else None
    agent = {"{AGENT_NAME}": VOICES[g]["name"]}  # VANI's own name = the voice's name (female voice, female name)
    if names is not None:
        names.update(agent)
    sec = R.sections(p)
    bad = sorted({k for k, t in sec.items() if NAME_TOKEN.search(t)})
    if bad:  # names of other sellers / the handler come only from the seller block (plan 5d)
        raise SystemExit(f"REFUSED: name tokens in persona sections {bad}")
    facts = json.load(open(os.path.join(run, "01_facts.json"), encoding="utf-8"))
    sec["prompt_seller"], block_lines = SB.build(facts, p, names)
    with open(os.path.join(run, "05_seller_block.json"), "w", encoding="utf-8") as f:
        json.dump([{"line": x, "source": c} for x, c in block_lines], f, ensure_ascii=False, indent=1)  # tokens, not names
    base = {
        "decision_id": p["decision_id"],
        "persona_voice_id": VOICES[g]["id"], "persona_voice_gender": g,
        "persona_pace": f"{pace:.2f}", "persona_pitch": f"{pitch:.2f}", "persona_language": lang,
        "persona_opening": fill(fill(p["opening"], names), agent), "identity_line": fill(fill(p["identity_line"], names), agent),
        "persona_style_id": (p.get("prior") or {}).get("chosen") if not (p.get("prior") or {}).get("override") else "COMPOSED",
        "switch_sensitivity": json.dumps(p.get("switch_sensitivity") or {}),
        "seller_name": (names or {}).get("{SELLER_NAME}", ""), "company_name": (names or {}).get("{COMPANY}", ""), "city": city or "",
        "handler_line": handler_line(facts, names),
    }
    # Sarvam fills variables in one pass: resolve @refs inside the sections here, before sending.
    inner = {k: base[k] for k in ("identity_line", "persona_opening", "seller_name", "company_name", "city")}
    for k, text in sec.items():
        for name in sorted(inner, key=len, reverse=True):
            text = text.replace("@" + name, inner[name] or ("the seller" if name == "seller_name" else "their company" if name == "company_name" else ""))
        sec[k] = fill(text if k == "prompt_seller" else fill(text, names), agent)
    out = {**base, **sec}
    cpath = os.path.join(R.REPO, "app", "contracts", "sarvam_vars.contract.json")
    if not os.path.exists(cpath):  # fail closed: never send variables that were not checked against the contract
        raise SystemExit(f"REFUSED: contract not found at {cpath} (the launcher sets VANI_REPO)")
    contract = json.load(open(cpath, encoding="utf-8"))
    missing = [k for k in contract["set_before_call"] if k not in out]
    if missing:
        raise SystemExit(f"REFUSED: contract variables missing {missing}")
    unknown = sorted({t for x in out.values() if isinstance(x, str) for t in ANY_TOKEN.findall(x) if not KNOWN_TOKEN.fullmatch(t)})
    if unknown:  # a token compile_vars does not know would be spoken as is
        raise SystemExit(f"REFUSED: unknown tokens {unknown}")
    leak = [k for k, x in out.items() if (k.startswith("prompt_") or k in ("persona_opening", "identity_line"))
            and isinstance(x, str) and PHONE_EMAIL.search(x)]
    if leak:
        raise SystemExit(f"REFUSED: phone number or email in {leak}")
    left = [k for k, x in out.items() if isinstance(x, str) and re.search(r"\{[A-Z_0-9]+\}", x)]
    if left and names is not None:
        raise SystemExit(f"REFUSED: unfilled name tokens in {left}")
    with open(os.path.join(run, "05_sarvam_vars.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    text, unfilled = R.render(out)
    if unfilled:
        raise SystemExit(f"REFUSED: skeleton variables not produced {unfilled}")
    open(os.path.join(run, "06_sarvam_prompt.md"), "w", encoding="utf-8").write(text)
    return out


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--run", required=True)
    a.add_argument("--names")
    a.add_argument("--city")
    p = a.parse_args()
    names = load_names(p.names) if p.names else None
    out = compile_vars(p.run, names, p.city)
    print(json.dumps({k: len(v) if isinstance(v, str) else v for k, v in out.items()}))  # sizes only: values hold names


if __name__ == "__main__":
    main()
