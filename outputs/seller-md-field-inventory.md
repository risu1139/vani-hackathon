# Seller context .md: field inventory

Every data point and sub-field the `.md` returns (SCRUBBER, 100 test sellers). Coverage = sellers with a non-empty value. Names only, no values. Mark **Keep** Y/N; I'll strip the rest.

| Section | ID | Data point | Sub-fields (coverage of 100) | Coverage | Source | Keep |
|---|---|---|---|---|---|---|
| Previous conversations with VANI | G01 | VANI call volume | n_prior_calls_all_history (89), first_call_date_all_history (89), answered_calls_last_90d (56), last_call_date (56), avg_duration_sec (56), older_calls_ignored (43), of_which_last_30d (14), never_reached_by_vani (11) | 100 | ps07_bot_calls (window 90 d; recent = 30 d) | |
| Previous conversations with VANI | G02 | VANI outcome history | outcome_counts_all_history (89), outcome_counts_last_90d (56), meetings_fixed_last_90d (13) | 89 | ps07_bot_calls (all-history = counts only; call_later_busy kept as an outcome, no times) | |
| Previous conversations with VANI | G03 | Last VANI call | last_call (56), note (33), earlier_calls_in_window (23) | 89 | ps07_bot_calls.lead_call_summary (scheduling sentences removed) | |
| Previous conversations with VANI | G04 | Past objections and questions | (single value) | 0 | evaluator objections / seller_questions (last 90 d) | |
| Previous conversations with VANI | G05 | Frustration / bot question / DNC / already-with-executive | undated_apr_sep_flags (lower weight) (54), already_met_or_in_touch (4) | 54 | evaluator se_contact / incorrect_mf (last 90 d) · ps07 seller file (undated) | |
| Previous conversations with VANI | G06 | Memory facts (regex baseline) | source (7), family (7), context (7), date (7), match (7) | 7 | regex over last-90-day summaries + evaluator + seller turns (scheduling families removed) | |
| Previous conversations with VANI | G07 | Speech style | seller_turns (11), words_per_turn (11), words_per_sec (11), latency_repetition (8) | 11 | ps07_call_turns · evaluator latency_repetition (last 90 d) | |
| Previous conversations with VANI | G08 | How past calls ended | how_calls_ended (51), who_ended_call (11) | 51 | evaluator disposition / execdrop (last 90 d) | |
| Previous conversations with VANI | G09 | Bot versions and call triggers heard | bot_versions_heard (56) | 56 | ps07_bot_calls (last 90 d) | |
| Previous conversations with VANI | G10 | Recordings | (single value) | 47 | ps07_bot_calls.call_recording_url (last 90 d) | |
| Previous conversations with VANI | G11 | Per-call signal rows (dated) | days_ago (56), outcome (56), duration_sec (56), date (56), has_evaluator (51), signal_sources (45), signals (45), end_pattern (40), has_transcript (11), ended_by (11) | 56 | ps07_bot_calls + evaluator + seller turns, per answered call in last 90 d (lexicon hits + labels; counts, not scores) | |
| Identity and callee | A01 | Seller GLID | (single value) | 100 | test set stratum = rich, rich sources = 4/8 | |
| Identity and callee | A02 | Company name | api (99), gc (95), so (5) | 99 | users_detail.glusr_usr_companyname · gc_profile · so_sellers | |
| Identity and callee | A03 | Contact person name | glusr_usr_firstname (100), glusr_usr_cfirstname (96), glusr_usr_clastname (86), glusr_usr_lastname (83), glusr_usr_add_contactname (1) | 100 | users_detail (account holder + contact person) | |
| Identity and callee | A04 | Contact designation | users_detail (43), so_sellers (5) | 43 | users_detail.glusr_usr_designation · so_sellers.contact_designation | |
| Identity and callee | A05 | Numbers on the account (type, office-hours status, pickup) | pns_slots (98), all_contact_numbers (98), pns_mapped (91), number_wise_pns_latest (39), per_number_success (32) | 99 | users_pnssetting · users_detail(all_contact_info) · pns_chart_api · byrsupplyapi | |
| Identity and callee | A06 | Past pickup role (DM / family / staff / wrong number) | n_calls_with_disposition_json (51), events (7) | 51 | ps07 evaluator `disposition` | |
| Identity and callee | A07 | Gender / salutation | glusr_usr_gender (2) | 2 | users_detail (often empty; never inferred from names) | |
| Location and language | B01 | City, district, state | seller_city (100), seller_district (100), seller_state (100), city_name (100), state_name (100) | 100 | ps07 seller file · users_detail | |
| Location and language | B02 | Pincode, locality, lat/long | seller_pincode (100), zip (100), address1 (99), seller_latitude (55), seller_longitude (55), seller_locality (36), address2 (13) | 100 | ps07 seller file · btc sellers · users_detail | |
| Location and language | B03 | Languages spoken on real calls | English (28), Hindi (27), Gujarati (5), Marathi (2), Kannada (1), Tamil (1), Bengali (1) | 28 | gc_buyer_call_extractions.languages (1 calls) | |
| Location and language | B04 | Seller's script / Hinglish mix on VANI calls | seller_turns (11), latin_char_share (11) | 11 | ps07_call_turns (speaker = seller) | |
| Location and language | B05 | Preferred language id | users_detail (7) | 7 | users_detail.gl_pref_language_id · so_sellers | |
| Business profile | C01 | Business type | business_type (99), legal_status (99), primary_biz_type (41), biz_type (26) | 100 | ps07 seller file · users_detail | |
| Business profile | C02 | Annual turnover | annual_turnover (89), users_turnover (22), so_gst_turnover (2) | 90 | ps07 seller file · users_detail · so_sellers | |
| Business profile | C03 | Nature of business | nature_of_business_secondary (99), nature_of_business (88) | 99 | ps07 seller file | |
| Business profile | C04 | Business vintage | member_since (100), gst_registration_year (99), service_start (14) | 100 | ps07 seller file · users_detail · byrsupplyapi · queryChartSum | |
| Business profile | C05 | Customer type / plan / paid | users_custtype (100), scorecard_service (100), byr_custtype (99), query_sum_service (99), gc_customer_type (96), gc_is_paid (96), paid_free (95) | 100 | users_detail · gc_profile · cust_scorecard · byrsupplyapi · queryChartSum | |
| Business profile | C06 | Listing status, KYC flags | users_listing_status (100), users_approv (100), listing_status (96), mobile_verified_flag (96), email_verified_flag (96), gst_verified_flag (96), gst_flag (96), is_pan_number_available (96), business_type_flag (96), visiting_card_flag (96), disabled_reason (3) | 100 | gc_profile · users_detail | |
| Business profile | C07 | Employees, year established | employees (29), year_of_estb (19), so_year_established (3), so_employees_id (2) | 32 | users_detail · so_sellers | |
| Categories and products | D01 | Top categories | mcats_api (98), top (94) | 98 | ps07 seller file · blsummarydetails | |
| Categories and products | D02 | Number of categories | by_rank_api (95), num_categories (94) | 95 | ps07 seller file · gl_mcats_prdts_dtls | |
| Categories and products | D03 | Categories by rank, negative, D-rank | category_dtls (100), scorecard_ranks (95), so_categories (3) | 100 | category_dtls · cust_scorecard · so_seller_categories | |
| Categories and products | D04 | Product count and recent changes | prd_mapping_count (100), file (67), added_deactivated (40) | 100 | ps07 seller file · prd_mapping_api · gettopbarsmry | |
| Categories and products | D05 | Product list | api_top_products (99), so_products (3) | 99 | prd_mapping_api · so_products | |
| Categories and products | D06 | Catalogue quality and gaps | filtercount (100), scorecard (99), query_sum_prd_smry (99), byr_curr_prd (99), eng_cqs (60), so_catalog_health (3) | 100 | ps07 seller file · cust_scorecard · queryChartSum · byrsupplyapi · productfiltercount · so_catalog_health | |
| Categories and products | D07 | Active / approved / deactivated products | prd_mapping_count (100), scorecard (98) | 100 | prd_mapping_api · cust_scorecard | |
| Buyer demand and buyleads | E01 | Enquiries received | byr_latest_month (95), topbar (83), monthly_18m (69), gc_enquiries_total (59), file (34) | 96 | ps07 seller file · gc_enquiries · gettopbarsmry · byrsupplyapi · queryChartDtls | |
| Buyer demand and buyleads | E02 | Latest enquiries | source_module (59), subject (59), product_name (59), enquiry_date (59), message (59), buyer_country (59), read_status (59), buyer_city (58), buyer_state (58), first_read_date (50), buyer_company (48), buyer_designation (19), search_keyword (12) | 59 | gc_enquiries_received (latest 5) | |
| Buyer demand and buyleads | E03 | Responsiveness | gc_enquiries (59), byr (50), gc_enquiries_read (50), gc_median_hours_to_first_read (46), file (42), gc_seller_replies (30), scorecard (25), callback_speed (15) | 90 | gc_enquiries · gc_enquiry_messages · ps07 seller file · cust_scorecard · cust_wh_apiv2 · byrsupplyapi | |
| Buyer demand and buyleads | E04 | Buyleads bought | gc_bought (12), gc_by_mcat_rank (12), gc_credits_used (12), api_bl_pur (12), byr (12), scorecard (10), gc_top_keywords (5) | 14 | gc_buyleads_bought · glusr_bl_summaryv2 · cust_scorecard · byrsupplyapi | |
| Buyer demand and buyleads | E05 | BL credits and lapsed credits | bl_credits_alctd (13), current_balance (12), bl_credit_lapsed (10), bl_credit_lapsed_i (10), last_cons_date (10) | 13 | cust_scorecard (latest month) | |
| Buyer demand and buyleads | E06 | BL consumption speed | bl_pur_0to4hrs_per (12), bl_pur_4to24hrs_per (12), cons_0_4_hrs (10), bl_pur_0to4hrs_frm_appr (10), bl_pur_gt24hrs_per (9), cons_4_24_hrs (7), bl_pur_0to15mins_frm_appr (7), cons_grter_1day (5), bl_pur_15to30mins_frm_appr (4) | 13 | cust_scorecard · byrsupplyapi | |
| Buyer demand and buyleads | E07 | BL not-interested reasons | scorecard (1) | 1 | cust_scorecard · glusr_bl_summaryv2 | |
| Buyer demand and buyleads | E08 | Local competition | counts (95), competitors (95) | 95 | nsdprepplus | |
| Phone behaviour and timing | F01 | Buyer (PNS) calls received / answered | glmisccount (42), topbar (42), file (30), scorecard (11) | 54 | ps07 seller file · glmisccount · cust_scorecard · gettopbarsmry | |
| Phone behaviour and timing | F02 | Buyer-call talk time | gc_buyer_calls (52), gc_connected (37), gc_median_talk_sec (37), api_avg_talktime (32) | 55 | pns_chart_api · gc_buyer_calls_received | |
| Phone behaviour and timing | F03 | Pickup ratio and callbacks | file (100), callback_speed (12) | 100 | ps07 seller file · cust_wh_apiv2 | |
| Phone behaviour and timing | F08 | Last seen on IndiaMART | glusr_usr_lastlogin (100), glusr_usr_lastmodified (100), glusr_usr_ext_modified_date (100) | 100 | users_detail | |
| Human relationship | H01 | Executive calls | dsr_monthly_api (100), exec_calls (12), last (12), modules (12), answered (11) | 100 | ps07_executive_calls (last 90 d) · getgldsrcount | |
| Human relationship | H02 | Account managers | custtype_name (99), assignedto (99), assignedto_name (99), assignedto_email (99), vertical_name (99), teleassignedto (99), teleassignedto_name (99), teleassignedto_email (99), tele_vertical (99), member_since (99), assignedto_mobile (62), teleassignedto_mobile (62), glusr_usr_comp_logo_img (4) | 99 | byrsupplyapi.GL_DTL (sales + tele account managers) | |
| Human relationship | H03 | Meetings | se_contact (11), scorecard (3) | 13 | evaluator se_contact · cust_scorecard · getgldsrcount | |
| Account health and risk | I01 | Complaints | cmplnts_cnt (1), closed_cmplnts (1) | 1 | cust_scorecard (latest month) | |
| Account health and risk | I02 | Renewal / payment | gap (100), proxy_service_start (14) | 100 | GAP | |
| Account health and risk | I03 | Churn / risk | gap (100), proxies (100) | 100 | GAP + cust_scorecard | |
| Account health and risk | I04 | Ratings | scorecard (34), byr (34) | 35 | cust_scorecard · byrsupplyapi | |
| Other channels | J01 | WhatsApp delivery and reads | messages (71), by_sender (71), status (71), last (71) | 71 | gc_whatsapp_messages | |
| Other channels | J02 | WhatsApp chatbot conversations | turns (63), intents (63), latest_seller_messages (63), api_conversation (47) | 77 | gc_whatsapp_chatbot_conversations · getwaconv | |
| Other channels | J03 | Buyer-call extractions | is_b2b (28), file_intent (28), categories (28), languages (28), products_discussed (28), call_date (28), seller_role_on_call (28), stock_status (27), specs_discussed (24), prices_quoted (16) | 28 | gc_buyer_call_extractions | |
| This call's context | K01 | Call trigger | latest_trigger_bucket (100), latest_lead_sent (100) | 100 | btc_attempts (latest) = why VANI is calling; live value comes from the dialler | |
| This call's context | K03 | Local time / season | festive_season_window (100) | 100 | calendar month heuristic (call timing is not decided here) | |
| This call's context | K04 | Dialled number type | gap (100), candidate_slots (98) | 100 | GAP | |

Excluded by design (not in the .md): F04 best time, F05 unanswered attempts, F06 promised callback, F07 do-not-call hours, K02 attempt number (scheduling). ID numbers are scrubbed from points.json.
