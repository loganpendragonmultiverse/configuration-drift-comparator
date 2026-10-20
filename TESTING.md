# Testing

Install `python -m pip install -e ".[dev]"`, then run `ruff format --check .`,
`ruff check .`, `mypy src`, `pytest` and `python -m build`. Keep the existing
90% branch-coverage gate and six native CI combinations unchanged.

Regressions cover typed sources, non-finite JSON, duplicate keys, string/missing
identity, dotted-key collisions, recursive pointer boundaries and source/report
preservation under competing output creation. Install both built wheel and
source distribution in fresh environments and run the same suite from outside
the checkout. Exercise the shipped sample in JSON and Markdown through the CLI.
