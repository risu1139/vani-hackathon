# Which opening/hook style books more meetings, by seller segment (PS07 natural experiment, 2026-10-10)

**Data.** 269,455 answered PS07 bot calls (Apr–Sep 2026). Outcome: `meeting_fixed`.
- Segments come from the PS07 seller file: turnover band; region (state mapped to a zone); top category group.
- Script: `app/analysis/bot_version_segments.py`. Full numbers: `outputs/analysis/bot_version_segments.json`. Aggregates only.
- **Method:** every version is compared with `main_vani` *inside the same week × trigger bucket* (Mantel–Haenszel risk difference, 95% CI). The versions ran at different times and on different triggers, and raw rates mislead.

**Versions (hooks, from outputs/call-flow-playbook.md):**
- `main_vani`: enquiry-count hook ("{N}+ buyer enquiries in {city}").
- `arrowhead`: interest hook ("buyers already showed interest; experts can triple it; free 20-minute meeting").
- `main`: discovery question about the seller's own market, with "branch manager" framing.
- `last_met_d`: follow-up for sellers an executive already met. A different population, so it is not compared.

## Overall (adjusted vs main_vani)
| Version | n | Raw meeting % | Adjusted difference (pts) | 95% CI |
|---|---|---|---|---|
| main_vani | 208,605 | 11.60 | — | — |
| arrowhead | 30,670 | 10.66 | **−0.52** | [−0.90, −0.14] |
| main (discovery opener) | 5,571 | 14.03 | **−2.46** | [−3.81, −1.10] |
| personalis | 452 | 14.16 | +3.02 | [−0.31, +6.36] (not significant) |
| base_vani | 289 | 18.34 | **+6.89** | [+2.32, +11.46] (small n) |
| summary_va | 91 | 3.30 | −8.23 | [−12.0, −4.5] (tiny n) |

**Note:** raw rates point the wrong way for `main`: 14.0% raw, but −2.5 points once week and bucket are held equal. The discovery opener looked good in the 3 calls read in the playbook, but it **loses** at scale.

## By segment: interest hook (arrowhead) vs enquiry-count hook (main_vani)
- **Region:**
  - better in **East +1.81** [+0.02, +3.59];
  - trending better in Central +2.57 (not significant) and South +1.21 (not significant);
  - worse in **North −1.16** [−1.70, −0.62]; West −0.63 (not significant).
- **Turnover:**
  - worse for **0–40 L −0.93** [−1.42, −0.45];
  - neutral for 1.5 Cr and above (≈ 0).
- **Category group:**
  - better for **Furniture +3.30** [+0.44, +6.16];
  - worse for **Apparel −3.02** [−4.33, −1.70], **Gems & Jewellery −3.04**, **Pharma −2.83**, **Textiles −2.66**, **Ayurvedic −3.53**. The 4 categories after Apparel are each just significant.
- **Discovery opener (main):**
  - worse for **0–40 L −3.17** [−4.92, −1.42], Central −6.86, Housewares −9.31, Industrial machinery −9.46;
  - no segment where it is significantly better.

## Caveats
- **Multiple comparisons:** about 40 category tests at 5% means about 2 false positives are expected. Treat category-level results as WEAK unless they repeat on a time split.
- Each version differs in more than the hook (the prompt, the persona name, the trigger mix). The comparison is of whole versions, so "the hook" is the best label, not a proof.
- `meeting_fixed` labels are noisy: the playbook found 4 of 20 labels that contradict the transcript.
- `base_vani` (+6.9 points, n = 289) and `personalis` are the 30 Sep concurrent trial. Their n is too small to rank styles, but `base_vani` is worth a look: it is the control prompt of that trial.

## What this gives the persona library (evidence-graded starting priors)
- **Hook/opening style per segment is now partly data-backed:**
  - enquiry-count hook = default;
  - interest hook = candidate for East (and Central/South), furniture, and larger sellers;
  - avoid the interest hook for small sellers (0–40 L), North, apparel, jewellery, pharma, textiles and ayurvedic;
  - avoid the discovery opener.
- Region, turnover and category do change which hook works. That supports segment-keyed priors with back-off.
- Voice gender, formality and pitch still have **no** data (PS07 used one voice). They stay GUESS and need exploration in Loop 2.
