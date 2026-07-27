from __future__ import annotations

import json
from typing import Any

PROJECT = "configuration-drift-comparator"


def _require(data: dict[str, Any], key: str) -> Any:
    value = data.get(key)
    if value is None or value == "" or value == []:
        raise ValueError(f"{key} is required")
    return value


def _config_drift(data: dict[str, Any]) -> dict[str, Any]:
    sources = _require(data, "sources")
    names = [str(item.get("name", "")) for item in sources]
    if any(not name for name in names) or len(names) != len(set(names)):
        raise ValueError("configuration sources need unique names")
    flattened: dict[str, dict[str, Any]] = {}
    for source in sources:
        values = source.get("values", {})
        stack = [("", values)]
        flat = {}
        while stack:
            prefix, value = stack.pop()
            if isinstance(value, dict):
                stack.extend(
                    ((f"{prefix}.{key}".strip("."), nested) for key, nested in value.items())
                )
            else:
                flat[prefix] = value
        flattened[source["name"]] = flat
    keys = sorted({key for values in flattened.values() for key in values})
    rows = []
    for key in keys:
        values = {name: flattened[name].get(key, "[missing]") for name in names}
        rows.append(
            {
                "key": key,
                "values": values,
                "drift": len({json.dumps(value, sort_keys=True) for value in values.values()}) > 1,
            }
        )
    return {"sources": names, "keys": rows, "drift_count": sum(item["drift"] for item in rows)}


def analyze(data: dict[str, Any]) -> dict[str, Any]:
    return {"version": 1, "project": PROJECT, **_config_drift(data)}


def render_json(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n"


def render_markdown(report: dict[str, Any]) -> str:
    lines = [f"# {report['project'].replace('-', ' ').title()} report", ""]
    for key, value in report.items():
        if key not in {"version", "project"}:
            lines.extend(
                [
                    f"## {key.replace('_', ' ').title()}",
                    "",
                    f"```json\n{json.dumps(value, indent=2, ensure_ascii=False, default=str)}\n```",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"
