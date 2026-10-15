import json

import pytest

from configuration_drift_comparator.cli import main
from configuration_drift_comparator.core import analyze, render_markdown


def report(a, b, **options):
    return analyze(
        {
            "recursive": True,
            "sources": [{"name": "a", "values": a}, {"name": "b", "values": b}],
            **options,
        }
    )


def test_escaped_pointers_and_stable_order():
    r = report({"a/b": {"~x": 1}, "": 3, "a.b": 4}, {"a/b": {"~x": 2}, "": 3})
    rows = {row["key"]: row for row in r["keys"]}
    assert list(rows) == ["/", "/a.b", "/a~1b/~0x"]
    assert rows["/a~1b/~0x"]["classification"] == "changed"
    assert rows["/a.b"]["missing_sources"] == ["b"]
    assert r["comparison"] == "json-pointer"
    assert "/a~1b/~0x" in render_markdown(r)


def test_absence_null_sentinel_and_atomic_arrays():
    r = report(
        {"null": None, "sentinel": "[missing]", "items": [1, {"x": 2}]}, {"items": [1, {"x": 3}]}
    )
    rows = {row["key"]: row for row in r["keys"]}
    assert set(rows) == {"/items", "/null", "/sentinel"}
    assert all(row["drift"] for row in rows.values())
    assert rows["/null"]["values"]["a"] is None
    assert rows["/sentinel"]["missing_sources"] == ["b"]


def test_object_boundaries_and_empty_objects():
    r = report(
        {"a": {"child": 1}, "empty": {}, "null": {}},
        {"a": 1, "empty": {}, "null": None},
        baseline="b",
    )
    rows = {row["key"]: row for row in r["keys"]}
    assert list(rows) == ["/a", "/empty", "/null"]
    assert rows["/a"]["values"]["a"] == {"child": 1}
    assert rows["/a"]["differing_from_baseline"] == ["a"]
    assert rows["/empty"]["classification"] == "consistent"
    assert rows["/null"]["classification"] == "changed"
    assert report({}, {})["keys"][0]["key"] == ""
    assert report({"object": {}}, {})["keys"][0]["missing_sources"] == ["b"]


def test_legacy_default_and_peer_mode():
    data = {
        "sources": [
            {"name": "a", "values": {"x": {"y": 1}}},
            {"name": "b", "values": {"x": {"y": 2}}},
        ]
    }
    assert analyze(data) == analyze({**data, "recursive": False})
    assert analyze(data)["keys"][0]["key"] == "x.y"
    r = analyze({**data, "recursive": True})
    assert r["baseline"] is None and r["keys"][0]["key"] == "/x/y"
    assert r["drift_count"] == 1


@pytest.mark.parametrize("option", [None, 1, "true", []])
def test_recursive_requires_boolean(option):
    with pytest.raises(TypeError, match="boolean"):
        report({}, {}, recursive=option)


def test_cli_and_invalid_values(tmp_path, capsys):
    path = tmp_path / "input.json"
    data = {
        "recursive": True,
        "sources": [{"name": "a", "values": {"x": None}}, {"name": "b", "values": {}}],
    }
    path.write_text(json.dumps(data), encoding="utf-8")
    before = path.read_bytes()
    assert main([str(path), "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["keys"][0]["key"] == "/x"
    assert path.read_bytes() == before
    with pytest.raises(ValueError, match="JSON objects"):
        report([], {})
