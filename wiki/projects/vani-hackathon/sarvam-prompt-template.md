# Sarvam prompt template: the target format for a per-seller VANI persona

Sources: [[2026-10-10-sarvam-prompt-template-example]] · [[2026-10-09-new-data-files-buyer-side]]

**What this is.** Our persona composer ([[system-design]] B4) and variable compiler (B6) must output a Sarvam agent in this template's shape. The user said so on 2026-10-10. The example is a B2B discovery agent called "Ananya". VANI's seller call reuses the same skeleton, filled with IndiaMART content and per-seller variables.

## Sections, in order

| Section | What it holds | VANI per-seller equivalent |
|---|---|---|
| **Greeting** | Opening line with variables (`partnerName`, `userName`) | `persona_opening` / `initial_message`: name, company, hook |
| **Translations** | Per-language versions (empty in the example) | Hindi / Hinglish / regional lines in native script |
| **Persona** | Name, role, tone ("warm, consultative, curious"), AI-disclosure rule, talk/listen ratio | Composed persona: voice gender and name, tone, formality, warmth, sophistication level |
| **Environment & Situation** | Channel, who the users are, why this call (`priorTouchpointSummary`), internal context | Seller context summary: trigger bucket, past calls, executive contact |
| **Objective** | One sentence | Book a meeting / get the seller to act on the hook |
| **Speaking Style** | Words per turn (<30), one question at a time, re-asks shorter, salutation, register and code-mix, terms kept as-is, "hmm/haan/ok = engagement, not an answer", paraphrase when unclear | Brevity, language mix, salutation, filler rules; mid-call switch directives change these |
| **Facts** | What the call is and isn't; internal-only variables; ask limits (budget nudges = 2) | `verified_facts` (what VANI may say), category value / AOV lines, ask limits |
| **Conversation Guidelines** | Phases 1–9: identity → discovery → fit and next step → graceful close → callback → wrong person → escalation (DND, mental health, legal, hostile, deceased, supervisor) | Call plan: identity → hook → objection playbook → meeting ask → close; same exit phases |
| **Guardrails** | No pricing or promises; summarise before the next step; booking only after a tool confirms; keep internal data private | Same, plus no human or "branch manager" claim, no unverifiable claims |
| **Date Resolution** | Resolve relative dates against `current_date` and confirm | Same, for callback and meeting times |

## Variables in the example

- **Inputs set at call start:** `partnerName`, `userName`, `companyName`, `productCategory`, `priorTouchpointSummary`, `campaignId`, `crmDealStage`, `typicalCustomerPainPoints`, `qualifyingSegments`, `disqualifyingSignals`, `proposedNextStepDefault`, `smeAvailableForFollowup`, `salesRepName`, `salesRepPhone`, `preferredCallbackWindow`, `dndRegistrationLine`, `customerCareNumber`, `current_date`.
- **Captured during the call:** `pain_points_mentioned`, `current_state_of_solving`, `authority_level`, `budget_indication`, `timeline_to_decide`, `chosen_next_step`, `next_step_date_time`, `alt_contact_number`.
- **Tools:** `book_next_step` (claim a booking only on its confirmation) and `end_interaction`.

## What this means for our build (as of 2026-10-10)

- The persona decision should produce **section texts plus variables**, not one free prompt. Fixed sections (escalation, guardrails, date resolution) stay constant. Persona, Speaking Style, Greeting, Facts and the phase wording change per seller.
- Per-call values go only through agent variables ([[system-design]]). The template's internal-only variables map to our seller context (category AOV, turnover band, past-call facts), which VANI uses but never reads aloud.
- The production buyer-side prompt uses the same idea with `{% if %}` blocks ([[2026-10-09-new-data-files-buyer-side]]). A `current_persona` / `seller_mode` variable can switch the Speaking Style block mid-call.
