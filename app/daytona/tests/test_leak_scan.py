"""deploy.leak_scan: real names, slugs, phones and emails refuse the upload; a missing map fails closed."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import deploy as D  # noqa: E402


def setup(tmp_path, monkeypatch, text):
    monkeypatch.setattr(D, "ROOT", str(tmp_path))
    src = tmp_path / "data" / "agent_export" / "p1"
    src.mkdir(parents=True)
    (src / "core.md").write_text(text, encoding="utf-8")
    (tmp_path / "data" / "agent_export_maps").mkdir(parents=True)
    (tmp_path / "data" / "agent_export_maps" / "p1.json").write_text(
        json.dumps({"tokens": {"{COMPETITOR_1}": ["Laxmi Enterprises"], "{SALES_EXEC}": ["Rakesh Verma"]}}), encoding="utf-8")
    return str(src)


@pytest.mark.parametrize("text,ok", [
    ("handler {SALES_EXEC}, peer {COMPETITOR_1}", True),
    ("handler Rakesh Verma", False), ("Laxmi Enterprises, Surat", True),
    ("call 98765 43210", False), ("mail a.b@example.com", False), ("lead id 152766804152", True)])
def test_leak_scan(tmp_path, monkeypatch, text, ok):
    src = setup(tmp_path, monkeypatch, text)
    assert (D.leak_scan(src, "p1") == []) is ok


def test_missing_map_fails_closed(tmp_path, monkeypatch):
    src = setup(tmp_path, monkeypatch, "x")
    os.remove(tmp_path / "data" / "agent_export_maps" / "p1.json")
    with pytest.raises(SystemExit):
        D.leak_scan(src, "p1")
