# Voice and language: starting guidance (judgement, not a rule table)

Status: starting priors (2026-10-10). The learning loop changes them with outcomes. Sources:
- `raw/research/2026-10-10-persona-priors-external-evidence.md`;
- `raw/hackathon/2026-10-10-team-decision-voice-language-priors.md`;
- `references/evidence/hook_priors.json`.

## The principle
There is no single best voice. The best voice depends on:
- the callee's gender;
- the price tier (the seller's AOV and turnover);
- the city tier;
- the weekday;
- how tense the call is.

(Field RCTs: 124K outbound AI calls; debt-collection field studies.) Weigh these for each seller. Do not use one voice for everyone.

## Starting priors (until our own data says otherwise)
| Dimension | Start with | Lean further when | Evidence |
|---|---|---|---|
| Voice gender | **Female** | The seller was frustrated or irate on past calls; the seller is in a rural area or a small town, especially in the Hindi belt | External field studies (female voice helps more in tense calls) + team decision. WEAK |
| Opening | **Short and interactive.** One value statement, then one simple question | — | External: statements beat questions; short beats long. PS07: the enquiry-count statement hook is the default. MODERATE |
| Hook style | Enquiry-count / value statement | See `evidence/hook_priors.json` by region, turnover and category | PS07 natural experiment. MODERATE (region, turnover), WEAK (category) |
| Language | **The seller's regional language** | High-value sellers: the agent decides, e.g. Hinglish or English for sophistication | Team decision. Light code-mixing that mirrors the seller (MSR India). WEAK |
| AI disclosure | Never volunteer "AI". Sidestep once; say "virtual assistant" if pressed; never claim to be human | — | Field RCT: disclosure up front cut purchases by about 80%. Team decision |
| Pace, pitch, formality, warmth | **No outside evidence.** Set them from the seller's states (rushed → brief; confused → slow phrasing) | — | GUESS + states. Learned by exploration |

## Data you can use for these
- **Callee gender:** `trait.seller_gender` (recorded, else a guess, with confidence).
- **Price tier:** `trait.business_scale`, plus seller AOV vs category AOV (E10).
- **City tier and rural:** city classification (1 metro, 2 tier-2, 3 small town, empty = village or small town) and the state (Hindi belt).
- **Weekday:** the planned call date.
- **Tension:** `state.call_mood` (irate / frustrated / rushed), `state.open_grievance`, `state.call_fatigue`.
