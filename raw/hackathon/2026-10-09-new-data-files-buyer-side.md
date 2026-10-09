# New files added to data/ on 2026-10-09 (structure only; contents stay in data/)

Added by the team lead on 2026-10-09 ~14:40.

1. **Current Definitions of Call Quality Matrix being used in VANI.png**. This is the production VANI (buyer side) QA rubric. Each parameter has a definition, a Fatal condition and a Non-Fatal condition. The parameters are: Outcome Accuracy, Quantity Accuracy (numeric), Quantity Unit Accuracy, Quantity Probing Error, Qty Missed Opportunity, Spec1/Spec2 Accuracy, Spec Missed Opportunity, Looping Behavior (probing more than 1+2 times; Fatal if the buyer gets irritated or the call disconnects), WER, Additional_details, OnCall AstBuy Error, Product Change/No Product Accuracy, Category ISQ's Error, MCAT/Search errors, Dead air (>5 s normally, 8 s with noise), Overall Call (Pass / Fatal / Non-fatal), and Additional Observation (e.g. pronunciation).
2. **Call_Logs_Hackathon.csv**: 1,000 buyer-side call records from 5–9 Oct 2026, with 825 distinct GLIDs and 717 recording URLs (557 on squadiq S3, 152 on agents.sarvam.ai). disposition_remarks: BL Enriched 449, Abruptly Disconnected 118, No Enrichment Scope 102, Technical Issue 80, BL Approved 64, Queue Drop 44, Foreign/Disabled 35, No Product Requirement 34, other ≤12. Answered: 733 yes, 125 no, 142 null. Buyer side, not seller side.
3. **Sarvam Prompt - Buyer Side VANI.docx**: the production buyer-side VANI prompt on Sarvam, about 159K characters and 1,591 paragraphs. Structure:
   - Global role and persona: a business development executive; never claim to be human; never assure.
   - Languages limited (English, Hindi, Telugu).
   - Lead quality mandate.
   - **Jinja-style conditional sections keyed by variables** (e.g. `{%if is_enrich=='1' and ast_seller_pns != ""%}`).
   - A collection-control block with **per-field ask limits** (product 4, quantity 3, each spec 2, name/city/state 3, transfer consent 2) and a `@call_step` variable set to LOOP_DETECTED when a field is exhausted.
4. **Seller Enrichment zip** (75 MB): the Seller Onboarding (PS06) dataset in 4 parts:
   - sellers, KYC and lookups;
   - category specs (ref_category_specs);
   - products, part 1;
   - products, part 2.

   It includes the category taxonomy and a data dictionary, and is already covered by the data agent (151 sellers overlap PS07).

Relevance to PS04 (seller-side persona):
- (a) The production prompt pattern shows variable-switched prompt sections, step-state variables and hard ask limits, which can be used for persona sections, plan branches and loop guards.
- (b) The quality matrix gives the reviewer a Fatal / Non-Fatal format to mirror. Looping, dead air and WER apply to seller calls too.
