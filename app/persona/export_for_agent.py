"""Export one seller's context folder for the frontier decider, under a pseudonym (review M19, data policy 2026-10-09).

Copies data/contexts/<glid>/ to data/agent_export/<pseudo>/, where
  <pseudo> = first 16 hex chars of HMAC-SHA256(VANI_PSEUDO_KEY, glid). The key lives in .env; it is made on first use.
In every .md file and context.json:
  - the GLID becomes the pseudo id;
  - seller / contact first and last names become {SELLER_NAME}; the company name becomes {COMPANY};
  - competitor companies become {COMPETITOR_1..n} (their GLIDs {COMPETITOR_n_ID}); the seller's sales handler becomes {SALES_EXEC} and the tele handler {TELE_EXEC} (the same token when it is the same person); other staff names become {EXEC_NAME};
  - the seller's catalogue URLs / alias become {COMPANY_URL}; enquiry buyer companies become {BUYER_COMPANY}.
The token -> value map goes to data/agent_export_maps/<pseudo>.json (never inside the export). compile_vars fills the
tokens back on-prem, for Sarvam only.
Hard gate: pii_check.scan plus a search for every original name, alias and the GLID. Any hit deletes the export and
exits non-zero. Values are never printed, only categories and file names.

Run: python app/persona/export_for_agent.py --glid 12345678 [--src data/contexts]
"""
import argparse
import hashlib
import hmac
import json
import os
import re
import secrets
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import pii_check  # noqa: E402

DATA = os.path.join(REPO, "data")
SRC = os.path.join(DATA, "contexts")
DST = os.path.join(DATA, "agent_export")
MAPS = os.path.join(DATA, "agent_export_maps")
ENV = os.path.join(REPO, ".env")
KEY_NAME = "VANI_PSEUDO_KEY"

SALUTES = {"mr", "mrs", "ms", "miss", "dr", "shri", "sri", "smt", "m/s", "ms.", "mr.", "mrs.", "dr.", "ji", "sir", "madam"}
COMPANY_SUFFIX = re.compile(r"[\s,.]*(private limited|pvt\.? ltd\.?|pvt\.?|limited|ltd\.?|llp|& co\.?|and co\.?|"
                            r"\(opc\)|opc)\s*$", re.I)
SELLER_KEYS = re.compile(r"^(glusr_usr_c?(first|middle|last)name|DIR_SEARCH_CONTACTPERSON|alternate_person_name|"
                         r"contact_name|contact_person|gst_partner_names)$", re.I)
COMPANY_KEYS = re.compile(r"^(glusr_usr_companyname|company_name|DIR_SEARCH_COMPANY|seller_company)$", re.I)
EXEC_KEYS = re.compile(r"^([a-z_]*assignedto_name|[a-z_]*exec(utive)?_name|employee_name|staff_name|[a-z_]*manager_name)$", re.I)
URL_KEYS = re.compile(r"^(URL|FREE_SHOWROOM_URL|PAID_SHOWROOM_URL|FREESHOWROOM_ALIAS|alias|freeshowroom_url|paidshowroom_url)$", re.I)
GENERIC_WORDS = {"shree", "shri", "india", "indian", "global", "royal", "super", "national", "international", "modern",
                 "universal", "standard", "united", "general", "premier", "perfect", "quality", "classic", "golden", "bharat",
                 "hindustan", "techno", "industries", "enterprises", "traders", "trading", "services", "solutions", "systems",
                 "engineering", "engineers", "electricals", "electronics", "steel", "plastic", "plastics", "packaging", "creative"}
# words of team / vertical names that sit in *_assignedto_name fields ("NSD Top Cities - Channel FSF"); never person names
ORG_WORDS = {"nsd", "csd", "tmw", "kcd", "fsf", "top", "cities", "city", "channel", "emerging", "markets", "inhouse", "registered",
             "supplier", "pre", "sales", "support", "tele", "monthly", "welcome", "team", "desk", "vertical", "zone", "region"}
MIN_LEN = 3  # name parts shorter than this are not replaced on their own (too many false matches)


# ---------------------------------------------------------------- key and pseudonym
def load_key(env_path=ENV):
    """Return VANI_PSEUDO_KEY from .env; generate and append one if missing. Never printed."""
    if os.environ.get(KEY_NAME):
        return os.environ[KEY_NAME]
    if os.path.exists(env_path):
        for line in open(env_path, encoding="utf-8"):
            if line.strip().startswith(KEY_NAME + "="):
                v = line.split("=", 1)[1].strip().strip('"').strip("'")
                if v:
                    return v
    key = secrets.token_hex(32)
    with open(env_path, "a", encoding="utf-8") as f:
        f.write(("\n" if os.path.exists(env_path) and open(env_path, encoding="utf-8").read()[-1:] not in ("", "\n") else "")
                + f"# HMAC key for seller pseudonyms (export_for_agent.py); never share\n{KEY_NAME}={key}\n")
    return key


def pseudo_id(glid, key):
    return hmac.new(key.encode(), str(glid).strip().encode(), hashlib.sha256).hexdigest()[:16]


# ---------------------------------------------------------------- collect names from context.json
def _walk(o, fn, key=""):
    if isinstance(o, dict):
        for k, v in o.items():
            _walk(v, fn, str(k))
    elif isinstance(o, list):
        for x in o:
            _walk(x, fn, key)
    else:
        fn(key, o)


def _person_parts(v):
    parts = [w.strip(".()[]") for w in re.split(r"[\s,;/]+", str(v or "").strip()) if w]
    if any(w.lower() in ORG_WORDS for w in parts) or " - " in str(v):
        return []  # a team / vertical name, not a person
    return [w for w in parts if w.lower() not in SALUTES and len(w) >= MIN_LEN]


def collect_names(ctx):
    """{token: [original strings]} from a context.json dict. Competitors keep their own numbered token."""
    seller, company, execs, urls, buyers = set(), set(), set(), set(), set()
    sales, tele = set(), set()                                  # the seller's handlers: role tokens {SALES_EXEC}, {TELE_EXEC}
    competitors, comp_ids = [], {}

    def fn(k, v):
        if not isinstance(v, str) or not v.strip():
            return
        if SELLER_KEYS.match(k):
            full = " ".join(_person_parts(v))
            if full:
                seller.add(full)
            seller.update(_person_parts(v))
        elif COMPANY_KEYS.match(k):
            company.add(v.strip())
        elif EXEC_KEYS.match(k):
            kl = k.lower()
            bucket = tele if kl.endswith("teleassignedto_name") else sales if kl.endswith("assignedto_name") else execs
            full = " ".join(_person_parts(v))
            if full:
                bucket.add(full)
            bucket.update(_person_parts(v))
        elif URL_KEYS.match(k):
            urls.add(v.strip().strip("/"))
        elif k == "buyer_company":
            buyers.add(v.strip())
    _walk(ctx.get("points", {}), fn)
    a02 = ((ctx.get("points") or {}).get("A02") or {}).get("value")
    if isinstance(a02, dict):
        company.update(str(x).strip() for x in a02.values() if isinstance(x, str) and x.strip())
    elif isinstance(a02, str) and a02.strip():
        company.add(a02.strip())
    e08 = (((ctx.get("points") or {}).get("E08") or {}).get("value") or {})
    for c in (((e08.get("competitors") or {}) if isinstance(e08, dict) else {}).get("competitors") or []):
        name = str(c.get("competitor_company") or "").strip()
        if name and name not in competitors:
            competitors.append(name)
        if c.get("competitor_glusr_id") and name:
            comp_ids[str(c["competitor_glusr_id"]).split(".")[0]] = competitors.index(name) + 1
    for c in list(company):  # "ABC Traders Pvt Ltd" -> also "ABC Traders", and "ABC" when it is distinctive (calls say "ABC se?")
        core = COMPANY_SUFFIX.sub("", c).strip()
        if len(core) >= 4 and core != c:
            company.add(core)
        first = re.split(r"[\s\-_.,&]+", core)[0] if core else ""
        if len(first) >= 5 and first.lower() not in GENERIC_WORDS and first != core:
            company.add(first)
    sales -= seller
    tele -= seller
    if tele and tele <= sales:                                  # the same person handles sales and tele: one token, {SALES_EXEC}
        tele = set()
    tele -= sales                                               # a name part shared by both roles maps to {SALES_EXEC}
    out = {"{SELLER_NAME}": sorted(seller), "{COMPANY}": sorted(company), "{SALES_EXEC}": sorted(sales), "{TELE_EXEC}": sorted(tele),
           "{EXEC_NAME}": sorted(execs - seller - sales - tele),
           "{COMPANY_URL}": sorted(u for u in urls if len(u) >= 4), "{BUYER_COMPANY}": sorted(b for b in buyers if len(b) >= MIN_LEN)}
    for i, n in enumerate(competitors, 1):
        out[f"{{COMPETITOR_{i}}}"] = [n] + ([COMPANY_SUFFIX.sub("", n).strip()] if len(COMPANY_SUFFIX.sub("", n).strip()) >= 4
                                            and COMPANY_SUFFIX.sub("", n).strip() != n else [])
    for gid, i in comp_ids.items():
        out[f"{{COMPETITOR_{i}_ID}}"] = [gid]
    return {k: v for k, v in out.items() if v}


# ---------------------------------------------------------------- replacement
def _pattern(s):
    """Case-insensitive; words may be joined by spaces, hyphens, dots, underscores or nothing (URL slugs)."""
    words = [re.escape(w) for w in re.split(r"[\s\-_.]+", s.strip()) if w]
    if not words:
        return None
    if re.fullmatch(r"\d+", s.strip()):
        return re.compile(rf"(?<!\d){re.escape(s.strip())}(?!\d)")
    return re.compile(r"(?<![A-Za-z0-9])" + r"[\s\-_.]*".join(words) + r"(?![A-Za-z0-9])", re.I)


def replacer(glid, pseudo, names):
    """One function str -> str that applies the GLID and every name token, longest original first."""
    pairs = [(o, tok) for tok, origs in names.items() for o in origs]
    pairs.sort(key=lambda p: -len(p[0]))
    pats = [(p, tok) for o, tok in pairs for p in [_pattern(o)] if p]
    gpat = re.compile(rf"(?<!\d){re.escape(str(glid))}(?!\d)")

    def fn(s):
        s = gpat.sub(pseudo, s)
        for p, tok in pats:
            s = p.sub(tok, s)
        return s
    return fn


def replace_json(o, fn, glid, pseudo):
    if isinstance(o, dict):
        return {fn(str(k)): replace_json(v, fn, glid, pseudo) for k, v in o.items()}
    if isinstance(o, list):
        return [replace_json(x, fn, glid, pseudo) for x in o]
    if isinstance(o, str):
        return fn(o)
    if isinstance(o, (int, float)) and not isinstance(o, bool) and float(o).is_integer():
        s = str(int(o))
        r = fn(s)  # the GLID or a competitor GLID stored as a number becomes its token
        return r if r != s else o
    return o


SOURCE_KEYS = {"sources", "api_status", "cache_files_used", "cache_hash"}


def _drop_gap(o):
    """'gap' notes name the APIs that did not work; the agent has no use for them."""
    if isinstance(o, dict):
        return {k: _drop_gap(v) for k, v in o.items() if k != "gap"}
    if isinstance(o, list):
        return [_drop_gap(x) for x in o]
    return o


def _drop_urls(o):
    """catalog_url holds the competitor's company name as a slug; VANI never says URLs."""
    if isinstance(o, dict):
        return {k: _drop_urls(v) for k, v in o.items() if k != "catalog_url"}
    if isinstance(o, list):
        return [_drop_urls(x) for x in o]
    return o


HANDLER_EXTRA_KEYS = re.compile(r"^(assignedto|teleassignedto\w*|tele_vertical|cks_assignedto\w*)$")
HANDLER_EXTRA_LINES = re.compile(r"(?m)^- \*\*(assignedto|teleassignedto\w*|tele_vertical|cks_assignedto\w*):\*\*.*\n?")


def _drop_handler_extras(ctx):
    """Only the SALES handler matters (user decision 2026-10-10): drop the tele handler and the employee id numbers from H02."""
    h02 = ((ctx.get("points") or {}).get("H02") or {})
    if isinstance(h02.get("value"), dict):
        h02["value"] = {k: v for k, v in h02["value"].items() if not HANDLER_EXTRA_KEYS.match(k)}
    return ctx


CATALOG_URL_TEXT = re.compile(r',?\s*"catalog_url":\s*"[^"]*"')


def strip_sources(ctx):
    """The agent must not see where data came from (files, tables, APIs): it runs in a sandbox that has none of them."""
    out = {k: v for k, v in ctx.items() if k not in SOURCE_KEYS}
    out["points"] = {pid: {k: v for k, v in (pt.items() if isinstance(pt, dict) else []) if k != "source"}
                     for pid, pt in (ctx.get("points") or {}).items()}
    return _drop_handler_extras(_drop_urls(_drop_gap(out)))


# ---------------------------------------------------------------- gate
def gate(folder, glid, names):
    """Hard PII gate: pii_check patterns + any original name / alias / GLID left. Returns {category: [files]}."""
    hits = {k: sorted({f for f, _ in v}) for k, v in pii_check.scan(folder).items()}
    gpat = re.compile(rf"(?<!\d){re.escape(str(glid))}(?!\d)")
    pats = [(tok, p) for tok, origs in names.items() for o in origs for p in [_pattern(o)] if p]
    for root, _, fs in os.walk(folder):
        for f in fs:
            path = os.path.join(root, f)
            rel = os.path.relpath(path, folder)
            if str(glid) in f:
                hits.setdefault("glid_in_filename", []).append(rel)
            t = open(path, encoding="utf-8").read()
            if gpat.search(t):
                hits.setdefault("glid", []).append(rel)
            for tok, p in pats:
                if p.search(t):
                    hits.setdefault("name " + tok, []).append(rel)
    return {k: sorted(set(v)) for k, v in hits.items()}


# ---------------------------------------------------------------- export
FIRST_NAME_KEYS = ("glusr_usr_cfirstname", "glusr_usr_firstname")


def spoken_names(ctx, names):
    """The form VANI may SAY for {SELLER_NAME}: the contact's FIRST name from the account first-name fields only.
    Never a word of the company name and never taken from gst_partner_names / contact-person strings (they can hold a firm name).
    Returns {"{SELLER_NAME}": "First"} or {} when no safe first name exists (then VANI says no name)."""
    a03 = (((ctx.get("points") or {}).get("A03") or {}).get("value") or {})
    company_words = {w.lower() for c in names.get("{COMPANY}", []) for w in re.split(r"\W+", c) if len(w) > 2}
    for k in FIRST_NAME_KEYS:
        v = a03.get(k) if isinstance(a03, dict) else None
        parts = re.split(r"\s+", str(v or "").strip())
        first = parts[0] if parts and parts[0] else ""
        if len(first) >= 2 and first.isalpha() and first.lower() not in company_words:
            return {"{SELLER_NAME}": first.title()}
    return {}


def export(glid, src=None, dst=None, maps=None, key=None):
    glid = str(glid).strip()
    src, dst, maps = src or SRC, dst or DST, maps or MAPS
    folder = os.path.join(src, glid)
    if not os.path.exists(os.path.join(folder, "context.json")):
        raise SystemExit(f"no context folder for this GLID under {os.path.relpath(src, REPO)}; build it first")
    key = key or load_key()
    pseudo = pseudo_id(glid, key)
    ctx = json.load(open(os.path.join(folder, "context.json"), encoding="utf-8"))
    names = collect_names(ctx)
    fn = replacer(glid, pseudo, names)
    out = os.path.join(dst, pseudo)
    if os.path.exists(out):
        shutil.rmtree(out)
    for root, _, fs in os.walk(folder):
        for f in fs:
            path = os.path.join(root, f)
            rel = os.path.relpath(path, folder)
            target = os.path.join(out, fn(rel))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            if f == "all.md":
                continue  # one-file human copy; the agent reads the split files
            if f == "context.json":
                with open(target, "w", encoding="utf-8") as w:
                    json.dump(replace_json(strip_sources(ctx), fn, glid, pseudo), w, ensure_ascii=False, default=str)
            elif f.endswith(".md"):
                with open(target, "w", encoding="utf-8") as w:
                    w.write(HANDLER_EXTRA_LINES.sub("", CATALOG_URL_TEXT.sub("", re.sub(r"(?m)^- \*\*gap:\*\*.*\n?", "", fn(open(path, encoding="utf-8").read())))))
            # any other file type is not exported
    hits = gate(out, glid, names)
    if hits:
        shutil.rmtree(out)
        return pseudo, None, hits
    os.makedirs(maps, exist_ok=True)
    with open(os.path.join(maps, f"{pseudo}.json"), "w", encoding="utf-8") as f:
        json.dump({"pseudo": pseudo, "glid": glid, "tokens": names, "spoken": spoken_names(ctx, names)}, f, ensure_ascii=False, indent=1)
    return pseudo, out, {}


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--glid", required=True)
    a.add_argument("--src", default=None, help="folder that holds <glid>/ (default data/contexts)")
    p = a.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    pseudo, out, hits = export(p.glid, os.path.abspath(p.src) if p.src else None)
    if hits:
        print(f"PII GATE FAILED for {pseudo}: export deleted. " + "; ".join(f"{k} in {v[:4]}" for k, v in hits.items()),
              file=sys.stderr)
        sys.exit(2)
    print(f"exported: {os.path.relpath(out, REPO)} (map: data/agent_export_maps/{pseudo}.json)")


if __name__ == "__main__":
    main()
