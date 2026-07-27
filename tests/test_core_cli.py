import json
from pathlib import Path

import pytest

from configuration_drift_comparator.cli import main
from configuration_drift_comparator.core import PROJECT, analyze, render_json, render_markdown


def test_representative_sample_has_expected_result():
    data = json.loads(
        (Path(__file__).parents[1] / "examples" / "sample.json").read_text(encoding="utf-8")
    )
    report = analyze(data)
    assert report["version"] == 1 and report["project"] == PROJECT
    assert report["drift_count"] == 2
    assert sum(report["classification_counts"].values()) == len(report["keys"])
    assert f'"project": "{PROJECT}"' in render_json(report)
    assert PROJECT.replace("-", " ").title() in render_markdown(report)


def test_missing_required_input_is_rejected():
    with pytest.raises(ValueError):
        analyze({})


def test_baseline_differences_and_missing_source_summary():
    report = analyze(
        {
            "baseline": "docs",
            "sources": [
                {"name": "docs", "values": {"port": 80, "secure": True}},
                {"name": "code", "values": {"port": 81}},
                {"name": "example", "values": {"port": 80, "secure": True}},
            ],
        }
    )
    port = next(item for item in report["keys"] if item["key"] == "port")
    assert port["differing_from_baseline"] == ["code"]
    assert report["missing_by_source"]["code"] == 1
    assert report["classification_counts"]["missing"] == 1
    with pytest.raises(ValueError, match="baseline"):
        analyze({"baseline": "live", "sources": [{"name": "docs", "values": {}}]})


def test_cli_json_and_output_safety(tmp_path, capsys):
    source = Path(__file__).parents[1] / "examples" / "sample.json"
    assert main([str(source), "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["project"] == PROJECT
    output = tmp_path / "report.md"
    output.write_text("keep", encoding="utf-8")
    assert main([str(source), "--output", str(output)]) == 2
