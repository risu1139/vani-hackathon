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


def test_phone_call_2026_10_10_lines():
    """lex-v3: the real phone test. The fatal miss was a Kannada 'no, no' that VANI pushed past."""
    assert T.classify("ಬೇಡ ಬೇಡ ಗೊತ್ತಿಲ್ಲ.")[0] == "declined"  # 2026-10-10 user rule: "no" is answered, the call is not ended
    assert T.classify("लीड्स की क्वालिटी बहुत ही बेकार आती है इसलिए मैं कंज्यूम नहीं कर रहा था।")[0] == "frustrated"
    assert T.classify("అది బై రేట్ సరిగ్గా రావట్లేదు, క్వాలిటీ బాగాలేదు. అందుకని నేను వాడట్లేదు.")[0] == "frustrated"
    assert T.classify("ಚಂಗಾ, ಗೊತ್ತಿಲ್ಲ")[0] == "confused"
    assert T.classify("సరే అండి.")[0] == "neutral"
