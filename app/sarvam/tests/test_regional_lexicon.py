"""lex-v2 (2026-10-10 playground smoke): Telugu 'busy' was neutral and romanised Telugu was read as English."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import vani_tools as T  # noqa: E402


def test_telugu_rushed():
    assert T.classify("ఇప్పుడు బిజీగా ఉన్నాను, త్వరగా చెప్పండి.")[0] == "rushed"


def test_romanised_regional_is_not_english():
    assert T.script_of("Phone lone cheppandi, meeting enduku?") != "latn"
    assert T.script_of("abhi busy hoon baad mein call karo") != "latn"


def test_real_english_is_english():
    assert T.script_of("Can you please tell me what this is about?") == "latn"


def test_regional_cues():
    cases = {"கால் பண்ணாதீங்க": "opt_out", "అర్థం కాలేదు": "confused", "మీరు bot ఆ? మనిషేనా?": "bot_question",
             "ಸಮಯ ಇಲ್ಲ": "rushed", "ফোন করবেন না": "opt_out", "समजलं नाही": "confused", "എത്ര തവണ": "frustrated",
             "మీటింగ్ ఎప్పుడు": "interested"}
    for utt, mode in cases.items():
        assert T.classify(utt)[0] == mode, utt


def test_regional_opt_out_with_later_is_callback():
    assert T.classify("ఇప్పుడు కాల్ చేయకండి, తర్వాత చేయండి")[0] == "rushed"


def test_plain_yes_stays_neutral():
    assert T.classify("అవును, చెప్పండి.")[0] == "neutral"
