"""M19: pseudonymous export with a hard PII gate. Synthetic seller only."""
import json
import os

import export_for_agent as E

GLID = "900000002"
KEY = "test-key-not-secret"


def make_context(root, extra_md=""):
    folder = root / "contexts" / GLID
    (folder / "calls").mkdir(parents=True)
    ctx = {"glid": GLID, "points": {
        "A01": {"value": int(GLID), "source": "test"},
        "A02": {"value": {"api": "Zorbax Fabricators Pvt Ltd", "gc": "Zorbax Fabricators"}, "source": "users_detail"},
        "A03": {"value": {"glusr_usr_firstname": "Quentaro", "glusr_usr_lastname": "Velmani",
                          "glusr_usr_cfirstname": "Ishvani", "glusr_usr_clastname": "Velmani"}, "source": "users_detail"},
        "C09": {"value": {"company": {"DIR_SEARCH_COMPANY": "Zorbax Fabricators", "DIR_SEARCH_CONTACTPERSON": "Mr. Quentaro Velmani"},
                          "url_detail": {"URL": "zorbax-fabricators"}}, "source": "company/detail"},
        "H02": {"value": {"assignedto_name": "Draventi Koshal", "teleassignedto_name": "Draventi Koshal", "assignedto": 42},
                "source": "byrsupplyapi"},
        "E08": {"value": {"competitors": {"competitors": [
            {"glusr_usr_id": int(GLID), "competitor_company": "Plemora Steel Works", "competitor_glusr_id": 812345678,
             "catalog_url": "https://www.indiamart.com/plemora-steel-works/"},
            {"glusr_usr_id": int(GLID), "competitor_company": "Hexwin Tubes LLP", "competitor_glusr_id": 823456789}]}},
            "source": "nsdprepplus"},
        "E02": {"value": [{"buyer_company": "Brontal Buyers", "subject": "pipes"}], "source": "gc_enquiries"},
    }, "key_facts": [{"id": "K1", "fact": f"Seller {GLID} Zorbax Fabricators", "cite": "core.md#A02"}]}
    (folder / "context.json").write_text(json.dumps(ctx), encoding="utf-8")
    (folder / "INDEX.md").write_text(f"# Seller {GLID}: INDEX\n- Company ZORBAX FABRICATORS PVT LTD, owner Quentaro velmani\n"
                                     f"- Executive: Draventi Koshal\n- see https://www.indiamart.com/zorbax-fabricators/\n{extra_md}",
                                     encoding="utf-8")
    (folder / "peers.md").write_text("Competitors: Plemora Steel Works (812345678), Hexwin Tubes LLP; Hexwin Tubes is near\n",
                                     encoding="utf-8")
    (folder / "calls" / "C01_2026-08-10.md").write_text(f"# {GLID}: call C01\n  - C01.T1 bot: Namaste Quentaro ji, Zorbax se?\n"
                                                        "  - C01.T2 seller: haan, Brontal Buyers ka order hai\n", encoding="utf-8")
    return folder


def run(tmp_path, extra_md=""):
    make_context(tmp_path, extra_md)
    return E.export(GLID, str(tmp_path / "contexts"), str(tmp_path / "export"), str(tmp_path / "maps"), key=KEY)


def all_text(folder):
    t = ""
    for root, _, fs in os.walk(folder):
        for f in fs:
            t += f + open(os.path.join(root, f), encoding="utf-8").read()
    return t


def test_pseudo_is_hmac_16_hex():
    p = E.pseudo_id(GLID, KEY)
    assert len(p) == 16 and int(p, 16) >= 0 and p == E.pseudo_id(GLID, KEY) and p != E.pseudo_id(GLID, KEY + "x")


def test_export_replaces_names_and_glid(tmp_path):
    pseudo, out, hits = run(tmp_path)
    assert hits == {} and out and os.path.basename(out) == pseudo
    t = all_text(out)
    for bad in (GLID, "Quentaro", "Velmani", "Ishvani", "Zorbax", "zorbax", "Draventi", "Koshal", "Plemora", "Hexwin",
                "plemora-steel-works", "812345678", "Brontal"):
        assert bad.lower() not in t.lower(), bad
    for tok in ("{SELLER_NAME}", "{COMPANY}", "{EXEC_NAME}", "{COMPETITOR_1}", "{COMPETITOR_2}", "{BUYER_COMPANY}"):
        assert tok in t, tok
    ctx = json.load(open(os.path.join(out, "context.json"), encoding="utf-8"))
    assert ctx["glid"] == pseudo and ctx["points"]["A01"]["value"] == pseudo
    assert ctx["points"]["H02"]["value"]["assignedto"] == 42


def test_map_written_outside_export(tmp_path):
    pseudo, out, _ = run(tmp_path)
    m = tmp_path / "maps" / f"{pseudo}.json"
    assert m.exists() and not str(m).startswith(str(out))
    mp = json.loads(m.read_text(encoding="utf-8"))
    assert mp["glid"] == GLID and "Quentaro" in mp["tokens"]["{SELLER_NAME}"]
    assert not any(f.endswith(".json") and f != "context.json" for f in os.listdir(out))


def test_gate_fails_and_deletes_on_phone(tmp_path):
    pseudo, out, hits = run(tmp_path, extra_md="call me on 9876543210\n")
    assert out is None and "mobile" in hits
    assert not (tmp_path / "export" / pseudo).exists()
    assert not (tmp_path / "maps" / f"{pseudo}.json").exists()


def test_gate_catches_leftover_name(tmp_path):
    folder = tmp_path / "x"
    folder.mkdir()
    (folder / "a.md").write_text("hello Quentaro and 900000002", encoding="utf-8")
    hits = E.gate(str(folder), GLID, {"{SELLER_NAME}": ["Quentaro"]})
    assert "glid" in hits and "name {SELLER_NAME}" in hits


def test_cli_exits_nonzero_on_gate_failure(tmp_path, monkeypatch):
    make_context(tmp_path, extra_md="mail a@b.com\n")
    monkeypatch.setattr(E, "DST", str(tmp_path / "export"))
    monkeypatch.setattr(E, "MAPS", str(tmp_path / "maps"))
    monkeypatch.setattr(E, "load_key", lambda *a: KEY)
    monkeypatch.setattr("sys.argv", ["x", "--glid", GLID, "--src", str(tmp_path / "contexts")])
    try:
        E.main()
        assert False, "should exit"
    except SystemExit as e:
        assert e.code == 2


def test_load_key_generates_once(tmp_path, monkeypatch):
    monkeypatch.delenv(E.KEY_NAME, raising=False)
    env = tmp_path / ".env"
    env.write_text("OTHER=1", encoding="utf-8")
    k1 = E.load_key(str(env))
    k2 = E.load_key(str(env))
    assert k1 == k2 and len(k1) == 64
    assert env.read_text(encoding="utf-8").startswith("OTHER=1\n")


def test_export_strips_sources_and_all_md():
    import export_for_agent as X
    ctx = {"glid": "1", "sources": {"gc_x": 3}, "api_status": {"a": 200}, "cache_hash": "h", "cache_files_used": 2,
           "points": {"A01": {"value": 5, "source": "users_detail", "as_of_unsafe": True}}}
    out = X.strip_sources(ctx)
    assert not (set(out) & X.SOURCE_KEYS)
    assert out["points"]["A01"] == {"value": 5, "as_of_unsafe": True}
