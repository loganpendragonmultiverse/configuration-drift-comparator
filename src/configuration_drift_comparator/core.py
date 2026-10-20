from __future__ import annotations

import json
from typing import Any

PROJECT = "configuration-drift-comparator"


def _sources(data: dict[str, Any]) -> list[dict[str, Any]]:
    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("sources must be a non-empty array")
    for source in sources:
        if not isinstance(source, dict):
            raise TypeError("each configuration source must be an object")
        name = source.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("configuration sources need non-empty string names")
        values = source.get("values", {})
        try:
            json.dumps(values, allow_nan=False)
        except (TypeError, ValueError, RecursionError) as exc:
            raise ValueError("source values must contain finite JSON values") from exc
        stack = [values]
        while stack:
            value = stack.pop()
            if isinstance(value, dict):
                if any(not isinstance(key, str) for key in value):
                    raise ValueError("configuration object keys must be strings")
                stack.extend(value.values())
            elif isinstance(value, list):
                stack.extend(value)
    return sources


def _config_drift(data: dict[str, Any]) -> dict[str, Any]:
    sources = _sources(data)
    names = [item["name"] for item in sources]
    if any(not name for name in names) or len(names) != len(set(names)):
        raise ValueError("configuration sources need unique names")
    baseline_raw: Any = data.get("baseline")
    if baseline_raw is not None and not isinstance(baseline_raw, str):
        raise ValueError("baseline must be a source name string")
    baseline = baseline_raw
    if baseline is not None and baseline not in names:
        raise ValueError("baseline must name one of the configuration sources")
    recursive = data.get("recursive", False)
    if not isinstance(recursive, bool):
        raise TypeError("recursive must be a boolean")
    flattened: dict[str, dict[str, Any]] = {}
    for source in [] if recursive else sources:
        values = source.get("values", {})
        if not isinstance(values, dict):
            raise TypeError("source values must be JSON objects")
        stack = [("", values)]
        flat: dict[str, Any] = {}
        while stack:
            prefix, value = stack.pop()
            if isinstance(value, dict):
                stack.extend(
                    ((f"{prefix}.{key}".strip("."), nested) for key, nested in value.items())
                )
            else:
                if prefix in flat:
                    raise ValueError("ambiguous dotted keys; use recursive=true")
                flat[prefix] = value
        flattened[source["name"]] = flat
    if recursive:
        flattened = _pointer_values(sources)
    keys = sorted({key for values in flattened.values() for key in values})
    rows: list[dict[str, Any]] = []
    for key in keys:
        values = {name: flattened[name].get(key, "[missing]") for name in names}
        encoded = {
            name: json.dumps([key in flattened[name], value], sort_keys=True)
            for name, value in values.items()
        }
        missing_sources = [name for name in names if key not in flattened[name]]
        reference = str(baseline) if baseline is not None else names[0]
        differing_sources = [name for name in names if encoded[name] != encoded[reference]]
        drift = len(set(encoded.values())) > 1
        rows.append(
            {
                "key": key,
                "values": values,
                "drift": drift,
                "classification": "missing"
                if missing_sources
                else "changed"
                if drift
                else "consistent",
                "missing_sources": missing_sources,
                "differing_from_baseline": differing_sources,
            }
        )
    return {
        **({"comparison": "json-pointer"} if recursive else {}),
        "sources": names,
        "baseline": baseline,
        "keys": rows,
        "drift_count": sum(item["drift"] for item in rows),
        "missing_by_source": {
            name: sum(name in item["missing_sources"] for item in rows) for name in names
        },
        "classification_counts": {
            state: sum(item["classification"] == state for item in rows)
            for state in ("consistent", "changed", "missing")
        },
    }


def analyze(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise TypeError("input must be a JSON object")
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


def _pointer_values(sources: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Descend shared objects; compare arrays and object/scalar boundaries atomically."""
    result: dict[str, dict[str, Any]] = {source["name"]: {} for source in sources}
    if not all(isinstance(source.get("values", {}), dict) for source in sources):
        raise ValueError("recursive source values must be JSON objects")

    def visit(pointer: str, present: dict[str, Any]) -> None:
        if len(present) == len(sources) and all(isinstance(v, dict) for v in present.values()):
            keys = sorted({key for value in present.values() for key in value})
            if keys:
                for key in keys:
                    escaped = key.replace("~", "~0").replace("/", "~1")
                    visit(
                        pointer + "/" + escaped,
                        {name: value[key] for name, value in present.items() if key in value},
                    )
                return
        for name, value in present.items():
            result[name][pointer] = value

    visit("", {source["name"]: source.get("values", {}) for source in sources})
    return result
