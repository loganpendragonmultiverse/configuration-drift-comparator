import json
from pathlib import Path

import pytest

from configuration_drift_comparator.cli import main
from configuration_drift_comparator.core import analyze


@pytest.mark.parametrize(
    "data",
    [
        None,
        [],
        3,
        {"sources": "x"},
        {"sources": {}},
        {"sources": []},
        {"sources": [None]},
        {"sources": [{"name": 1}]},
        {"sources": [{"name": " "}]},
        {"sources": [{"name": "a", "values": []}]},
        {"sources": [{"name": "a"}], "baseline": True},
    ],
)
def test_malformed_inputs_are_validation_errors(data):
    with pytest.raises((ValueError, TypeError)):
        analyze(data)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), {1: "bad"}, {"nested": [object()]}])
def test_only_finite_json_values_and_string_keys(value):
    with pytest.raises(ValueError):
        analyze({"sources": [{"name": "a", "values": {"key": value}}]})


def test_legacy_missing_sentinel_is_still_drift():
    report = analyze(
        {"sources": [{"name": "a", "values": {"x": "[missing]"}}, {"name": "b", "values": {}}]}
    )
    assert report["keys"][0]["drift"] is True
    assert report["keys"][0]["missing_sources"] == ["b"]
    assert report["keys"][0]["differing_from_baseline"] == ["b"]


def test_ambiguous_dotted_keys_require_pointer_mode():
    data = {"sources": [{"name": "a", "values": {"x.y": 1, "x": {"y": 2}}}]}
    with pytest.raises(ValueError, match="ambiguous"):
        analyze(data)
    assert len(analyze({**data, "recursive": True})["keys"]) == 2


def test_duplicate_keys_and_output_alias_preserve_inputs(tmp_path, capsys):
    source = tmp_path / "input.json"
    source.write_text('{"sources": [], "sources": [{"name": "a"}]}')
    assert main([str(source)]) == 2
    assert "duplicate object key" in capsys.readouterr().err
    source.write_text(json.dumps({"sources": [{"name": "a", "values": {"x": 1}}]}))
    before = source.read_bytes()
    assert main([str(source), "--output", str(source)]) == 2
    assert source.read_bytes() == before


def test_output_creation_race_does_not_overwrite(tmp_path, monkeypatch):
    source = tmp_path / "input.json"
    source.write_text(json.dumps({"sources": [{"name": "a"}]}))
    output = tmp_path / "report.md"
    original = Path.open

    def race(path, mode="r", *args, **kwargs):
        if path == output and mode == "x":
            with original(path, "w", encoding="utf-8") as handle:
                handle.write("other writer")
        return original(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", race)
    assert main([str(source), "--output", str(output)]) == 2
    assert output.read_text() == "other writer"


def test_dangling_output_symlink_is_never_followed(tmp_path):
    source = tmp_path / "input.json"
    data = {"sources": [{"name": "a"}]}
    source.write_text(json.dumps(data))
    target = tmp_path / "absent-target"
    output = tmp_path / "report.md"
    try:
        output.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable")
    assert main([str(source), "--output", str(output)]) == 2
    assert output.is_symlink() and not target.exists()
