"""compile_vars.py: validated persona → Sarvam agent variables (S5). Contract: app/contracts/sarvam_vars.contract.json.

Refuses unless <run>/validation.json says pass (review B5: Sarvam variables are written only from a validated persona).
Fills name tokens ({SELLER_NAME}, {COMPANY}) on premises from the export map (never sent to the frontier model).
Range and catalogue checks (review m3). Division text goes in the `division_block` variable (no Jinja, review M5).

Usage: python3 compile_vars.py --run <run dir> [--names <map json>] [--city <city>]
Writes <run>/05_sarvam_vars.json.
"""
import argparse
import json
import os
import re

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
STYLE = {
    "formality": {"low": "Friendly, informal respect.", "medium": "Polite and direct.", "high": "Formal and respectful."},
    "warmth": {"medium": "Calm and pleasant.", "high": "Warm and caring; sound genuinely glad to help."},
    "sophistication": {"simple": "Very simple words; no jargon.", "practical": "Practical, everyday business words.",
                       "numbers_first": "Lead with one concrete number when you have one from the facts."},
    "code_mix": {"regional_only": "Speak only the seller's regional language.", "light_hinglish": "Hindi with a few common English words.",
                 "hinglish": "Natural Hinglish.", "english_heavy": "Mostly English with light Hindi."},
}


def val(p, d):
    return ((p.get("dimensions") or {}).get(d) or {}).get("value")


def fill(text, names):
    for k, v in (names or {}).items():
        text = text.replace(k, v)
    return text


def division_block(div):
    path = os.path.join(REF, f"division_{div.lower()}.md")
    if not os.path.exists(path):
        return ""
    t = open(path, encoding="utf-8").read()
    m = re.search(r"<!-- sarvam_block -->(.*?)<!-- /sarvam_block -->", t, re.S)
    return (m.group(1) if m else "").strip()


def compile_vars(run, names=None, city=None):
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
    style = " ".join(x for x in [
        STYLE["formality"].get(val(p, "formality"), ""), STYLE["warmth"].get(val(p, "warmth"), ""),
        STYLE["sophistication"].get(val(p, "sophistication"), ""), STYLE["code_mix"].get(val(p, "code_mix"), ""),
        f"At most {int(val(p, 'words_per_turn') or 15)} words per reply. One question at a time. Address the seller as 'ji'.",
        f"Empathy: {val(p, 'empathy')}." if val(p, "empathy") else "",
        "Speak as a woman (use feminine first-person forms: 'kar rahi hoon')." if g == "F" else "Speak as a man (use masculine first-person forms: 'kar raha hoon')."]
        if x)
    plan = []
    for s in p.get("call_plan") or []:
        plan.append(f"{s.get('step')}. {s.get('goal')}: {s.get('say')}")
    plan.append("Objections (in this order):")
    for o in p.get("objection_playbook") or []:
        plan.append(f"- If the seller says \"{o.get('objection')}\": {o.get('response')}")
    plan.append("Escalation: " + "; ".join(p.get("escalation_rules") or []))
    out = {
        "decision_id": p["decision_id"],
        "persona_voice_id": VOICES[g]["id"], "persona_voice_gender": g,
        "persona_pace": f"{pace:.2f}", "persona_pitch": f"{pitch:.2f}", "persona_language": lang,
        "persona_opening": fill(p["opening"], names), "identity_line": fill(p["identity_line"], names),
        "persona_style_id": (p.get("prior") or {}).get("chosen") if not (p.get("prior") or {}).get("override") else "COMPOSED",
        "persona_style": style, "division_block": division_block(p["division"]),
        "call_plan": fill("\n".join(plan), names),
        "verified_facts": "\n".join(f"- {x.get('say')}" for x in p.get("verified_facts") or []),
        "guardrails_extra": "\n".join(f"- {x}" for x in (p.get("guardrails") or []) + [g2.get("action") for g2 in p.get("guards_ack") or [] if g2.get("action")]),
        "switch_sensitivity": json.dumps(p.get("switch_sensitivity") or {}),
        "seller_name": (names or {}).get("{SELLER_NAME}", ""), "company_name": (names or {}).get("{COMPANY}", ""), "city": city or "",
    }
    contract = json.load(open(os.path.join(HERE, "..", "..", "..", "..", "app", "contracts", "sarvam_vars.contract.json"), encoding="utf-8")) \
        if os.path.exists(os.path.join(HERE, "..", "..", "..", "..", "app", "contracts", "sarvam_vars.contract.json")) else None
    if contract:
        missing = [k for k in contract["set_before_call"] if k not in out]
        if missing:
            raise SystemExit(f"REFUSED: contract variables missing {missing}")
    left = [k for k, x in out.items() if isinstance(x, str) and re.search(r"\{[A-Z_]+\}", x)]
    if left and names is not None:
        raise SystemExit(f"REFUSED: unfilled name tokens in {left}")
    with open(os.path.join(run, "05_sarvam_vars.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    return out


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--run", required=True)
    a.add_argument("--names")
    a.add_argument("--city")
    p = a.parse_args()
    names = json.load(open(p.names, encoding="utf-8")) if p.names else None
    out = compile_vars(p.run, names, p.city)
    print(json.dumps({k: (v[:60] + "…" if isinstance(v, str) and len(v) > 60 else v) for k, v in out.items()}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
