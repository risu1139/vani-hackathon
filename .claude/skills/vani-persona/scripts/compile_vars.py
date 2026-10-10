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

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "..", "references")
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


SUFFIX = re.compile(r"\s*(pvt\.?|private|ltd\.?|limited|llp|inc\.?|co\.)(\s|$).*$", re.I)


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
    return out


def fill(text, names):
    for k, v in (names or {}).items():
        text = text.replace(k, v)
    return text


def seller_city(run):
    """City is not PII: from the seller folder named in turn.json (B01, else X05)."""
    try:
        folder = json.load(open(os.path.join(run, "turn.json"), encoding="utf-8"))["folder"]
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
    sec = R.sections(p)
    base = {
        "decision_id": p["decision_id"],
        "persona_voice_id": VOICES[g]["id"], "persona_voice_gender": g,
        "persona_pace": f"{pace:.2f}", "persona_pitch": f"{pitch:.2f}", "persona_language": lang,
        "persona_opening": fill(p["opening"], names), "identity_line": fill(p["identity_line"], names),
        "persona_style_id": (p.get("prior") or {}).get("chosen") if not (p.get("prior") or {}).get("override") else "COMPOSED",
        "switch_sensitivity": json.dumps(p.get("switch_sensitivity") or {}),
        "seller_name": (names or {}).get("{SELLER_NAME}", ""), "company_name": (names or {}).get("{COMPANY}", ""), "city": city or "",
    }
    # Sarvam fills variables in one pass: resolve @refs inside the sections here, before sending.
    inner = {k: base[k] for k in ("identity_line", "persona_opening", "seller_name", "company_name", "city")}
    for k, text in sec.items():
        for name in sorted(inner, key=len, reverse=True):
            text = text.replace("@" + name, inner[name] or ("the seller" if name == "seller_name" else "their company" if name == "company_name" else ""))
        sec[k] = fill(text, names)
    out = {**base, **sec}
    cpath = os.path.join(R.REPO, "app", "contracts", "sarvam_vars.contract.json")
    if not os.path.exists(cpath):  # fail closed: never send variables that were not checked against the contract
        raise SystemExit(f"REFUSED: contract not found at {cpath} (the launcher sets VANI_REPO)")
    contract = json.load(open(cpath, encoding="utf-8"))
    missing = [k for k in contract["set_before_call"] if k not in out]
    if missing:
        raise SystemExit(f"REFUSED: contract variables missing {missing}")
    left = [k for k, x in out.items() if isinstance(x, str) and re.search(r"\{[A-Z_]+\}", x)]
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
