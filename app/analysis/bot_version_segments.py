"""Natural experiment in PS07: which bot opening/hook style books more meetings, overall and per seller segment.

Bot versions differ in the opening hook (outputs/call-flow-playbook.md):
  main_vani  = enquiry-count hook ("{N}+ buyer enquiries in {city}")
  arrowhead  = interest hook ("buyers already showed interest; experts can triple it; free 20-min meeting")
  main       = discovery question about the seller's own market (branch-manager framing)
  last_met_d = follow-up for sellers an executive already met (different population; reported, not compared)

Confounds: versions ran in different weeks and trigger buckets. So every comparison against main_vani is
STRATIFIED by week x trigger bucket (Mantel-Haenszel risk difference): only strata where both versions ran count.

Segments (from the PS07 seller file): top_category_group, annual_turnover band, region (state -> zone).
Outcome: meeting_fixed on answered bot calls. Aggregates only; no seller ids are written.

Usage: python app/analysis/bot_version_segments.py  ->  prints tables; writes outputs/analysis/bot_version_segments.json
"""
import glob
import json
import math
import os

import pandas as pd

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
D = os.path.join(REPO, "data", "ps07")
BASE = "main_vani"
COMPARE = ["arrowhead", "main", "personalis", "summary_va", "base_vani"]
MIN_N = 150  # min calls of the compared version inside a segment to report it

ZONE = {
    "North": ["Delhi", "Haryana", "Punjab", "Chandigarh", "Himachal Pradesh", "Jammu & Kashmir", "Jammu and Kashmir", "Uttarakhand", "Uttar Pradesh", "Rajasthan", "Ladakh"],
    "West": ["Maharashtra", "Gujarat", "Goa", "Dadra & Nagar Haveli", "Daman & Diu", "Dadra and Nagar Haveli and Daman and Diu"],
    "South": ["Tamil Nadu", "Karnataka", "Kerala", "Andhra Pradesh", "Telangana", "Puducherry", "Pondicherry"],
    "East": ["West Bengal", "Odisha", "Orissa", "Bihar", "Jharkhand", "Assam", "Meghalaya", "Tripura", "Manipur", "Mizoram", "Nagaland", "Arunachal Pradesh", "Sikkim"],
    "Central": ["Madhya Pradesh", "Chhattisgarh"],
}
STATE_ZONE = {s.lower(): z for z, ss in ZONE.items() for s in ss}


def load():
    calls = pd.concat([pd.read_csv(f, usecols=["fk_glusr_usr_id", "redis_bucket", "lead_bot_version", "call_start_time",
                                               "meeting_fixed"], low_memory=False)
                       for f in sorted(glob.glob(os.path.join(D, "ps07_bot_calls_*.csv")))], ignore_index=True)
    calls["meeting"] = pd.to_numeric(calls["meeting_fixed"], errors="coerce").fillna(0).clip(0, 1)
    calls["week"] = pd.to_datetime(calls["call_start_time"], errors="coerce").dt.to_period("W").astype(str)
    calls["stratum"] = calls["week"] + "|" + calls["redis_bucket"].fillna("?")
    sf = pd.concat([pd.read_csv(f, usecols=["fk_glusr_usr_id", "seller_state", "annual_turnover", "top_category_group"],
                                low_memory=False) for f in sorted(glob.glob(os.path.join(D, "ps07_seller_files_part*.csv")))],
                   ignore_index=True).drop_duplicates("fk_glusr_usr_id")
    sf["region"] = sf["seller_state"].fillna("").str.strip().str.lower().map(STATE_ZONE).fillna("Other/unknown")
    sf["turnover"] = sf["annual_turnover"].fillna("unknown")
    sf["category_group"] = sf["top_category_group"].fillna("unknown")
    return calls.merge(sf[["fk_glusr_usr_id", "region", "turnover", "category_group"]], on="fk_glusr_usr_id", how="left").reset_index(drop=True)


def mh_diff(df, version):
    """Mantel-Haenszel risk difference (version - BASE) over week x bucket strata, with a 95% CI."""
    num = w_sum = var = 0.0
    n_v = n_b = 0
    for _, g in df[df["lead_bot_version"].isin([version, BASE])].groupby("stratum"):
        a = g[g["lead_bot_version"] == version]["meeting"]
        b = g[g["lead_bot_version"] == BASE]["meeting"]
        if len(a) == 0 or len(b) == 0:
            continue
        n1, n0 = len(a), len(b)
        p1, p0 = a.mean(), b.mean()
        w = n1 * n0 / (n1 + n0)
        num += w * (p1 - p0)
        w_sum += w
        var += w * w * (p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0)
        n_v += n1
        n_b += n0
    if w_sum == 0:
        return None
    d = num / w_sum
    se = math.sqrt(var) / w_sum
    return {"version": version, "n_version": n_v, "n_base_matched": n_b, "diff_pts": round(100 * d, 2),
            "ci95_pts": [round(100 * (d - 1.96 * se), 2), round(100 * (d + 1.96 * se), 2)],
            "significant": abs(d) > 1.96 * se}


def main():
    df = load()
    out = {"base": BASE, "outcome": "meeting_fixed on answered bot calls", "n_calls": int(len(df)),
           "raw_rates": {v: {"n": int(len(g)), "meeting_pct": round(100 * g["meeting"].mean(), 2)}
                         for v, g in df.groupby("lead_bot_version")}}
    print(f"calls {len(df)}; raw meeting rate by version:")
    for v, r in sorted(out["raw_rates"].items(), key=lambda x: -x[1]["n"]):
        print(f"  {v:12} n={r['n']:7}  {r['meeting_pct']:5.2f}%")
    out["overall_adjusted"] = [r for v in COMPARE if (r := mh_diff(df, v))]
    print("\nadjusted vs main_vani (same week x bucket):")
    for r in out["overall_adjusted"]:
        print(f"  {r['version']:12} n={r['n_version']:6}  diff {r['diff_pts']:+.2f} pts  CI {r['ci95_pts']}  {'*' if r['significant'] else ''}")
    out["by_segment"] = {}
    for seg in ["turnover", "region", "category_group"]:
        rows = []
        for val, g in df.groupby(seg):
            for v in ["arrowhead", "main"]:
                if (g["lead_bot_version"] == v).sum() < MIN_N:
                    continue
                r = mh_diff(g, v)
                if r:
                    rows.append({seg: val, "base_rate_pct": round(100 * g[g.lead_bot_version == BASE]["meeting"].mean(), 2), **r})
        out["by_segment"][seg] = rows
        print(f"\nby {seg} (only cells with >= {MIN_N} calls of the version):")
        for r in sorted(rows, key=lambda x: (x["version"], -x["diff_pts"])):
            print(f"  {r['version']:10} {str(r[seg])[:40]:40} base {r['base_rate_pct']:5.2f}%  diff {r['diff_pts']:+6.2f}  CI {r['ci95_pts']}  {'*' if r['significant'] else ''}")
    os.makedirs(os.path.join(REPO, "outputs", "analysis"), exist_ok=True)
    with open(os.path.join(REPO, "outputs", "analysis", "bot_version_segments.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=str)


if __name__ == "__main__":
    main()
