# Configuration Drift Comparator

[![CI](https://github.com/loganpendragonmultiverse/configuration-drift-comparator/actions/workflows/ci.yml/badge.svg)](https://github.com/loganpendragonmultiverse/configuration-drift-comparator/actions/workflows/ci.yml)

Compare configuration examples, code expectations, documentation, and manifests for drift. The command uses explicit UTF-8 JSON input and produces reviewable JSON or Markdown output.

## Three-minute start

```bash
python -m pip install .
config-drift examples/sample.json
config-drift examples/sample.json --format json --output report.json
```

The example documents the v1 input shape. Existing report files are never overwritten. Source inputs are read-only except where the documented purpose explicitly creates a new output artifact.

## Privacy and platforms

The tool runs locally and does not upload input or include telemetry. Python 3.10 or newer is supported on Windows, macOS, and Linux.

## Interpretation boundary

The comparator evaluates explicit values and missing keys; it does not contact deployed systems or decide which source is authoritative.

## Development

```bash
python -m pip install -e ".[dev]"
ruff format --check .
ruff check .
mypy src
pytest
python -m build
```

The project is feature-complete for its documented v1 scope. Maintenance focuses on correctness, security, compatibility, and well-supported input improvements.

Part of the [Logan Pendragon Forge open-source collection](https://www.loganpendragonforge.com/open-source/). Licensed under the [MIT License](LICENSE).
