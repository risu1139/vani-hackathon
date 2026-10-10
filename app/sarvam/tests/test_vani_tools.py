"""Offline tests for app/sarvam/vani_tools.py: classifier, sensitivity, directives, the tools on a fake context.
Run: python -m pytest app/sarvam/tests -q"""
import asyncio
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import vani_tools as vt  # noqa: E402
from sarvam_conv_ai_sdk.tool import SarvamToolLanguageName as L  # noqa: E402
from sarvam_conv_ai_sdk import SarvamToolContext, SarvamOnStartToolContext  # noqa: E402

CONTRACT = json.loads((Path(__file__).resolve().parents[2] / "contracts" / "sarvam_vars.contract.json").read_text(encoding="utf-8"))
ALL_VARS = list(CONTRACT["set_before_call"]) + list(CONTRACT["set_during_call_by_tools"])

# (utterance, expected mode) - the 2026-10-09 test set, the Jev-labelled ASR variants, the three T4 lexicon gaps,
# and PS07-style romanised lines.
GOLD = [
    ("अभी बिज़ी हूँ यार, जल्दी बोलो क्या है", "rushed"),
    ("अबे बिजी हूँ यार।", "rushed"),
    ("अभी बिजी हूँ यार, बाद में बात करते हैं।", "rushed"),
    ("Abhi busy hoon yaar, jaldi bolo kya hai", "rushed"),
    ("Sir main abhi driving kar raha hoon", "rushed"),
    ("time nahi hai abhi, baad mein call karo", "rushed"),
    ("abhi call mat karo, shaam ko karna", "rushed"),
    ("कितनी बार कॉल करोगे, परेशान कर दिया है", "frustrated"),
    ("फिर से पूछ रहा हूँ, प्राइस बताओ वरना फोन रख दो", "frustrated"),
    ("aap log baar baar phone karte ho", "frustrated"),
    ("समझ नहीं आया, क्या मतलब मीटिंग?", "confused"),
    ("samajh mein nahi aaya aap kya bol rahe ho", "confused"),
    ("awaaz nahi aa rahi, dobara boliye", "confused"),
    ("अच्छा, ये कैसे काम करता है? कितना चार्ज है?", "interested"),
    ("Achha haan yaad aaya. Par paise kitne lagenge?", "interested"),
    ("Theek hai, mil lete hain.", "interested"),
    ("સારું, બલ્ક બાયર્સ જોઈએ છે. મીટિંગ ક્યારે કરશો?", "interested"),
    ("अच्छा ठीक है, पर एग्जैक्ट प्राइस बताओ कितने का प्लान है?", "interested"),
    ("Aap bot ho kya? Recorded call hai?", "bot_question"),
    ("aap insaan ho ya robot?", "bot_question"),
    ("मुझे कॉल मत करो, मेरा नंबर हटा दो", "opt_out"),
    ("please dobara call mat karna", "opt_out"),
    ("मेरा नंबर डिलीट करो", "opt_out"),
]
NEUTRAL = ["हाँ जी बोलिए, कौन बोल रहा है?", "ओके ओके", "ok", "haan", "hmm", "हम्म, ठीक है", "अच्छा, ठीक है।",
           "मैं owner नहीं हूँ, manager हूँ. Owner बाहर गए हैं.", "Haan ji, main hi owner hoon. Boliye.",
           "Leads ki zarurat nahi hai, pehle se bahut aa rahi hain.", "haan samajh gaya", "iska koi matlab nahi hai",
           "humare paas CNC machine hai", "I have finished recording you may hang up", "સારું, આગળ બોલો.",
           "Kal shaam paanch baje aa jaiye.".replace("aa jaiye", "theek rahega"), "हाँ जी।", "पहले ये बताओ आप कौन हो?"]


@pytest.mark.parametrize("utt,mode", GOLD)
def test_gold(utt, mode):
    assert vt.classify(utt)[0] == mode, (utt, vt.classify(utt))


@pytest.mark.parametrize("utt", NEUTRAL)
def test_neutral_no_switch(utt):
    # plan 5f: a question ("kaun bol raha hai?") is answered (question mode), never a pitch or a meeting ask
    assert vt.classify(utt)[0] in ("neutral", "question"), (utt, vt.find_cues(utt))


def test_interest_strict_bare_fillers():
    for u in ("ok", "okay", "haan", "haan ji", "hmm", "achha", "ठीक है", "हाँ", "ओके"):
        assert vt.classify(u)[0] != "interested"


def test_not_wanted_blocks_interest():
    assert vt.classify("kitne ka bhi ho, nahi chahiye")[0] == "declined"  # not interest, and not an end-call request


def test_strong_beats_weak_across_modes():
    assert vt.classify("jaldi aa jaiye kal")[0] == "interested"  # weak rushed 'jaldi' vs strong interested


def test_returns_cue():
    mode, strength, cue, _ = vt.classify("abhi busy hoon")
    assert (mode, strength, cue) == ("rushed", "strong", "busy")


def test_scripts():
    assert vt.script_of("ગુજરાતીમાં વાત કરો ને") == "gujr"
    assert vt.script_of("अभी बिज़ी हूँ") == "deva"
    assert vt.script_of("I am busy right now please call later") == "latn"
    assert vt.script_of("मैं owner नहीं हूँ") == "deva"
    assert vt.script_of("ok") == "none"


# ---------------- sensitivity
def test_decide():
    assert vt.decide("rushed", "weak", "high", [])[0]
    assert not vt.decide("rushed", "weak", "normal", [])[0]
    assert vt.decide("rushed", "weak", "normal", ["rushed"])[0]
    assert vt.decide("rushed", "strong", "normal", [])[0]
    assert not vt.decide("rushed", "strong", "low", [])[0]
    assert vt.decide("rushed", "strong", "low", ["rushed"])[0]
    for m in ("opt_out", "frustrated", "bot_question"):
        assert vt.decide(m, "strong", "low", [])[0]


# ---------------- directives
STYLES = ["P0", "P1", "P2", "P3", "P4", "P5", "P6", "COMPOSED", "", "XYZ"]


@pytest.mark.parametrize("mode", list(vt._D))
@pytest.mark.parametrize("style", STYLES)
def test_directive_caps(mode, style):
    did, cap, text = vt.directive(mode, style, "Gujarati")
    base = mode.replace("_pressed", "")
    assert cap <= vt.MODE_CAP[base], (did, cap)
    assert f"Max {cap} words" in text or f"max {cap} words" in text, text
    assert len(text.split()) <= 45, (did, len(text.split()))
    assert "{" not in text
    assert did.startswith(mode + ".")
    low = text.lower()
    assert "branch manager" not in low and "account manager" not in low and "personally" not in low
    if "ai" in re.findall(r"[a-z]+", low):
        assert "do not say ai" in low or "never ai" in low or "never say ai" in low  # AI only appears as a prohibition


def test_directive_style_variants_differ():
    assert vt.directive("rushed", "P4")[2] != vt.directive("rushed", "P6")[2]
    assert vt.directive("neutral", "P4")[1] == 10 and vt.directive("neutral", "P0")[1] == 20


# ---------------- tools on a fake context
def _ctx(**vals):
    av = {k: "" for k in ALL_VARS}
    av.update(seller_mode="neutral", switch_log="[]", meeting_fixed="no", persona_style_id="P0",
              switch_sensitivity=json.dumps({"rushed": "normal"}), decision_id="d-test", persona_language="Hindi")
    av.update(vals)
    return SarvamToolContext(agent_variables=av, internal_variables={}, language=L.HINDI,
                             allowed_languages=[L.HINDI, L.GUJARATI, L.ENGLISH], state="start", next_valid_states=[],
                             engagement_metadata={"interaction_id": "x", "app_id": "a", "app_version": 1})


def _say(ctx, utt, lang="hindi"):
    out = asyncio.run(vt.ReadSellerSignal(seller_utterance=utt, language=lang).run(ctx))
    return out, json.loads(ctx.agent_variables["switch_log"])[-1]


def test_tool_rushed_row_fields():
    ctx = _ctx()
    out, row = _say(ctx, "अभी बिज़ी हूँ यार, जल्दी बोलो क्या है")
    assert ctx.agent_variables["seller_mode"] == "rushed"
    for k in ("t", "turn", "utt", "lang", "from", "to", "cue", "directive_id", "change", "reason", "ms", "decision_id"):
        assert k in row
    assert row["cue"].startswith("busy") or "जल्दी" in row["cue"] or "बिजी" in row["cue"]
    assert row["directive_id"] == "rushed.base.v1" and row["decision_id"] == "d-test"
    assert "switch_log" not in out.message_to_llm and "[" not in out.message_to_llm


def test_tool_weak_cue_waits_under_normal_switches_under_high():
    ctx = _ctx()
    _, row = _say(ctx, "thodi der mein")
    assert row["to"] == "neutral" and "waiting" in row["reason"]
    _, row = _say(ctx, "abhi nahi yaar")
    assert row["to"] == "rushed" and "second" in row["reason"]
    ctx = _ctx(switch_sensitivity=json.dumps({"rushed": "high"}))
    _, row = _say(ctx, "thodi der mein")
    assert row["to"] == "rushed"


def test_tool_dedupe_and_valid_json():
    ctx = _ctx()
    _say(ctx, "समझ नहीं आया")
    out, row = _say(ctx, "समझ नहीं आया")
    assert row["dup"] is True and out.message_to_llm.startswith("No change")
    for i in range(40):
        _say(ctx, f"line {i}")
    log = json.loads(ctx.agent_variables["switch_log"])
    assert len(log) == vt.LOG_ROWS


def test_tool_bot_question_sidestep_then_pressed():
    ctx = _ctx()
    out1, r1 = _say(ctx, "aap bot ho kya?")
    out2, r2 = _say(ctx, "sach batao, robot ho?")
    assert r1["directive_id"].startswith("bot_question.") and "virtual assistant" not in out1.message_to_llm
    assert r2["directive_id"].startswith("bot_question_pressed.") and "virtual assistant" in out2.message_to_llm


def test_tool_language_switch_by_script():
    ctx = _ctx()
    _say(ctx, "हाँ जी बोलिए")
    out, row = _say(ctx, "ગુજરાતીમાં વાત કરો ને, મને હિન્દી ઓછું ફાવે છે.")
    assert row["to"] == "language_switch" and "Gujarati" in out.message_to_llm and "deva->gujr" in row["reason"]
    assert ctx.language == L.GUJARATI


def test_tool_language_switch_from_start_language():
    ctx = _ctx(persona_language="GUJARATI")
    out, row = _say(ctx, "अभी बिज़ी हूँ यार")
    assert row["to"] == "rushed" and "Reply in Hindi" in out.message_to_llm


def test_tool_opt_out_ends():
    ctx = _ctx()
    out, row = _say(ctx, "मुझे कॉल मत करो, मेरा नंबर हटा दो")
    assert ctx.end_conversation and row["to"] == "opt_out" and out.message_to_user


def test_book_meeting():
    ctx = _ctx()
    out = asyncio.run(vt.BookMeeting(slot="kal shaam 5 baje", place="shop").run(ctx))
    assert ctx.agent_variables["meeting_fixed"] == "yes" and "kal shaam 5 baje" in ctx.agent_variables["meeting_slot"]
    assert out.message_to_llm.startswith("Booked")
    out = asyncio.run(vt.BookMeeting(slot="").run(_ctx()))
    assert out.message_to_llm.startswith("Not booked")


def test_onstart():
    av = {k: "" for k in ALL_VARS}
    av.update(persona_voice_id="uuid-x", persona_pace="1.4", persona_pitch="0.05", persona_language="GUJARATI",
              persona_opening="નમસ્તે")
    ctx = SarvamOnStartToolContext(agent_variables=av, user_identifier="u", initial_state_name="start",
                                   initial_language_name=L.HINDI,
                                   engagement_metadata={"interaction_id": "x", "app_id": "a", "app_version": 1})
    ctx = asyncio.run(vt.OnStart().run(ctx))
    assert ctx.initial_language_name == L.GUJARATI and ctx.initial_bot_message == "નમસ્તે"
    assert ctx.text_to_speech_config.speech_settings.pace == 1.25  # clamped
    assert ctx.internal_variables["start_script"] == "gujr"


def test_tool_only_contract_variables():
    src = (Path(vt.__file__)).read_text(encoding="utf-8")
    used = set(re.findall(r'_(?:set)?var\(context, "([a-z_]+)"', src))
    assert used <= set(ALL_VARS), used - set(ALL_VARS)


@pytest.mark.parametrize("slot,ok", [
    ("kal shaam 5 baje", True), ("kal subah 10 baje", True), ("Monday 11 am", True), ("రేపు సాయంత్రం 5 గంటలకు", True),
    ("kal 3 baje", True), ("kal shaam 7 baje", False), ("raat 9 baje", False), ("subah 8 baje", False), ("8 baje", False),
    ("6 pm", False), ("kal milte hain", True)])
def test_slot_inside_work_hours(slot, ok):
    assert (vt.slot_check(slot) == "") is ok


def test_book_meeting_refuses_outside_hours():
    ctx = _ctx()
    out = asyncio.run(vt.BookMeeting(slot="kal raat 8 baje").run(ctx))
    assert out.message_to_llm.startswith("Not booked") and ctx.agent_variables.get("meeting_fixed") != "yes"


def test_time_named_nudges_booking():
    ctx = _ctx()
    out, row = _say(ctx, "theek hai kal shaam 4 baje aa jaiye")
    assert "book_meeting" in out.message_to_llm and "book_meeting nudge" in row["reason"]
    out, row = _say(ctx, "mere 5 credits bache hain")
    assert "book_meeting" not in out.message_to_llm


def test_hindi_after_marathi_start_switches():
    """2026-10-10 call: Marathi start, seller asked in Hindi; same script, so the old check missed it."""
    assert vt.deva_lang("आप कोण बोल रहे हो?") == "Hindi"
    assert vt.deva_lang("तुम्ही कोण बोलता आहात?") == "Marathi"
    assert vt.deva_lang("हॅलो.", "marathi") == "Marathi"
    ctx = _ctx(persona_language="MARATHI")
    out, row = _say(ctx, "हॅलो.", "marathi")
    assert "Hindi" not in out.message_to_llm
    out, row = _say(ctx, "आप कौन बोल रहे हो? मुझे हिंदी में बात करनी है")
    assert "Hindi" in out.message_to_llm and "Marathi->" not in row["reason"]
    out, row = _say(ctx, "हाँ बताइए क्या बात है")
    assert "Reply in Hindi" not in out.message_to_llm or row["to"] == "language_switch"  # already Hindi: no second switch


@pytest.mark.parametrize("utt,mode,ends", [
    ("नहीं, नहीं करनी मुझे मीटिंग तुमसे।", "declined", False), ("not interested", "declined", False),
    ("mujhe baat nahi karni", "declined", False), ("ಬೇಡ ಬೇಡ", "declined", False),
    ("call mat karo mujhe", "opt_out", True), ("कॉल काट दो", "opt_out", True), ("please cut the call", "opt_out", True)])
def test_only_explicit_requests_end_the_call(utt, mode, ends):
    """User rule 2026-10-10: 'not interested' / 'nahi baat karni' never ends the call; only an explicit request does."""
    ctx = _ctx()
    out, row = _say(ctx, utt)
    assert row["to"] == mode and bool(ctx.end_conversation) is ends


# ---------------------------------------------------------------- plan 5f: R1 answer-first, R2 ask grant, R4 handler line
@pytest.mark.parametrize("utt,lang", [("कितने बजे आओगे कल?", "hindi"), ("meeting kab hogi", "hindi"),
                                      ("రేపు సాయంత్రం ఐదు గంటలకు రండి", "telugu"), ("kal shaam 4 baje aa jao", "hindi")])
def test_time_or_interest_beats_question(utt, lang):
    """review note 1: 'kab aaoge' / a named time is interest, never 'question' (which would forbid the ask)."""
    ctx = _ctx()
    out, row = _say(ctx, utt, lang)
    assert vt.classify(utt)[0] == "interested" or vt.time_mention(utt)
    assert row["ask_ok"] is True and "You may ask" in out.message_to_llm


@pytest.mark.parametrize("utt,lang", [("अच्छा, किस तरह की लीड आती है?", "hindi"), ("ఎన్ని లీడ్స్ వచ్చాయి", "telugu"),
                                      ("எத்தனை லீட்ஸ் வந்தது", "tamil")])
def test_question_is_answered_without_ask(utt, lang):
    ctx = _ctx()
    out, row = _say(ctx, utt, lang)
    assert vt.classify(utt)[0] == "question" and row.get("overlay") == "question" and row["ask_ok"] is False         and "Do NOT ask" in out.message_to_llm


@pytest.mark.parametrize("utt,lang", [("कौन है मेरा एग्जीक्यूटिव? कौन आएगा?", "hindi"), ("executive ఎవరు వస్తారు", "telugu")])
def test_handler_question_gets_the_handler_line(utt, lang):
    ctx = _ctx(handler_line="our IndiaMART team handles your account; the executive will introduce themselves when they call")
    out, row = _say(ctx, utt, lang)
    assert row.get("overlay") == "ask_handler" and "introduce themselves" in out.message_to_llm and "Do NOT ask" in out.message_to_llm
    out, row = _say(_ctx(), utt, lang)  # no variable: the team sentence, never empty
    assert "IndiaMART team handles your account" in out.message_to_llm


def test_ask_never_twice_in_a_row():
    ctx = _ctx()
    grants = []
    for u in ("haan boliye", "achha", "theek hai", "haan", "accha ji", "theek"):
        out, row = _say(ctx, u)
        grants.append(row["ask_ok"])
    assert grants == [False, True, False, True, False, True], grants  # opening first; then VANI decides, never two turns running


# review of the 5f build: whole-token question words, no generic name questions, overlays, booking nudge wins
@pytest.mark.parametrize("utt", ["मैंने किसी को नहीं बोला", "किसान लोग आते हैं", "ठीक है, कबाड़ का काम है",
                                 "আমাকে কিছু বলেননি, কিন্তু কাজ চলছে", "ਮੈਂ ਕੰਮ ਕੀਤਾ ਹੈ", "હું કામ કરું છું કેમકે ઓર્ડર છે",
                                 "తాకే వస్తువులు ఉన్నాయి", "என் கடை திறந்திருக்கு"])
def test_statements_are_not_questions(utt):
    assert vt.classify(utt)[0] != "question", (utt, vt.find_cues(utt))


@pytest.mark.parametrize("utt", ["aapka naam kya hai", "product ka naam batao", "आपका नाम क्या है?"])
def test_generic_name_question_is_not_handler(utt):
    assert vt.classify(utt)[0] != "ask_handler"


def test_question_overlay_applies_at_once_and_leaves_seller_mode():
    ctx = _ctx()
    out, row = _say(ctx, "किस तरह की requirements हैं?")
    assert row.get("overlay") == "question" and "Answer it fully" in out.message_to_llm
    assert ctx.agent_variables["seller_mode"] in ("neutral", "language_switch")


def test_named_time_booking_nudge_wins_over_no_ask():
    ctx = _ctx()
    out, row = _say(ctx, "समझ नहीं आया, कल 4 बजे आ जाओ")
    assert "book_meeting" in out.message_to_llm and "Do NOT ask" not in out.message_to_llm


def test_overlay_keeps_frustrated_mode():
    """review: a frustrated seller asking 'kitne leads aaye?' gets the question directive, stays frustrated, no ask."""
    ctx = _ctx(seller_mode="frustrated")
    out, row = _say(ctx, "kitne leads aaye?")
    assert row.get("overlay") == "question" and "Answer it fully" in out.message_to_llm
    assert ctx.agent_variables["seller_mode"] == "frustrated" and row["ask_ok"] is False


def test_question_from_the_models_flag_in_any_language():
    """generic: the model marks a seller question in any language; the tool answers it without a meeting ask."""
    ctx = _ctx()
    out = asyncio.run(vt.ReadSellerSignal(seller_utterance="ଆପଣଙ୍କ ପାଖରେ କେତେ ଲିଡ୍ ଅଛି", language="other",
                                          seller_asked_question=True).run(ctx))
    row = json.loads(ctx.agent_variables["switch_log"])[-1]
    assert row.get("overlay") == "question" and "Do NOT ask" in out.message_to_llm


def test_booking_reply_asks_anything_else_and_does_not_close():
    out = asyncio.run(vt.BookMeeting(slot="kal shaam 4 baje").run(_ctx()))
    assert "anything" in out.message_to_llm and "Do not end the call" in out.message_to_llm and "close the call" not in out.message_to_llm
