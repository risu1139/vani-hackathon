"""Scan seller context folders for PII left behind. Exit code 1 if anything is found.

Checks phone numbers, emails, GST/PAN/Aadhaar/IFSC patterns, and PII-bearing JSON keys with a value.
Names (seller, contact, company) are allowed by the team data policy and are not flagged.

Usage: python app/persona/pii_check.py [data/contexts/<glid> ...]   (default: every folder in data/contexts)
"""
import glob
import os
import re
import sys

PATTERNS = {
    "mobile": r"(?<![\d.])(?:\+?91[-\s]?)?[6-9]\d{9}(?![\d])",
    "landline": r"(?<![\d])0\d{2,4}[-\s]\d{6,8}(?![\d])",
    "email": r"[\w.+-]+@[\w-]+\.[a-z]{2,}",
    "GSTIN": r"\b\d{2}[A-Z]{5}\d{4}[A-Z][0-9A-Z]Z[0-9A-Z]\b",
    "PAN": r"\b[A-Z]{5}\d{4}[A-Z]\b",
    "aadhaar": r"(?<![\d])\d{4}\s\d{4}\s\d{4}(?![\d])",
    "IFSC": r"\b[A-Z]{4}0[A-Z0-9]{6}\b",
}
PII_KEYS = re.compile(r'"(?![a-z_]*_flag")(glusr_usr_ph[a-z_]*|[a-z_]*email[a-z_]*|[a-z_]*pincode|address\d?|[a-z_]*latitude|[a-z_]*longitude|'
                      r'document_path|original_file_path|llm_extraction|glusr_gst_no)"\s*:\s*"[^"]+', re.I)


def scan(folder):
    hits = {}
    for f in glob.glob(os.path.join(folder, "**", "*"), recursive=True):
        if os.path.isdir(f):
            continue
        t = open(f, encoding="utf-8").read()
        for k, p in PATTERNS.items():
            for m in re.findall(p, t):
                hits.setdefault(k, []).append((os.path.relpath(f), m[:3] + "…"))
        for m in PII_KEYS.findall(t):
            hits.setdefault("pii_key", []).append((os.path.relpath(f), m))
    return hits


def main():
    folders = sys.argv[1:] or sorted(d for d in glob.glob(os.path.join("data", "contexts", "*")) if os.path.isdir(d))
    bad = 0
    for d in folders:
        h = scan(d)
        n = sum(len(v) for v in h.values())
        bad += n
        print(f"{os.path.basename(d):>11}: " + ("clean" if not n else ", ".join(f"{k} {len(v)} in {sorted({x[0] for x in v})[:3]}" for k, v in h.items())))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
