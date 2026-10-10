"""Key facts must never cut inside a value (fact check 2026-10-10: gc_credits_used 13000 showed as 1300)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from seller_context_builder import _short  # noqa: E402


def test_dict_cut_at_whole_field():
    v = {"bl_bought": 412, "long_note": "x" * 150, "gc_credits_used": 13000, "other": 5}
    out = _short(v, 200)
    assert "1300" not in out.replace("13000", "")  # never a cut number
    assert "more, see source" in out


def test_number_kept_whole():
    out = _short({"a": "y" * 170, "gc_credits_used": 13000}, 180)
    assert "13000" in out or "gc_credits_used" not in out


def test_short_string_unchanged():
    assert _short("Surat, Gujarat") == "Surat, Gujarat"


def test_long_string_word_boundary():
    out = _short("word " * 60, 50)
    assert out.endswith("(see source)") and "wor …" not in out
